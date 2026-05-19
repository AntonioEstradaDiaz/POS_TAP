import sqlite3
import os
from datetime import datetime


class Database:
    """
    Capa SQLite para POS_TAP.
    Guarda ventas, gastos e inventario en paralelo al DataManager JSON.
    No reemplaza nada — solo agrega persistencia en base de datos.
    """

    def __init__(self, dir_data: str):
        self.db_path = os.path.join(dir_data, "pos_tap.db")
        self._conectar()
        self._crear_tablas()

    def _conectar(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _crear_tablas(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS inventario (
                nombre      TEXT PRIMARY KEY,
                precio      REAL NOT NULL,
                stock       INTEGER NOT NULL DEFAULT 100,
                categoria   TEXT NOT NULL DEFAULT 'comida'
            );

            CREATE TABLE IF NOT EXISTS ventas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT NOT NULL,
                hora        TEXT NOT NULL,
                total       REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS venta_productos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id    INTEGER NOT NULL,
                producto    TEXT NOT NULL,
                cantidad    INTEGER NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id)
            );

            CREATE TABLE IF NOT EXISTS gastos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT NOT NULL,
                concepto    TEXT NOT NULL,
                monto       REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cierres (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT UNIQUE NOT NULL,
                ventas      REAL NOT NULL,
                gastos      REAL NOT NULL,
                ganancia    REAL NOT NULL
            );
        """)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Inventario
    # ------------------------------------------------------------------
    def sincronizar_inventario(self, inventario: dict):
        for nombre, datos in inventario.items():
            self.cursor.execute("""
                INSERT OR IGNORE INTO inventario (nombre, precio, stock, categoria)
                VALUES (?, ?, ?, ?)
            """, (nombre, datos["precio"], datos["stock"], datos.get("categoria", "comida")))
        self.conn.commit()

    def agregar_producto(self, nombre: str, precio: float, stock: int = 100, categoria: str = "comida"):
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO inventario (nombre, precio, stock, categoria)
                VALUES (?, ?, ?, ?)
            """, (nombre, precio, stock, categoria))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error agregar_producto: {e}")

    def eliminar_producto(self, nombre: str):
        try:
            self.cursor.execute("DELETE FROM inventario WHERE nombre = ?", (nombre,))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error eliminar_producto: {e}")

    def actualizar_stock(self, nombre: str, cantidad: int):
        try:
            self.cursor.execute("""
                UPDATE inventario SET stock = stock - ? WHERE nombre = ?
            """, (cantidad, nombre))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error actualizar_stock: {e}")

    def restaurar_stock(self, nombre: str, cantidad: int):
        try:
            self.cursor.execute("""
                UPDATE inventario SET stock = stock + ? WHERE nombre = ?
            """, (cantidad, nombre))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error restaurar_stock: {e}")

    def get_inventario(self) -> dict:
        self.cursor.execute("SELECT * FROM inventario")
        filas = self.cursor.fetchall()
        return {
            f["nombre"]: {
                "precio":    f["precio"],
                "stock":     f["stock"],
                "categoria": f["categoria"]
            }
            for f in filas
        }

    # ------------------------------------------------------------------
    # Ventas
    # ------------------------------------------------------------------
    def registrar_venta(self, carrito: dict, total: float):
        try:
            ahora = datetime.now()
            self.cursor.execute("""
                INSERT INTO ventas (fecha, hora, total)
                VALUES (?, ?, ?)
            """, (ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M"), total))
            venta_id = self.cursor.lastrowid

            for producto, cantidad in carrito.items():
                self.cursor.execute("""
                    INSERT INTO venta_productos (venta_id, producto, cantidad)
                    VALUES (?, ?, ?)
                """, (venta_id, producto, cantidad))
                self.actualizar_stock(producto, cantidad)

            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error registrar_venta: {e}")

    def deshacer_ultima_venta(self):
        try:
            self.cursor.execute("SELECT * FROM ventas ORDER BY id DESC LIMIT 1")
            ultima = self.cursor.fetchone()
            if not ultima:
                return False

            self.cursor.execute("""
                SELECT producto, cantidad FROM venta_productos WHERE venta_id = ?
            """, (ultima["id"],))
            productos = self.cursor.fetchall()

            for p in productos:
                self.restaurar_stock(p["producto"], p["cantidad"])

            self.cursor.execute("DELETE FROM venta_productos WHERE venta_id = ?", (ultima["id"],))
            self.cursor.execute("DELETE FROM ventas WHERE id = ?", (ultima["id"],))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB] Error deshacer_ultima_venta: {e}")
            return False

    def get_historial_hoy(self) -> list:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT * FROM ventas WHERE fecha = ? ORDER BY id DESC
        """, (fecha_hoy,))
        ventas = self.cursor.fetchall()

        resultado = []
        for v in ventas:
            self.cursor.execute("""
                SELECT producto, cantidad FROM venta_productos WHERE venta_id = ?
            """, (v["id"],))
            productos = {p["producto"]: p["cantidad"] for p in self.cursor.fetchall()}
            resultado.append({
                "hora":      v["hora"],
                "total":     v["total"],
                "productos": productos
            })
        return resultado

    def get_historico_7_dias(self) -> list:
        from datetime import timedelta
        hoy = datetime.now().date()
        resultado = []
        for i in range(6, -1, -1):
            dia = hoy - timedelta(days=i)
            fecha_str = dia.strftime("%Y-%m-%d")
            self.cursor.execute("""
                SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE fecha = ?
            """, (fecha_str,))
            total = self.cursor.fetchone()["total"]
            resultado.append({"fecha": dia.strftime("%d/%m"), "total": total})
        return resultado

    def get_kpis_y_graficos(self) -> dict:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

        self.cursor.execute("""
            SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE fecha = ?
        """, (fecha_hoy,))
        total_v = self.cursor.fetchone()["total"]

        self.cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total FROM gastos WHERE fecha = ?
        """, (fecha_hoy,))
        total_g = self.cursor.fetchone()["total"]

        self.cursor.execute("""
            SELECT vp.producto, SUM(vp.cantidad) as cantidad
            FROM venta_productos vp
            JOIN ventas v ON v.id = vp.venta_id
            WHERE v.fecha = ?
            GROUP BY vp.producto
            ORDER BY cantidad DESC
        """, (fecha_hoy,))
        top = {r["producto"]: r["cantidad"] for r in self.cursor.fetchall()}

        return {
            "ventas_hoy":    total_v,
            "gastos_hoy":    total_g,
            "ganancia":      total_v - total_g,
            "top_productos": top
        }

    # ------------------------------------------------------------------
    # Gastos
    # ------------------------------------------------------------------
    def registrar_gasto(self, concepto: str, monto: float):
        try:
            self.cursor.execute("""
                INSERT INTO gastos (fecha, concepto, monto)
                VALUES (?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d"), concepto, monto))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error registrar_gasto: {e}")

    # ------------------------------------------------------------------
    # Cierre de dia
    # ------------------------------------------------------------------
    def cerrar_dia(self, ventas: float, gastos: float, ganancia: float):
        try:
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("""
                INSERT OR REPLACE INTO cierres (fecha, ventas, gastos, ganancia)
                VALUES (?, ?, ?, ?)
            """, (fecha_hoy, ventas, gastos, ganancia))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error cerrar_dia: {e}")

    # ------------------------------------------------------------------
    # Cerrar conexion
    # ------------------------------------------------------------------
    def cerrar(self):
        self.conn.close()