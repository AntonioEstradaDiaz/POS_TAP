import json
import os
import sqlite3
import sys

# Añadir el directorio actual al path para poder importar core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import Database

def migrate():
    # Caminos de los archivos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dir_data = os.path.join(base_dir, "data")
    f_ventas    = os.path.join(dir_data, "ventas.json")
    f_gastos    = os.path.join(dir_data, "gastos.json")
    f_inventario = os.path.join(dir_data, "inventario.json")
    dir_cierres = os.path.join(dir_data, "cierres")
    db_path = os.path.join(dir_data, "pos_tap.db")

    print(f"Iniciando migración a {db_path}...")

    db = Database(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()

    # 1. Migrar Inventario
    if os.path.exists(f_inventario):
        print("Migrando inventario...")
        with open(f_inventario, 'r', encoding='utf-8') as f:
            inv = json.load(f)
            for nombre, data in inv.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                    (nombre, data['precio'], data['stock'])
                )
    
    # 2. Migrar Gastos
    if os.path.exists(f_gastos):
        print("Migrando gastos...")
        with open(f_gastos, 'r', encoding='utf-8') as f:
            gastos = json.load(f)
            for g in gastos:
                cursor.execute(
                    "INSERT INTO gastos (fecha, concepto, monto) VALUES (?, ?, ?)",
                    (g['fecha'], g['concepto'], float(g['monto']))
                )

    # 3. Migrar Ventas
    if os.path.exists(f_ventas):
        print("Migrando ventas...")
        with open(f_ventas, 'r', encoding='utf-8') as f:
            ventas = json.load(f)
            for v in ventas:
                cursor.execute(
                    "INSERT INTO ventas (fecha, hora, total) VALUES (?, ?, ?)",
                    (v['fecha'], v['hora'], v['total'])
                )
                venta_id = cursor.lastrowid
                
                for prod_nombre, cant in v['productos'].items():
                    # Obtener ID del producto
                    cursor.execute("SELECT id, precio FROM productos WHERE nombre = ?", (prod_nombre,))
                    row = cursor.fetchone()
                    if row:
                        prod_id, precio_actual = row
                        cursor.execute(
                            "INSERT INTO venta_detalles (venta_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                            (venta_id, prod_id, cant, precio_actual)
                        )
                    else:
                        # Si por alguna razón el producto no existe en el inventario actual, lo creamos con stock 0
                        print(f"Aviso: Producto '{prod_nombre}' no encontrado en inventario. Creando entrada temporal.")
                        cursor.execute(
                            "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                            (prod_nombre, v['total'] / cant, 0) # Estimación de precio
                        )
                        prod_id = cursor.lastrowid
                        cursor.execute(
                            "INSERT INTO venta_detalles (venta_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                            (venta_id, prod_id, cant, v['total'] / cant)
                        )

    # 4. Migrar Cierres
    if os.path.exists(dir_cierres):
        print("Migrando cierres...")
        for filename in os.listdir(dir_cierres):
            if filename.endswith(".json"):
                with open(os.path.join(dir_cierres, filename), 'r', encoding='utf-8') as f:
                    c = json.load(f)
                    cursor.execute(
                        "INSERT OR IGNORE INTO cierres (fecha, ventas, gastos, ganancia) VALUES (?, ?, ?, ?)",
                        (c['fecha'], c['ventas'], c['gastos'], c['ganancia'])
                    )
    
    conn.commit()
    conn.close()
    print("Migración completada con éxito.")

if __name__ == "__main__":
    migrate()
