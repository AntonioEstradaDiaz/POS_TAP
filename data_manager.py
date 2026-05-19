import sqlite3
import json
import os
import hashlib
from datetime import datetime, timedelta


class DataManager:
    """
    Capa de Acceso a Datos (DAL) para el sistema de Punto de Venta.
    Usa SQLite. Incluye gestión de usuarios con roles admin/empleado.
    """

    def __init__(self):
        mobile_storage = os.environ.get("FLET_APP_STORAGE")
        if mobile_storage:
            self.dir_data = os.path.join(mobile_storage, "data")
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.dir_data = os.path.join(base_dir, "..", "data")
        os.makedirs(self.dir_data, exist_ok=True)

        self.db_path = os.path.join(self.dir_data, "pos_tap.db")
        self._crear_tablas()
        self._inicializar_inventario()
        self._inicializar_usuarios()

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Tablas
    # ------------------------------------------------------------------

    def _crear_tablas(self):
        with self._conectar() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS inventario (
                    nombre  TEXT PRIMARY KEY,
                    precio  REAL NOT NULL,
                    stock   INTEGER NOT NULL DEFAULT 100
                );
                CREATE TABLE IF NOT EXISTS ventas (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha     TEXT NOT NULL,
                    hora      TEXT NOT NULL,
                    productos TEXT NOT NULL,
                    total     REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS gastos (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha    TEXT NOT NULL,
                    concepto TEXT NOT NULL,
                    monto    REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cierres (
                    fecha    TEXT PRIMARY KEY,
                    ventas   REAL NOT NULL,
                    gastos   REAL NOT NULL,
                    ganancia REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS usuarios (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario  TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    rol      TEXT NOT NULL CHECK(rol IN ('admin','empleado'))
                );
            """)

    # ------------------------------------------------------------------
    # Usuarios
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _inicializar_usuarios(self):
        """Crea admin por defecto si la tabla está vacía."""
        with self._conectar() as conn:
            if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO usuarios (usuario, password, rol) VALUES (?, ?, ?)",
                    ("admin", self._hash("admin123"), "admin")
                )

    def login(self, usuario: str, password: str):
        """
        Verifica credenciales.
        Retorna {'id', 'usuario', 'rol'} si es correcto, None si falla.
        """
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT id, usuario, rol FROM usuarios WHERE usuario=? AND password=?",
                (usuario.strip(), self._hash(password.strip()))
            ).fetchone()
        return {"id": row["id"], "usuario": row["usuario"], "rol": row["rol"]} if row else None

    def get_usuarios(self) -> list:
        with self._conectar() as conn:
            rows = conn.execute(
                "SELECT id, usuario, rol FROM usuarios ORDER BY rol, usuario"
            ).fetchall()
        return [{"id": r["id"], "usuario": r["usuario"], "rol": r["rol"]} for r in rows]

    def agregar_usuario(self, usuario: str, password: str, rol: str) -> tuple:
        if not usuario or not password:
            return False, "Usuario y contraseña son obligatorios"
        if rol not in ("admin", "empleado"):
            return False, "Rol inválido"
        try:
            with self._conectar() as conn:
                conn.execute(
                    "INSERT INTO usuarios (usuario, password, rol) VALUES (?, ?, ?)",
                    (usuario.strip(), self._hash(password.strip()), rol)
                )
            return True, ""
        except sqlite3.IntegrityError:
            return False, f"El usuario '{usuario}' ya existe"

    def eliminar_usuario(self, user_id: int) -> tuple:
        with self._conectar() as conn:
            u = conn.execute(
                "SELECT rol FROM usuarios WHERE id=?", (user_id,)
            ).fetchone()
            if not u:
                return False, "Usuario no encontrado"
            if u["rol"] == "admin":
                total_admins = conn.execute(
                    "SELECT COUNT(*) FROM usuarios WHERE rol='admin'"
                ).fetchone()[0]
                if total_admins <= 1:
                    return False, "No puedes eliminar el único administrador"
            conn.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
        return True, ""

    def cambiar_password(self, user_id: int, nueva_password: str) -> tuple:
        if not nueva_password:
            return False, "La contraseña no puede estar vacía"
        with self._conectar() as conn:
            cursor = conn.execute(
                "UPDATE usuarios SET password=? WHERE id=?",
                (self._hash(nueva_password.strip()), user_id)
            )
        return (True, "") if cursor.rowcount > 0 else (False, "Usuario no encontrado")

    # ------------------------------------------------------------------
    # Inventario
    # ------------------------------------------------------------------

    def _inicializar_inventario(self):
        base = {
            "Mole Poblano":      {"precio": 45, "stock": 100},
            "Enchiladas Verdes": {"precio": 35, "stock": 100},
            "Chilaquiles Rojos": {"precio": 30, "stock": 100},
            "Pozole Rojo":       {"precio": 50, "stock": 100},
            "Chiles Rellenos":   {"precio": 40, "stock": 100},
            "Tlayuda Oaxaquena": {"precio": 55, "stock": 100},
        }
        with self._conectar() as conn:
            if conn.execute("SELECT COUNT(*) FROM inventario").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO inventario (nombre, precio, stock) VALUES (?, ?, ?)",
                    [(n, d["precio"], d["stock"]) for n, d in base.items()]
                )

    def get_inventario(self) -> dict:
        with self._conectar() as conn:
            rows = conn.execute("SELECT nombre, precio, stock FROM inventario").fetchall()
        return {r["nombre"]: {"precio": r["precio"], "stock": r["stock"]} for r in rows}

    def agregar_producto(self, nombre: str, precio: float, stock: int = 100) -> bool:
        try:
            with self._conectar() as conn:
                conn.execute(
                    "INSERT INTO inventario (nombre, precio, stock) VALUES (?, ?, ?)",
                    (nombre, precio, stock)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_producto(self, nombre: str) -> bool:
        with self._conectar() as conn:
            cursor = conn.execute("DELETE FROM inventario WHERE nombre=?", (nombre,))
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Ventas
    # ------------------------------------------------------------------

    def registrar_venta(self, carrito: dict, total: float):
        ahora = datetime.now()
        with self._conectar() as conn:
            conn.execute(
                "INSERT INTO ventas (fecha, hora, productos, total) VALUES (?, ?, ?, ?)",
                (ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M"),
                 json.dumps(carrito, ensure_ascii=False), total)
            )
            for prod, cant in carrito.items():
                conn.execute(
                    "UPDATE inventario SET stock = stock - ? WHERE nombre=?", (cant, prod)
                )

    def deshacer_ultima_venta(self):
        with self._conectar() as conn:
            ultima = conn.execute(
                "SELECT * FROM ventas ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not ultima:
                return False
            productos = json.loads(ultima["productos"])
            for prod, cant in productos.items():
                conn.execute(
                    "UPDATE inventario SET stock = stock + ? WHERE nombre=?", (cant, prod)
                )
            conn.execute("DELETE FROM ventas WHERE id=?", (ultima["id"],))
        return {"fecha": ultima["fecha"], "hora": ultima["hora"],
                "productos": productos, "total": ultima["total"]}

    # ------------------------------------------------------------------
    # Gastos
    # ------------------------------------------------------------------

    def registrar_gasto(self, concepto: str, monto: float):
        with self._conectar() as conn:
            conn.execute(
                "INSERT INTO gastos (fecha, concepto, monto) VALUES (?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d"), concepto, monto)
            )

    # ------------------------------------------------------------------
    # Historial / KPIs
    # ------------------------------------------------------------------

    def get_historial_hoy(self) -> list:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        with self._conectar() as conn:
            rows = conn.execute(
                "SELECT fecha, hora, productos, total FROM ventas WHERE fecha=?",
                (fecha_hoy,)
            ).fetchall()
        return [{"fecha": r["fecha"], "hora": r["hora"],
                 "productos": json.loads(r["productos"]), "total": r["total"]}
                for r in rows]

    def get_historico_7_dias(self) -> list:
        hoy = datetime.now().date()
        resultado = []
        with self._conectar() as conn:
            for i in range(6, -1, -1):
                dia = hoy - timedelta(days=i)
                fecha_str = dia.strftime("%Y-%m-%d")
                total_dia = conn.execute(
                    "SELECT COALESCE(SUM(total),0) as total FROM ventas WHERE fecha=?",
                    (fecha_str,)
                ).fetchone()["total"]
                resultado.append({"fecha": dia.strftime("%d/%m"), "total": total_dia})
        return resultado

    def get_kpis_y_graficos(self) -> dict:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        with self._conectar() as conn:
            total_v = conn.execute(
                "SELECT COALESCE(SUM(total),0) as total FROM ventas WHERE fecha=?",
                (fecha_hoy,)
            ).fetchone()["total"]
            total_g = conn.execute(
                "SELECT COALESCE(SUM(monto),0) as total FROM gastos WHERE fecha=?",
                (fecha_hoy,)
            ).fetchone()["total"]
            rows = conn.execute(
                "SELECT productos FROM ventas WHERE fecha=?", (fecha_hoy,)
            ).fetchall()
        conteo = {}
        for row in rows:
            for prod, cant in json.loads(row["productos"]).items():
                conteo[prod] = conteo.get(prod, 0) + cant
        return {"ventas_hoy": total_v, "gastos_hoy": total_g,
                "ganancia": total_v - total_g, "top_productos": conteo}

    # ------------------------------------------------------------------
    # Cierre de día
    # ------------------------------------------------------------------

    def cerrar_dia(self) -> tuple:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        with self._conectar() as conn:
            total_ventas = conn.execute(
                "SELECT COALESCE(SUM(total),0) as total FROM ventas WHERE fecha=?",
                (fecha_hoy,)
            ).fetchone()["total"]
            total_gastos = conn.execute(
                "SELECT COALESCE(SUM(monto),0) as total FROM gastos WHERE fecha=?",
                (fecha_hoy,)
            ).fetchone()["total"]
            ganancia = round(total_ventas - total_gastos, 2)
            conn.execute(
                """INSERT INTO cierres (fecha, ventas, gastos, ganancia) VALUES (?,?,?,?)
                   ON CONFLICT(fecha) DO UPDATE SET
                   ventas=excluded.ventas, gastos=excluded.gastos,
                   ganancia=excluded.ganancia""",
                (fecha_hoy, round(total_ventas, 2), round(total_gastos, 2), ganancia)
            )
        return ({"fecha": fecha_hoy, "ventas": round(total_ventas, 2),
                 "gastos": round(total_gastos, 2), "ganancia": ganancia}, self.db_path)