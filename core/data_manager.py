import sqlite3
import os
from datetime import datetime, timedelta

class DataManager:
    """
    Capa de Acceso a Datos (DAL) para el sistema de Punto de Venta.
    Usa SQLite como motor de persistencia.
    """

    # ─────────────────────────────────────────────
    # INICIALIZACIÓN
    # ─────────────────────────────────────────────

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
        """Abre y retorna una conexión con soporte a claves foráneas y modo WAL activado."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row        # Permite acceder columnas por nombre
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode=WAL") # 🔥 ESTA LÍNEA HACE QUE LA WEB VEA LOS CAMBIOS AL INSTANTE
        return conn

    def _inicializar_bd(self):
        """Crea todas las tablas del sistema (POS + Reseñas) si no existen."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS productos (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre  TEXT    UNIQUE NOT NULL,
                    precio  REAL    NOT NULL,
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

                CREATE TABLE IF NOT EXISTS resenas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto TEXT NOT NULL,
                    calificacion INTEGER NOT NULL,
                    comentario TEXT,
                    fecha TEXT NOT NULL
                );
            """)

            # Insertar catálogo base solo si la tabla está vacía
            count = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
            if count == 0:
                catalogo_base = [
                    ("Mole Poblano",      45.0, 100),
                    ("Enchiladas Verdes", 35.0, 100),
                    ("Chilaquiles Rojos", 30.0, 100),
                    ("Pozole Rojo",       50.0, 100),
                    ("Chiles Rellenos",   40.0, 100),
                    ("Tlayuda Oaxaquena", 55.0, 100),
                ]
                conn.executemany(
                    "INSERT OR IGNORE INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                    catalogo_base
                )

    # ─────────────────────────────────────────────
    # MÉTODOS DE INVENTARIO / PRODUCTOS
    # ─────────────────────────────────────────────

    def get_inventario(self) -> dict:
        """Retorna el diccionario con todo el inventario de productos."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT nombre, precio, stock FROM productos ORDER BY id"
            ).fetchall()
        return {r["nombre"]: {"precio": r["precio"], "stock": r["stock"]} for r in rows}

    def get_productos(self) -> list:
        """Retorna los productos formateados como lista de diccionarios para la web."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT nombre, precio FROM productos ORDER BY nombre").fetchall()
        return [{"nombre": r["nombre"], "precio": r["precio"]} for r in rows]

    def agregar_producto(self, nombre: str, precio: float, stock: int = 100) -> bool:
        """Agrega un nuevo producto al inventario."""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                    (nombre, precio, stock)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_producto(self, nombre: str) -> bool:
        """Elimina un producto por su nombre."""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM productos WHERE nombre = ?", (nombre,))
        return cursor.rowcount > 0

    # ─────────────────────────────────────────────
    # MÉTODOS DE VENTAS
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
    # MÉTODOS DE GASTOS
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

            ganancia = round(total_ventas - total_gastos, 2)

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
            "fecha":    fecha_hoy,
            "ventas":   round(total_ventas, 2),
            "gastos":   round(total_gastos, 2),
            "ganancia": ganancia,
        }

        dir_cierres = os.path.join(self.dir_data, "cierres")
        os.makedirs(dir_cierres, exist_ok=True)
        ruta = os.path.join(dir_cierres, f"{fecha_hoy}.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(resumen, f, indent=4, ensure_ascii=False)

        return resumen, ruta

    # ─────────────────────────────────────────────
    # CONSULTAS REQUERIDAS POR EL DASHBOARD
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

            rows = conn.execute(
                """SELECT vd.producto, SUM(vd.cantidad) AS total_cant
                   FROM venta_detalle vd
                   JOIN ventas v ON v.id = vd.venta_id
                   WHERE v.fecha = ?
                   GROUP BY vd.producto
                   ORDER BY total_cant DESC""",
                (fecha_hoy,)
            ).fetchall()

        top_productos = {r["producto"]: r["total_cant"] for r in rows}

        return {
            "ventas_hoy":    total_v,
            "gastos_hoy":    total_g,
            "ganancia":      total_v - total_g,
            "top_productos": top_productos,
        }

    # ─────────────────────────────────────────────
    # MÉTODOS EXCLUSIVOS DE LA WEB DE RESEÑAS
    # ─────────────────────────────────────────────

    def registrar_resena(self, producto: str, calificacion: int, comentario: str):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO resenas (producto, calificacion, comentario, fecha) VALUES (?, ?, ?, ?)",
                (producto, calificacion, comentario, fecha)
            )

    def get_resenas_producto(self, producto: str) -> list:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT calificacion, comentario, fecha FROM resenas WHERE producto = ? ORDER BY id DESC",
                (producto,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_promedio_calificacion(self, producto: str) -> float:
        with self._get_conn() as conn:
            res = conn.execute(
                "SELECT AVG(calificacion) FROM resenas WHERE producto = ?", (producto,)
            ).fetchone()[0]
        return round(res, 1) if res else 0.0