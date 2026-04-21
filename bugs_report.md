# Reporte de Bugs Encontrados y Solucionados

Este documento detalla los errores encontrados en el proyecto POS_TAP y las soluciones implementadas.

---

### BUG 1: Cálculo de Ganancia Incorrecto
**Archivo:** `views/dashboard_view.py`

*   **Descripción:** La ganancia del día se estaba calculando restando las ventas de los gastos, lo cual es incorrecto y generaba saldos negativos erróneos.
*   **Solución:** Se invirtió la operación para restar los gastos de las ventas totales.

**Código Original:**
```python
# BUG 1: La ganancia esta calculada al reves (gastos - ventas)
self._kpi_card("Ganancia", f"${data['gastos_hoy'] - data['ventas_hoy']:.2f}", Icons.ACCOUNT_BALANCE_WALLET, "#38bdf8")
```

**Código Corregido:**
```python
# BUG 1 CORREGIDO: La ganancia esta calculada correctamente (ventas - gastos)
self._kpi_card("Ganancia", f"${data['ventas_hoy'] - data['gastos_hoy']:.2f}", Icons.ACCOUNT_BALANCE_WALLET, "#38bdf8")
```

---

### BUG 2: Falta de Escalado en Gráfico de Barras
**Archivo:** `views/dashboard_view.py`

*   **Descripción:** El ancho de las barras de los productos más vendidos no estaba escalado. Se usaba el valor de la cantidad directamente como ancho en píxeles, haciendo que las barras fueran casi invisibles para cantidades pequeñas.
*   **Solución:** Se aplicó una fórmula de escalado proporcional basada en un ancho máximo de 220px.

**Código Original:**
```python
# BUG 2: Usa la cantidad directamente como altura, sin escalar
width=cant,
```

**Código Corregido:**
```python
# BUG 2 CORREGIDO: Ahora se escala el ancho de la barra
width=max(4, int((cant / max_cant) * 220)),
```

---

### BUG 3: Visualización de Diccionario Crudo en Historial
**Archivo:** `views/historial_view.py`

*   **Descripción:** La columna de productos en el historial de ventas mostraba el objeto `dict` de Python directamente en la interfaz (ej: `{'Coca-Cola': 1}`).
*   **Solución:** Se implementó un formateo de cadena para mostrar los productos de forma legible (ej: `1x Coca-Cola`).

**Código Original:**
```python
# BUG 3: Muestra el dict crudo en vez de formatearlo
detalle = str(productos)
```

**Código Corregido:**
```python
# BUG 3 CORREGIDO: Muestra los productos formateados
detalle = ", ".join(f"{c}x {p}" for p, c in productos.items())
```

---

### BUG 4: Error de Referencia y Lógica en Recarga
**Archivo:** `views/historial_view.py`

*   **Descripción:** El botón de refrescar llamaba a `_recargar()`, la cual intentaba limpiar una lista de datos (`list`) usando el método `.controls.clear()` (que pertenece a objetos Flet), causando un error en tiempo de ejecución.
*   **Solución:** Se eliminó la función `_recargar()` y se redirigió el evento del botón directamente a `_cargar_historial()`, que ya realiza la lógica correcta.

**Código Original:**
```python
# En __init__ / _build_ui
on_click=lambda e: self._recargar()

# Función con error
def _recargar(self):
    lista = self.dm.get_historial_hoy()
    lista.controls.clear() # Error: 'list' object has no attribute 'controls'
    self._cargar_historial()
```

**Código Corregido:**
```python
# En _build_ui
# BUG 4 CORREGIDO: Llama directamente a self._cargar_historial()
on_click=lambda e: self._cargar_historial()
```

---

### BUG 5 (personal): Error de tipo en el cálculo de KPIs (Suma de Gastos)
**Archivo:** `core/data_manager.py` y `views/gastos_view.py`

*   **Descripción:** Se producía un `TypeError: unsupported operand type(s) for +: 'int' and 'str'` al intentar calcular los KPIs en el Dashboard. Esto ocurría porque los montos de los gastos se estaban guardando como cadenas de texto (`str`) en el archivo JSON, y la función `sum()` fallaba al intentar sumar un entero con una cadena.
*   **Solución:** 
    1. Se modificó `views/gastos_view.py` para pasar el valor numérico ya validado a `DataManager`.
    2. Se actualizó `core/data_manager.py` para asegurar que `registrar_gasto` convierta siempre el monto a `float`.
    3. Se añadieron conversiones explícitas a `float` en todas las funciones de agregación (`get_kpis_y_graficos`, `cerrar_dia`, `get_historico_7_dias`) para hacer el sistema más robusto ante datos inconsistentes.
    4. Se corrigieron los datos existentes en `data/gastos.json`.

**Código Original (`core/data_manager.py`):**
```python
total_g = sum(g["monto"] for g in gastos if g.get("fecha") == fecha_hoy)
```

**Código Corregido (`core/data_manager.py`):**
```python
total_g = sum(float(g.get("monto", 0)) for g in gastos if g.get("fecha") == fecha_hoy)
```
