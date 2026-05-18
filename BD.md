# Documentación de la Base de Datos - POS_TAP

Este proyecto ha sido migrado de un sistema basado en archivos JSON a una base de datos relacional robusta utilizando **SQLite**.

## Cambios Realizados

1.  **Nuevo Módulo de Base de Datos**: Se creó `core/database.py` para gestionar la conexión y la creación de tablas.
2.  **Migración de Datos**: Se desarrolló un script `migrate_to_sqlite.py` que transfiere automáticamente la información de los archivos `.json` existentes a las nuevas tablas de SQLite.
3.  **Refactorización de DataManager**: El archivo `core/data_manager.py` fue actualizado para realizar todas las operaciones de lectura y escritura directamente en la base de datos, manteniendo la misma interfaz (métodos y retornos) para asegurar la compatibilidad con las vistas existentes.
4.  **Esquema Relacional**: Se implementó un esquema con relaciones (llaves foráneas) para mejorar la integridad de los datos, especialmente entre ventas y sus productos.

## Estructura de la Base de Datos

La base de datos se encuentra en `data/pos_tap.db` y consta de las siguientes tablas:

### 1. `productos`
Almacena el catálogo de platillos e inventario.
- `id`: Identificador único (Auto-increment).
- `nombre`: Nombre del platillo (Único).
- `precio`: Precio actual de venta.
- `stock`: Cantidad disponible.

### 2. `ventas`
Registra la cabecera de cada transacción de venta.
- `id`: Identificador único.
- `fecha`: Fecha de la venta (YYYY-MM-DD).
- `hora`: Hora de la venta (HH:MM).
- `total`: Monto total de la venta.

### 3. `venta_detalles`
Tabla de unión que detalla qué productos se vendieron en cada transacción.
- `id`: Identificador único.
- `venta_id`: Relación con la tabla `ventas`.
- `producto_id`: Relación con la tabla `productos`.
- `cantidad`: Cantidad vendida de ese producto.
- `precio_unitario`: Precio al que se vendió el producto (histórico).

### 4. `gastos`
Registro de egresos del negocio.
- `id`: Identificador único.
- `fecha`: Fecha del gasto.
- `concepto`: Descripción del gasto.
- `monto`: Importe del gasto.

### 5. `cierres`
Resúmenes diarios de operación.
- `id`: Identificador único.
- `fecha`: Fecha del cierre (Única).
- `ventas`: Suma total de ventas del día.
- `gastos`: Suma total de gastos del día.
- `ganancia`: Resultado neto (Ventas - Gastos).

## Ventajas del nuevo sistema

-   **Integridad de Datos**: El uso de llaves foráneas asegura que no existan detalles de venta sin una venta padre o productos inexistentes.
-   **Rendimiento**: Las consultas SQL son mucho más eficientes que cargar y parsear archivos JSON completos, especialmente a medida que crece el historial.
-   **Escalabilidad**: Es más sencillo agregar reportes complejos y análisis estadísticos mediante consultas SQL (`JOIN`, `GROUP BY`, `SUM`).
-   **Concurrencia**: SQLite maneja mejor los accesos simultáneos que la escritura manual de archivos de texto.

## Cómo ejecutar la migración

Si necesitas volver a migrar o inicializar en un entorno nuevo con datos JSON existentes:
```bash
python migrate_to_sqlite.py
```
*Nota: El DataManager inicializará una base de datos vacía con productos por defecto si no encuentra el archivo `.db` ni datos para migrar.*
