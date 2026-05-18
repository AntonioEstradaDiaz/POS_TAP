# Mejora implementada: control integral de catálogo, stock y datos válidos

Fecha de implementación: 17/05/2026

## Alcance funcional

1. **Validaciones reforzadas**
   - Los formularios de productos y gastos rechazan campos vacíos, campos con solo espacios, importes inválidos y valores menores o iguales a cero.
   - La capa de datos normaliza textos y valida precios, montos, stock y cantidades antes de escribir en SQLite.
   - Los productos duplicados se bloquean aunque cambien mayúsculas o minúsculas.

2. **Bloqueo por stock insuficiente**
   - El carrito valida stock antes de agregar productos o incrementar cantidades.
   - El cobro vuelve a validar el carrito completo antes de registrar la venta.
   - `DataManager.registrar_venta` descuenta inventario solo si la base de datos confirma que hay stock suficiente, evitando inventario negativo.

3. **Edición de productos existentes**
   - El catálogo ahora muestra acciones separadas para agregar al carrito, editar y eliminar.
   - La edición permite actualizar nombre, precio y stock de un platillo existente sin eliminarlo.
   - Si un producto editado ya estaba en el carrito, el ticket se sincroniza con el nuevo nombre, precio y stock disponible.

## Archivos principales modificados

- `views/ventas_view.py`: validaciones de producto, visualización de stock, bloqueo de carrito/cobro y diálogo de edición.
- `views/gastos_view.py`: validaciones de concepto y monto antes de guardar gastos.
- `core/data_manager.py`: validaciones centrales, edición de productos, bloqueo transaccional por stock y control de duplicados.
- `README.md`: actualización de características y estructura del proyecto.
- `BD.md`: documentación de reglas operativas aplicadas sobre las tablas existentes.

## Base de datos

No se agregó una tabla nueva ni se cambió el esquema de SQLite. Las mejoras usan la tabla existente `productos` para actualizar `nombre`, `precio` y `stock`, y refuerzan las reglas desde la capa de datos antes de insertar o actualizar registros.