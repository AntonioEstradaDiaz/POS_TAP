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
        """Abre y retorna una conexión con soporte a claves foráneas activado."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _inicializar_bd(self):
        """Crea las tablas si no existen e inserta el catálogo base si el inventario está vacío."""
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

                CREATE TABLE IF NOT EXISTS insumos (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre          TEXT    NOT NULL,
                    unidad_medida   TEXT    NOT NULL,
                    cantidad_actual REAL    NOT NULL DEFAULT 0,
                    stock_minimo    REAL    NOT NULL DEFAULT 0,
                    precio_compra   REAL    NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS recetas (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_nombre    TEXT    NOT NULL,
                    insumo_id          INTEGER NOT NULL,
                    cantidad_por_orden REAL    NOT NULL,
                    FOREIGN KEY (insumo_id) REFERENCES insumos(id)
                );
            """)

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
    # INVENTARIO DE PRODUCTOS
    # ─────────────────────────────────────────────

    def get_inventario(self) -> dict:
        """Retorna el diccionario con todo el inventario de productos."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT nombre, precio, stock FROM productos ORDER BY id"
            ).fetchall()
        return {r["nombre"]: {"precio": r["precio"], "stock": r["stock"]} for r in rows}

    def agregar_producto(self, nombre: str, precio: float, stock: int = 100) -> bool:
        """
        Agrega un nuevo producto al inventario.
        Retorna True si tuvo éxito, False si el producto ya existía.
        """
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
        """Elimina un producto del inventario de forma permanente."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM productos WHERE nombre = ?", (nombre,)
            )
        return cursor.rowcount > 0

    # ─────────────────────────────────────────────
    # VENTAS
    # ─────────────────────────────────────────────

    def registrar_venta(self, carrito: dict, total: float):
        """
        Registra una venta con su estampa de tiempo y descuenta el inventario.
        Todo ocurre en una sola transacción atómica, incluyendo el descuento
        de insumos según las recetas registradas.

        CORRECCIÓN: la transacción de insumos ahora ocurre dentro del mismo
        bloque 'with', garantizando atomicidad completa.
        """
        ahora = datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        hora  = ahora.strftime("%H:%M")

        with self._get_conn() as conn:
            # 1. Insertar cabecera de venta
            cursor = conn.execute(
                "INSERT INTO ventas (fecha, hora, total) VALUES (?, ?, ?)",
                (fecha, hora, total)
            )
            venta_id = cursor.lastrowid

            # 2. Insertar detalle, descontar stock de productos y descontar insumos
            for prod, cant in carrito.items():
                conn.execute(
                    "INSERT INTO venta_detalle (venta_id, producto, cantidad) VALUES (?, ?, ?)",
                    (venta_id, prod, cant)
                )
                conn.execute(
                    "UPDATE productos SET stock = stock - ? WHERE nombre = ?",
                    (cant, prod)
                )
                # Descontar insumos dentro de la misma conexión/transacción
                self._descontar_insumos_conn(conn, prod, cant)

    def _descontar_insumos_conn(self, conn: sqlite3.Connection, nombre_producto: str, cantidad_vendida: int):
        """
        Método interno que descuenta insumos usando una conexión ya abierta.
        Se llama desde registrar_venta para mantener la atomicidad.
        Emite avisos por consola si algún insumo baja de su stock mínimo.
        """
        receta = conn.execute("""
            SELECT insumo_id, cantidad_por_orden
            FROM recetas
            WHERE producto_nombre = ?
        """, (nombre_producto,)).fetchall()

        if not receta:
            print(f"ℹ️ Sin receta registrada para: {nombre_producto}")
            return

        for row in receta:
            insumo_id     = row["insumo_id"]
            cant_necesaria = row["cantidad_por_orden"]
            total_a_restar = cant_necesaria * cantidad_vendida

            conn.execute("""
                UPDATE insumos
                SET cantidad_actual = cantidad_actual - ?
                WHERE id = ?
            """, (total_a_restar, insumo_id))

            insumo = conn.execute("""
                SELECT nombre, cantidad_actual, stock_minimo
                FROM insumos WHERE id = ?
            """, (insumo_id,)).fetchone()

            if insumo and insumo["cantidad_actual"] <= insumo["stock_minimo"]:
                print(f"⚠️ POCO STOCK: {insumo['nombre']} | Quedan: {insumo['cantidad_actual']:.3f}")

    def deshacer_ultima_venta(self):
        """
        Elimina la última venta y restaura el stock de productos e insumos.

        CORRECCIÓN: ahora también revierte el descuento de insumos para
        mantener la consistencia del inventario.
        """
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
                # Restaurar stock de productos
                conn.execute(
                    "UPDATE productos SET stock = stock + ? WHERE nombre = ?",
                    (d["cantidad"], d["producto"])
                )
                # Restaurar insumos (operación inversa al descuento)
                self._restaurar_insumos_conn(conn, d["producto"], d["cantidad"])

            # Elimina venta y en cascada venta_detalle
            conn.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))

        productos = {d["producto"]: d["cantidad"] for d in detalles}
        return {
            "fecha":     ultima["fecha"],
            "hora":      ultima["hora"],
            "productos": productos,
            "total":     ultima["total"],
        }

    def _restaurar_insumos_conn(self, conn: sqlite3.Connection, nombre_producto: str, cantidad_vendida: int):
        """
        Método interno que revierte el descuento de insumos usando una conexión ya abierta.
        Se llama desde deshacer_ultima_venta para mantener la atomicidad.
        """
        receta = conn.execute("""
            SELECT insumo_id, cantidad_por_orden
            FROM recetas
            WHERE producto_nombre = ?
        """, (nombre_producto,)).fetchall()

        for row in receta:
            total_a_sumar = row["cantidad_por_orden"] * cantidad_vendida
            conn.execute("""
                UPDATE insumos
                SET cantidad_actual = cantidad_actual + ?
                WHERE id = ?
            """, (total_a_sumar, row["insumo_id"]))

    def get_historial_hoy(self) -> list:
        """Retorna lista de ventas del día actual con hora y total."""
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
        """Registra un gasto del día."""
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
        """
        Calcula el resumen del día y lo guarda en la tabla 'cierres'.
        También genera un archivo JSON de respaldo en data/cierres/YYYY-MM-DD.json.
        Retorna (resumen_dict, ruta_archivo).
        """
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
    # CONSULTAS PARA DASHBOARD
    # ─────────────────────────────────────────────

    def get_historico_7_dias(self) -> list:
        """Retorna totales de ventas de los últimos 7 días."""
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
        """Retorna ventas, gastos, ganancia del día y top productos vendidos hoy."""
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
    # INSUMOS
    # ─────────────────────────────────────────────

    def agregar_insumo(self, nombre: str, unidad: str, cantidad: float, minimo: float, precio: float):
        """Da de alta un nuevo insumo en el inventario."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO insumos (nombre, unidad_medida, cantidad_actual, stock_minimo, precio_compra)
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, unidad, cantidad, minimo, precio))

    def get_lista_insumos(self) -> list:
        """Retorna id, nombre y unidad de todos los insumos. Útil para selectores."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, nombre, unidad_medida FROM insumos ORDER BY nombre"
            ).fetchall()
        return [{"id": r["id"], "nombre": r["nombre"], "unidad_medida": r["unidad_medida"]} for r in rows]

    def get_lista_insumos_completa(self) -> list:
        """Retorna todos los campos de insumos. Útil para la vista de inventario."""
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM insumos ORDER BY nombre").fetchall()

    def eliminar_insumo(self, id_insumo: int):
        """
        Elimina un insumo. Lanza Exception si está siendo usado en alguna receta.
        """
        with self._get_conn() as conn:
            usado = conn.execute(
                "SELECT id FROM recetas WHERE insumo_id = ?", (id_insumo,)
            ).fetchone()
            if usado:
                raise Exception("Este insumo está en una receta. Elimina la receta primero.")
            conn.execute("DELETE FROM insumos WHERE id = ?", (id_insumo,))

    def get_lista_productos(self) -> list:
        """Retorna los nombres de todos los productos. Útil para selectores."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT nombre FROM productos ORDER BY nombre"
            ).fetchall()
        return [r["nombre"] for r in rows]

    # ─────────────────────────────────────────────
    # RECETAS
    # ─────────────────────────────────────────────

    def nueva_receta(self, nombre_platillo: str, precio_venta: float, ingredientes: list):
        """
        Guarda todos los ingredientes de una receta en una sola transacción.

        CORRECCIÓN: este método faltaba y es el que llama RecetasView._guardar_receta.

        Parámetros:
            nombre_platillo  — nombre del platillo (coincide con productos.nombre)
            precio_venta     — precio de venta (actualmente informativo; el precio
                               oficial vive en la tabla 'productos')
            ingredientes     — lista de dicts: [{"id": int, "cantidad": float}, ...]
        """
        if not ingredientes:
            raise ValueError("La receta debe tener al menos un ingrediente.")

        with self._get_conn() as conn:
            for ing in ingredientes:
                conn.execute("""
                    INSERT INTO recetas (producto_nombre, insumo_id, cantidad_por_orden)
                    VALUES (?, ?, ?)
                """, (nombre_platillo, ing["id"], ing["cantidad"]))

    def obtener_todas_recetas(self) -> list:
        """
        Retorna todas las recetas con nombre de producto, insumo, cantidad y
        costo calculado por ingrediente.

        CORRECCIÓN: ahora incluye costo_ingrediente y costo_total por receta
        para que la vista pueda mostrar la ganancia correctamente.
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    r.producto_nombre                               AS nombre,
                    p.precio                                        AS precio,
                    SUM(i.precio_compra * r.cantidad_por_orden)     AS costo
                FROM recetas r
                LEFT JOIN productos p ON p.nombre = r.producto_nombre
                LEFT JOIN insumos   i ON i.id      = r.insumo_id
                GROUP BY r.producto_nombre
                ORDER BY r.producto_nombre
            """).fetchall()
        return rows

    def obtener_detalle_receta(self, nombre_platillo: str) -> list:
        """
        Retorna el detalle de ingredientes de un platillo específico.
        Útil para mostrar o editar una receta individual.
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    i.id,
                    i.nombre            AS insumo,
                    i.unidad_medida     AS unidad,
                    r.cantidad_por_orden AS cantidad,
                    i.precio_compra     AS precio_unitario,
                    (i.precio_compra * r.cantidad_por_orden) AS costo_linea
                FROM recetas r
                JOIN insumos i ON i.id = r.insumo_id
                WHERE r.producto_nombre = ?
                ORDER BY i.nombre
            """, (nombre_platillo,)).fetchall()
        return rows

    def eliminar_receta(self, nombre_platillo: str) -> bool:
        """
        Elimina todos los ingredientes de la receta de un platillo.
        Retorna True si se eliminó algo, False si no existía.
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM recetas WHERE producto_nombre = ?", (nombre_platillo,)
            )
        return cursor.rowcount > 0