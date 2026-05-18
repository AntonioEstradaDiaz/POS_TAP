import os
from datetime import datetime
from .database import Database

class DataManager:
    """
    Capa de Acceso a Datos (DAL) para el sistema de Punto de Venta.
    Controla la persistencia de ventas, inventario y cierres en una base de datos SQLite.
    """
    def __init__(self):
        # En Android/iOS, Flet expone FLET_APP_STORAGE como carpeta de escritura segura.
        # En desktop, usamos la carpeta /data del proyecto.
        mobile_storage = os.environ.get("FLET_APP_STORAGE")
        if mobile_storage:
            self.dir_data = os.path.join(mobile_storage, "data")
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.dir_data = os.path.join(base_dir, "..", "data")
        os.makedirs(self.dir_data, exist_ok=True)

        self.db_path = os.path.join(self.dir_data, "pos_tap.db")
        self.db = Database(self.db_path)
        self._inicializar_inventario()

    @staticmethod
    def _normalizar_texto(valor) -> str:
        if valor is None:
            return ""
        return str(valor).strip()

    @staticmethod
    def _normalizar_decimal_positivo(valor):
        try:
            numero = float(valor)
        except (ValueError, TypeError):
            return None
        if numero <= 0:
            return None
        return numero

    @staticmethod
    def _normalizar_entero_positivo(valor):
        try:
            if isinstance(valor, float) and not valor.is_integer():
                return None
            numero = int(valor)
        except (ValueError, TypeError):
            return None
        if numero <= 0:
            return None
        return numero

    @staticmethod
    def _nombre_producto_duplicado(cursor, nombre: str, producto_id_excluido=None) -> bool:
        cursor.execute("SELECT id, nombre FROM productos")
        nombre_normalizado = nombre.casefold()
        for prod_id, nombre_existente in cursor.fetchall():
            if producto_id_excluido is not None and prod_id == producto_id_excluido:
                continue
            if nombre_existente.strip().casefold() == nombre_normalizado:
                return True
        return False

    # ------------------------------------------------------------------
    # Inventario
    # ------------------------------------------------------------------
    def _inicializar_inventario(self):
        base = {
            "Mole Poblano":       {"precio": 45, "stock": 100},
            "Enchiladas Verdes":  {"precio": 35, "stock": 100},
            "Chilaquiles Rojos":  {"precio": 30, "stock": 100},
            "Pozole Rojo":        {"precio": 50, "stock": 100},
            "Chiles Rellenos":    {"precio": 40, "stock": 100},
            "Tlayuda Oaxaquena":  {"precio": 55, "stock": 100},
        }
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM productos")
            if cursor.fetchone()[0] == 0:
                for nombre, data in base.items():
                    cursor.execute(
                        "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                        (nombre, data['precio'], data['stock'])
                    )
                conn.commit()

    def get_inventario(self) -> dict:
        """Retorna el diccionario con todo el inventario de productos."""
        inv = {}
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, precio, stock FROM productos ORDER BY nombre")
            for row in cursor.fetchall():
                inv[row[0]] = {"precio": row[1], "stock": row[2]}
        return inv

    def agregar_producto(self, nombre: str, precio: float, stock: int = 100) -> bool:
        """
        Agrega un nuevo producto al inventario.
        Retorna True si la operacion fue exitosa, o False si el producto ya existia.
        """
        nombre = self._normalizar_texto(nombre)
        precio = self._normalizar_decimal_positivo(precio)
        stock = self._normalizar_entero_positivo(stock)
        if not nombre or precio is None or stock is None:
            return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if self._nombre_producto_duplicado(cursor, nombre):
                    return False
                cursor.execute(
                    "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                    (nombre, precio, stock)
                )
                conn.commit()
                return True
        except Exception:
            return False

    def editar_producto(self, nombre_actual: str, nuevo_nombre: str, precio: float, stock: int) -> bool:
        """Actualiza nombre, precio y stock de un producto existente."""
        nombre_actual = self._normalizar_texto(nombre_actual)
        nuevo_nombre = self._normalizar_texto(nuevo_nombre)
        precio = self._normalizar_decimal_positivo(precio)
        stock = self._normalizar_entero_positivo(stock)
        if not nombre_actual or not nuevo_nombre or precio is None or stock is None:
            return False

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM productos WHERE nombre = ?", (nombre_actual,))
            row = cursor.fetchone()
            if not row:
                return False

            prod_id = row[0]
            if self._nombre_producto_duplicado(cursor, nuevo_nombre, prod_id):
                return False

            cursor.execute(
                "UPDATE productos SET nombre = ?, precio = ?, stock = ? WHERE id = ?",
                (nuevo_nombre, precio, stock, prod_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def eliminar_producto(self, nombre: str) -> bool:
        """Elimina un producto del inventario de forma permanente."""
        nombre = self._normalizar_texto(nombre)
        if not nombre:
            return False
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM productos WHERE nombre = ?", (nombre,))
            conn.commit()
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Ventas
    # ------------------------------------------------------------------
    def _validar_carrito_stock_con_cursor(self, cursor, carrito: dict):
        if not carrito:
            return False, "El carrito esta vacio."

        for prod_nombre, cant in carrito.items():
            prod_nombre = self._normalizar_texto(prod_nombre)
            cantidad = self._normalizar_entero_positivo(cant)
            if not prod_nombre or cantidad is None:
                return False, "El carrito contiene productos o cantidades invalidas."

            cursor.execute("SELECT stock FROM productos WHERE nombre = ?", (prod_nombre,))
            row = cursor.fetchone()
            if not row:
                return False, f"El producto '{prod_nombre}' ya no existe en el catalogo."

            stock = row[0]
            if cantidad > stock:
                return False, f"Stock insuficiente para '{prod_nombre}'. Disponible: {stock}."

        return True, ""

    def validar_carrito_stock(self, carrito: dict):
        """Valida que todas las cantidades del carrito existan y tengan stock suficiente."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            return self._validar_carrito_stock_con_cursor(cursor, carrito)

    def registrar_venta(self, carrito: dict, total: float):
        """Registra una venta con su estampa de tiempo y descuenta el inventario."""
        total = self._normalizar_decimal_positivo(total)
        if total is None:
            return False

        ahora = datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        hora = ahora.strftime("%H:%M")
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            stock_valido, _ = self._validar_carrito_stock_con_cursor(cursor, carrito)
            if not stock_valido:
                return False

            # Registrar venta
            cursor.execute(
                "INSERT INTO ventas (fecha, hora, total) VALUES (?, ?, ?)",
                (fecha, hora, total)
            )
            venta_id = cursor.lastrowid
            
            # Registrar detalles y descontar stock
            for prod_nombre, cant in carrito.items():
                prod_nombre = self._normalizar_texto(prod_nombre)
                cant = self._normalizar_entero_positivo(cant)
                cursor.execute("SELECT id, precio FROM productos WHERE nombre = ?", (prod_nombre,))
                row = cursor.fetchone()
                if not row:
                    conn.rollback()
                    return False

                prod_id, precio_u = row
                cursor.execute(
                    "INSERT INTO venta_detalles (venta_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                    (venta_id, prod_id, cant, precio_u)
                )
                cursor.execute(
                    "UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?",
                    (cant, prod_id, cant)
                )
                if cursor.rowcount == 0:
                    conn.rollback()
                    return False
            conn.commit()
            return True

    def deshacer_ultima_venta(self):
        """Elimina la ultima venta y restaura el stock correspondiente."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Obtener ultima venta
            cursor.execute("SELECT id, total, fecha, hora FROM ventas ORDER BY id DESC LIMIT 1")
            venta_row = cursor.fetchone()
            if not venta_row:
                return False
            
            venta_id, total, fecha, hora = venta_row
            
            # Obtener productos de esa venta para restaurar stock
            cursor.execute("""
                SELECT p.nombre, vd.producto_id, vd.cantidad 
                FROM venta_detalles vd 
                JOIN productos p ON vd.producto_id = p.id 
                WHERE vd.venta_id = ?
            """, (venta_id,))
            detalles = cursor.fetchall()
            
            productos_restaurados = {}
            for nombre, prod_id, cant in detalles:
                cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cant, prod_id))
                productos_restaurados[nombre] = cant
            
            # Eliminar venta (cascada debería eliminar detalles si se configuró)
            cursor.execute("DELETE FROM venta_detalles WHERE venta_id = ?", (venta_id,))
            cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
            
            conn.commit()
            
            return {
                "fecha": fecha,
                "hora": hora,
                "productos": productos_restaurados,
                "total": total
            }

    # ------------------------------------------------------------------
    # Gastos
    # ------------------------------------------------------------------
    def registrar_gasto(self, concepto, monto):
        concepto = self._normalizar_texto(concepto)
        monto_float = self._normalizar_decimal_positivo(monto)
        if not concepto or monto_float is None:
            return False

        fecha = datetime.now().strftime("%Y-%m-%d")
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO gastos (fecha, concepto, monto) VALUES (?, ?, ?)",
                (fecha, concepto, monto_float)
            )
            conn.commit()
            return True

    # ------------------------------------------------------------------
    # Historial / KPIs
    # ------------------------------------------------------------------
    def get_historial_hoy(self):
        """Retorna lista de ventas del dia actual."""
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        ventas_list = []
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, fecha, hora, total FROM ventas WHERE fecha = ?", (fecha_hoy,))
            ventas = cursor.fetchall()
            
            for v_id, f, h, t in ventas:
                # Obtener productos para cada venta
                cursor.execute("""
                    SELECT p.nombre, vd.cantidad 
                    FROM venta_detalles vd 
                    JOIN productos p ON vd.producto_id = p.id 
                    WHERE vd.venta_id = ?
                """, (v_id,))
                prods = {row[0]: row[1] for row in cursor.fetchall()}
                ventas_list.append({
                    "fecha": f,
                    "hora": h,
                    "productos": prods,
                    "total": t
                })
        return ventas_list

    def get_historico_7_dias(self):
        from datetime import timedelta
        resultado = []
        hoy = datetime.now().date()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for i in range(6, -1, -1):
                dia = hoy - timedelta(days=i)
                fecha_str = dia.strftime("%Y-%m-%d")
                
                cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha = ?", (fecha_str,))
                total_dia = cursor.fetchone()[0] or 0.0
                
                resultado.append({"fecha": dia.strftime("%d/%m"), "total": total_dia})
        return resultado

    def get_kpis_y_graficos(self):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ventas hoy
            cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha = ?", (fecha_hoy,))
            total_v = cursor.fetchone()[0] or 0.0
            
            # Gastos hoy
            cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha = ?", (fecha_hoy,))
            total_g = cursor.fetchone()[0] or 0.0
            
            # Top productos hoy
            cursor.execute("""
                SELECT p.nombre, SUM(vd.cantidad)
                FROM venta_detalles vd
                JOIN ventas v ON vd.venta_id = v.id
                JOIN productos p ON vd.producto_id = p.id
                WHERE v.fecha = ?
                GROUP BY p.nombre
            """, (fecha_hoy,))
            conteo = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "ventas_hoy":    total_v,
            "gastos_hoy":    total_g,
            "ganancia":      total_v - total_g,
            "top_productos": conteo
        }

    def cerrar_dia(self):
        """Calcula el resumen del dia y lo guarda en la tabla cierres."""
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calcular totales
            cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha = ?", (fecha_hoy,))
            total_ventas = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha = ?", (fecha_hoy,))
            total_gastos = cursor.fetchone()[0] or 0.0
            
            ganancia = total_ventas - total_gastos
            
            resumen = {
                "fecha":    fecha_hoy,
                "ventas":   round(total_ventas, 2),
                "gastos":   round(total_gastos, 2),
                "ganancia": round(ganancia, 2)
            }
            
            # Guardar en DB
            cursor.execute("""
                INSERT OR REPLACE INTO cierres (fecha, ventas, gastos, ganancia)
                VALUES (?, ?, ?, ?)
            """, (fecha_hoy, resumen['ventas'], resumen['gastos'], resumen['ganancia']))
            
            conn.commit()
            
        return resumen, "Base de Datos (Tabla cierres)"
