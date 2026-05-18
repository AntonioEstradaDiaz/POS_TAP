import sqlite3
import os
from contextlib import contextmanager

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._create_tables()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de productos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    precio REAL NOT NULL,
                    stock INTEGER NOT NULL
                )
            ''')
            
            # Tabla de ventas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    total REAL NOT NULL
                )
            ''')
            
            # Tabla de detalles de venta
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS venta_detalles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas (id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos (id)
                )
            ''')
            
            # Tabla de gastos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    concepto TEXT NOT NULL,
                    monto REAL NOT NULL
                )
            ''')
            
            # Tabla de cierres
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cierres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT UNIQUE NOT NULL,
                    ventas REAL NOT NULL,
                    gastos REAL NOT NULL,
                    ganancia REAL NOT NULL
                )
            ''')
            
            conn.commit()
