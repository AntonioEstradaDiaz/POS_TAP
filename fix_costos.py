import sqlite3

conn = sqlite3.connect(r'c:\proyectos\mi_app_flet\POS_TAP\data\pos.db')

costos = [
    ('Mole Poblano',      22.0),
    ('Enchiladas Verdes', 17.0),
    ('Chilaquiles Rojos', 14.0),
    ('Pozole Rojo',       25.0),
    ('Chiles Rellenos',   20.0),
    ('Tlayuda Oaxaquena', 27.0),
]

for nombre, costo in costos:
    conn.execute('UPDATE productos SET costo = ? WHERE nombre = ?', (costo, nombre))

conn.commit()

for r in conn.execute('SELECT nombre, precio, costo FROM productos').fetchall():
    print(f"  {r[0]}: precio={r[1]}, costo={r[2]}")

conn.close()
