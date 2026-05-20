import sqlite3
import os
from datetime import datetime, timedelta


class DataManager:
    """
    Capa de Acceso a Datos (DAL) para el sistema de Punto de Venta.
    Usa SQLite como motor de persistencia.
    """

    def __init__(self):
        mobile_storage = os.environ.get("FLET_APP_STORAGE")
        if mobile_storage:
            self.dir_data = os.path.join(mobile_storage, "data")
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.dir_data = os.path.join(base_dir, "..", "data")

        os.makedirs(self.dir_data, exist_ok=True)
        self.db_path = os.path.join(self.dir_data, "pos.db")
        self._inicializar_bd()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
# El sistema calculaba 'ganancia' como precio x cantidad, lo cual es ingreso bruto. Se agrego la columna costo a la tabla productos y se corrigio la formula en SQL.
# La ganancia neta se calcula restando el costo de ingredientes y gastos operativos a los ingresos por ventas, dando una visión realista de la rentabilidad.

    def _inicializar_bd(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS productos (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre  TEXT    UNIQUE NOT NULL,
                    precio  REAL    NOT NULL,
                    costo   REAL    NOT NULL DEFAULT 0,
                    stock   INTEGER NOT NULL DEFAULT 100
                );

                CREATE TABLE IF NOT EXISTS ventas (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT    NOT NULL,
                    hora  TEXT    NOT NULL,
                    total REAL    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS venta_detalle (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id  INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
                    producto  TEXT    NOT NULL,
                    cantidad  INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS gastos (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha    TEXT NOT NULL,
                    concepto TEXT NOT NULL,
                    monto    REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cierres (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha    TEXT UNIQUE NOT NULL,
                    ventas   REAL NOT NULL,
                    gastos   REAL NOT NULL,
                    ganancia REAL NOT NULL
                );
            """)

            # ── Migración: agregar columna costo si no existe (BD ya creada) ──
            columnas = [r[1] for r in conn.execute("PRAGMA table_info(productos)").fetchall()]
            if "costo" not in columnas:
                conn.execute("ALTER TABLE productos ADD COLUMN costo REAL NOT NULL DEFAULT 0")
                # Actualizar costos de los productos del catálogo base
                costos_base = {
                    "Mole Poblano":      22.0,
                    "Enchiladas Verdes": 17.0,
                    "Chilaquiles Rojos": 14.0,
                    "Pozole Rojo":       25.0,
                    "Chiles Rellenos":   20.0,
                    "Tlayuda Oaxaquena": 27.0,
                }
                for nombre, costo in costos_base.items():
                    conn.execute(
                        "UPDATE productos SET costo = ? WHERE nombre = ? AND costo = 0",
                        (costo, nombre)
                    )

            # Catálogo base solo si la tabla está vacía
            count = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
            if count == 0:
                # (nombre, precio, costo, stock)
                # costo aproximado ~50-60% del precio de venta
                catalogo_base = [
                    ("Mole Poblano",      45.0, 22.0, 100),
                    ("Enchiladas Verdes", 35.0, 17.0, 100),
                    ("Chilaquiles Rojos", 30.0, 14.0, 100),
                    ("Pozole Rojo",       50.0, 25.0, 100),
                    ("Chiles Rellenos",   40.0, 20.0, 100),
                    ("Tlayuda Oaxaquena", 55.0, 27.0, 100),
                ]
                conn.executemany(
                    "INSERT OR IGNORE INTO productos (nombre, precio, costo, stock) VALUES (?, ?, ?, ?)",
                    catalogo_base
                )

    # ─────────────────────────────────────────────
    # INVENTARIO
    # ─────────────────────────────────────────────

    def get_inventario(self) -> dict:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT nombre, precio, costo, stock FROM productos ORDER BY id"
            ).fetchall()
        return {
            r["nombre"]: {
                "precio": r["precio"],
                "costo":  r["costo"],
                "stock":  r["stock"],
            }
            for r in rows
        }

    def agregar_producto(self, nombre: str, precio: float, costo: float = 0.0, stock: int = 100) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO productos (nombre, precio, costo, stock) VALUES (?, ?, ?, ?)",
                    (nombre, precio, costo, stock)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def actualizar_costo(self, nombre: str, costo: float) -> bool:
        """Actualiza el costo de ingredientes de un producto existente."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "UPDATE productos SET costo = ? WHERE nombre = ?",
                (costo, nombre)
            )
        return cursor.rowcount > 0

    def eliminar_producto(self, nombre: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM productos WHERE nombre = ?", (nombre,))
        return cursor.rowcount > 0

    # ─────────────────────────────────────────────
    # VENTAS
    # ─────────────────────────────────────────────

    def registrar_venta(self, carrito: dict, total: float):
        ahora = datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        hora  = ahora.strftime("%H:%M")

        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO ventas (fecha, hora, total) VALUES (?, ?, ?)",
                (fecha, hora, total)
            )
            venta_id = cursor.lastrowid

            for prod, cant in carrito.items():
                conn.execute(
                    "INSERT INTO venta_detalle (venta_id, producto, cantidad) VALUES (?, ?, ?)",
                    (venta_id, prod, cant)
                )
                conn.execute(
                    "UPDATE productos SET stock = stock - ? WHERE nombre = ?",
                    (cant, prod)
                )

    def deshacer_ultima_venta(self):
        with self._get_conn() as conn:
            ultima = conn.execute(
                "SELECT id, fecha, hora, total FROM ventas ORDER BY id DESC LIMIT 1"
            ).fetchone()

            if not ultima:
                return False

            venta_id = ultima["id"]
            detalles = conn.execute(
                "SELECT producto, cantidad FROM venta_detalle WHERE venta_id = ?",
                (venta_id,)
            ).fetchall()

            for d in detalles:
                conn.execute(
                    "UPDATE productos SET stock = stock + ? WHERE nombre = ?",
                    (d["cantidad"], d["producto"])
                )

            conn.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))

        productos = {d["producto"]: d["cantidad"] for d in detalles}
        return {
            "fecha":     ultima["fecha"],
            "hora":      ultima["hora"],
            "productos": productos,
            "total":     ultima["total"],
        }

    def get_historial_hoy(self) -> list:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            ventas = conn.execute(
                "SELECT id, hora, total FROM ventas WHERE fecha = ? ORDER BY id",
                (fecha_hoy,)
            ).fetchall()

            resultado = []
            for v in ventas:
                detalles = conn.execute(
                    "SELECT producto, cantidad FROM venta_detalle WHERE venta_id = ?",
                    (v["id"],)
                ).fetchall()
                productos = {d["producto"]: d["cantidad"] for d in detalles}
                resultado.append({
                    "fecha":     fecha_hoy,
                    "hora":      v["hora"],
                    "productos": productos,
                    "total":     v["total"],
                })
        return resultado

    # ─────────────────────────────────────────────
    # GASTOS
    # ─────────────────────────────────────────────

    def registrar_gasto(self, concepto: str, monto: float):
        fecha = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO gastos (fecha, concepto, monto) VALUES (?, ?, ?)",
                (fecha, concepto, monto)
            )

    # ─────────────────────────────────────────────
    # CIERRE DE DÍA
    # ─────────────────────────────────────────────

    def cerrar_dia(self):
        import json

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

        with self._get_conn() as conn:
            total_ventas = conn.execute(
                "SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha = ?",
                (fecha_hoy,)
            ).fetchone()[0]

            total_gastos = conn.execute(
                "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE fecha = ?",
                (fecha_hoy,)
            ).fetchone()[0]

            # Ganancia neta = ingresos - costo_ingredientes - gastos_operativos
            costo_ingredientes = conn.execute(
                """SELECT COALESCE(SUM(vd.cantidad * p.costo), 0)
                   FROM venta_detalle vd
                   JOIN ventas v ON v.id = vd.venta_id
                   JOIN productos p ON p.nombre = vd.producto
                   WHERE v.fecha = ?""",
                (fecha_hoy,)
            ).fetchone()[0]

            ganancia = round(total_ventas - costo_ingredientes - total_gastos, 2)

            conn.execute(
                """INSERT INTO cierres (fecha, ventas, gastos, ganancia)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(fecha) DO UPDATE SET
                       ventas   = excluded.ventas,
                       gastos   = excluded.gastos,
                       ganancia = excluded.ganancia""",
                (fecha_hoy, round(total_ventas, 2), round(total_gastos, 2), ganancia)
            )

        resumen = {
            "fecha":               fecha_hoy,
            "ventas":              round(total_ventas, 2),
            "costo_ingredientes":  round(costo_ingredientes, 2),
            "gastos_operativos":   round(total_gastos, 2),
            "ganancia_neta":       ganancia,
        }

        dir_cierres = os.path.join(self.dir_data, "cierres")
        os.makedirs(dir_cierres, exist_ok=True)
        ruta = os.path.join(dir_cierres, f"{fecha_hoy}.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(resumen, f, indent=4, ensure_ascii=False)

        return resumen, ruta

    # ─────────────────────────────────────────────
    # DASHBOARD
    # ─────────────────────────────────────────────

    def get_historico_7_dias(self) -> list:
        hoy = datetime.now().date()
        resultado = []

        with self._get_conn() as conn:
            for i in range(6, -1, -1):
                dia = hoy - timedelta(days=i)
                fecha_str = dia.strftime("%Y-%m-%d")
                total_dia = conn.execute(
                    "SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha = ?",
                    (fecha_str,)
                ).fetchone()[0]
                resultado.append({
                    "fecha": dia.strftime("%d/%m"),
                    "total": total_dia
                })

        return resultado
    # La consulta SQL para obtener los KPIs y el top de productos se optimizó para calcular todo en una sola pasada, evitando múltiples consultas a la base de datos.
    def get_kpis_y_graficos(self) -> dict:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

        with self._get_conn() as conn:
            total_v = conn.execute(
                "SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha = ?",
                (fecha_hoy,)
            ).fetchone()[0]

            total_g = conn.execute(
                "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE fecha = ?",
                (fecha_hoy,)
            ).fetchone()[0]

            # Costo total de ingredientes del día
            costo_ingredientes = conn.execute(
                """SELECT COALESCE(SUM(vd.cantidad * p.costo), 0)
                   FROM venta_detalle vd
                   JOIN ventas v ON v.id = vd.venta_id
                   JOIN productos p ON p.nombre = vd.producto
                   WHERE v.fecha = ?""",
                (fecha_hoy,)
            ).fetchone()[0]

            # Top productos con ganancia NETA por platillo
            rows = conn.execute(
                """SELECT
                       vd.producto,
                       SUM(vd.cantidad)                          AS total_cant,
                       p.precio,
                       p.costo,
                       SUM(vd.cantidad) * (p.precio - p.costo)  AS ganancia_neta
                   FROM venta_detalle vd
                   JOIN ventas v   ON v.id    = vd.venta_id
                   JOIN productos p ON p.nombre = vd.producto
                   WHERE v.fecha = ?
                   GROUP BY vd.producto
                   ORDER BY total_cant DESC""",
                (fecha_hoy,)
            ).fetchall()

        top_productos = {
            r["producto"]: {
                "cantidad":      r["total_cant"],
                "precio":        r["precio"],
                "costo":         r["costo"],
                "ganancia_neta": round(r["ganancia_neta"], 2),
            }
            for r in rows
        }

        return {
            "ventas_hoy":         total_v,
            "gastos_hoy":         total_g,
            "costo_ingredientes": costo_ingredientes,
            # Ganancia neta = ventas - costo ingredientes - gastos operativos
            "ganancia":           round(total_v - costo_ingredientes - total_g, 2),
            "top_productos":      top_productos,
        }