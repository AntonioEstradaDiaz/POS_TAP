import sqlite3
import os

# Ruta a tu base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "pos.db")

def limpiar_datos_prueba():
    print(f"Conectando a {DB_PATH}...\n")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # 1. Borrar los registros de las tablas de transacciones
            conn.execute("DELETE FROM venta_detalle")
            conn.execute("DELETE FROM ventas")
            conn.execute("DELETE FROM gastos")
            conn.execute("DELETE FROM cierres")
            
            # 2. Reiniciar los contadores de ID (para que las nuevas ventas empiecen en 1)
            conn.execute("DELETE FROM sqlite_sequence WHERE name='ventas'")
            conn.execute("DELETE FROM sqlite_sequence WHERE name='venta_detalle'")
            conn.execute("DELETE FROM sqlite_sequence WHERE name='gastos'")
            conn.execute("DELETE FROM sqlite_sequence WHERE name='cierres'")
            
            # 3. (Opcional) Restaurar el stock de todos los productos a 100
            conn.execute("UPDATE productos SET stock = 100")
            
        print("✅ ¡Limpieza completada!")
        print("✅ Ventas, gastos y cierres han sido eliminados.")
        print("✅ Tu inventario (productos) se mantuvo intacto y el stock se reinició.")
        
    except sqlite3.Error as e:
        print(f"❌ Error al limpiar la base de datos: {e}")

if __name__ == "__main__":
    print("⚠️ ATENCIÓN: Esto borrará el historial de ventas, gastos y cierres.")
    respuesta = input("¿Estás seguro de continuar? (s/n): ").strip().lower()
    
    if respuesta == 's':
        limpiar_datos_prueba()
    else:
        print("Operación cancelada.")
