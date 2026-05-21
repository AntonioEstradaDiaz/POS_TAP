import psycopg2

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "pos_tap",
    "user":     "postgres",
    "password": "Cris1206"
}

class DBManager:
    """
    Capa de acceso a PostgreSQL.
    Funciona en paralelo con DataManager (JSON).
    Si la conexion falla, el programa sigue funcionando normal.
    """

    def _conectar(self):
        conn = psycopg2.connect(**DB_CONFIG)
        print("[DB] Conexion exitosa")
        return conn

    def sincronizar_inventario(self, inventario: dict):
        """Sincroniza todo el inventario JSON con la tabla inventario en Postgres."""
        try:
            conn = self._conectar()
            cur = conn.cursor()
            for nombre, data in inventario.items():
                cur.execute("""
                    INSERT INTO inventario (nombre, precio)
                    VALUES (%s, %s)
                    ON CONFLICT (nombre) DO UPDATE SET precio = EXCLUDED.precio
                """, (nombre, data["precio"]))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[DB] Error sincronizando inventario: {e}")

    def agregar_producto(self, nombre: str, precio: float):
        """Agrega un producto nuevo a Postgres."""
        try:
            conn = self._conectar()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO inventario (nombre, precio)
                VALUES (%s, %s)
                ON CONFLICT (nombre) DO NOTHING
            """, (nombre, precio))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[DB] Error agregando producto: {e}")

    def eliminar_producto(self, nombre: str):
        """Elimina un producto de Postgres."""
        try:
            conn = self._conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM inventario WHERE nombre = %s", (nombre,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[DB] Error eliminando producto: {e}")

    def registrar_venta(self, carrito: dict, total: float, inventario: dict):
        """Guarda la venta y su detalle en Postgres."""
        try:
            conn = self._conectar()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO ventas (total) VALUES (%s) RETURNING id
            """, (total,))
            venta_id = cur.fetchone()[0]
            for prod, cant in carrito.items():
                precio = inventario.get(prod, {}).get("precio", 0)
                cur.execute("""
                    INSERT INTO detalle_venta (venta_id, producto, cantidad, precio)
                    VALUES (%s, %s, %s, %s)
                """, (venta_id, prod, cant, precio))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[DB] Error registrando venta: {e}")