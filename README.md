# POS_TAP — Sistema de Punto de Venta

Aplicación de escritorio desarrollada con **Python + Flet** para gestionar ventas, registrar gastos y visualizar analíticas del negocio en tiempo real.

---

## Estructura del Proyecto

```
POS_TAP/
├── main.py
├── data_manager.py
└── views/
    ├── gastos_view.py
    ├── dashboard_view.py
    └── historial_view.py
```

---

## Funcionamiento de cada Vista

### 1. `gastos_view.py` — Gestión de Gastos

Formulario para registrar un gasto con **concepto** y **monto**.

**Flujo:**
1. El usuario llena los campos `Concepto` y `Monto`.
2. Al presionar **GUARDAR GASTO** se ejecuta `_guardar_gasto()`.
3. Se validan los campos: si alguno está vacío, aparece un `SnackBar` de advertencia.
4. Se convierte el monto a `float`. Si falla, se muestra un error.
5. Si todo es válido, se llama a `data_manager.registrar_gasto(concepto, monto)` pasando el número.
6. Se limpian los campos y se muestra confirmación visual con `page.update()`.

```python
class GastosView(ft.Container):
    def __init__(self, page, data_manager): ...
    def _guardar_gasto(self, e): ...   # Validación y guardado
    def _build_ui(self):          ...  # Construcción de la interfaz
```



---

### 2. `dashboard_view.py` — Dashboard & Analíticas

Muestra un resumen visual del día con **KPIs**, **top productos** e **histórico 7 días**.

**Flujo:**
1. Llama a `data_manager.get_kpis_y_graficos()` para obtener ventas, gastos y productos del día.
2. Llama a `data_manager.get_historico_7_dias()` para el gráfico histórico.
3. Construye 3 tarjetas KPI: *Ventas Hoy*, *Gastos Hoy* y *Ganancia* (`ventas - gastos`).
4. Genera barras horizontales de top productos, escalando el ancho proporcionalmente al máximo.
5. Genera barras verticales con las ventas de los últimos 7 días.

```python
class DashboardView(ft.Container):
    def __init__(self, page, data_manager): ...
    def _build_ui(self):       ...  # KPIs + gráficos
    def _kpi_card(...):        ...  # Tarjeta individual de métrica
```



---

### 3. `historial_view.py` — Historial de Ventas

Lista todas las ventas realizadas **hoy**, con hora, productos y total.

**Flujo:**
1. Al montar la vista (`did_mount`), se ejecuta `_cargar_historial()`.
2. Se limpia `self.lista` (el `ListView`) y se consulta `data_manager.get_historial_hoy()`.
3. Si no hay ventas, muestra un mensaje informativo.
4. Si hay ventas, las recorre en orden inverso (más reciente arriba), formateando los productos como `"2x Taco, 1x Agua"`.
5. El botón llama directamente a `_cargar_historial()` para refrescar la lista.

```python
class HistorialView(ft.Container):
    def __init__(self, page, data_manager): ...
    def did_mount(self):              ...  # Carga inicial automática
    def _build_ui(self):              ...  # Tabla con encabezados y ListView
    def _cargar_historial(self):      ...  # Limpia y repopula la lista
```


---

## Reporte de Bugs Corregidos

### `gastos_view.py` — 2 errores

---

#### Bug #1 — Monto enviado como `string` en lugar de `float`

| Campo | Detalle |
|-------|---------|
| **Tipo** | Error de tipo de dato |
| **Qué lo causaba** | Aunque el monto se convertía a `float` en la variable `monto`, al llamar `registrar_gasto()` se pasaba `self.input_monto.value` (el string original) en lugar de la variable ya convertida. |
| **Consecuencia** | El `DataManager` recibía texto en vez de número. Al sumar gastos en el Dashboard, Python lanzaba: `TypeError: unsupported operand type(s) for +: 'int' and 'str'` |

```python
# Antes (con error)
self.dm.registrar_gasto(self.input_concepto.value, self.input_monto.value)

# Después (corregido)
self.dm.registrar_gasto(self.input_concepto.value, monto)
```

---

#### Bug #2 — Falta `page.update()` al guardar exitosamente

| Campo | Detalle |
|-------|---------|
| **Tipo** | Error de flujo del framework (Flet) |
| **Qué lo causaba** | En los bloques de error sí se llamaba `page.update()`, pero en el bloque de éxito se omitió. En Flet, sin esta llamada la UI no se refresca. |
| **Consecuencia** | El SnackBar de confirmación nunca aparecía y los campos no se limpiaban visualmente en pantalla. |

```python
# Antes (con error)
self.main_page.snack_bar.open = True
# ← fin del método, sin update()

# Después (corregido)
self.main_page.snack_bar.open = True
self.main_page.update()
```

---

### `dashboard_view.py` — 2 errores

---

#### Bug #3 — Ganancia calculada al revés (`gastos - ventas`)

| Campo | Detalle |
|-------|---------|
| **Tipo** | Error de lógica |
| **Qué lo causaba** | Los operandos de la resta estaban invertidos: `gastos_hoy - ventas_hoy`. |
| **Consecuencia** | Cuando las ventas superan los gastos, la ganancia se mostraba como número negativo, engañando al usuario. |

```python
# Antes (con error)
self._kpi_card("Ganancia", f"${data['gastos_hoy'] - data['ventas_hoy']:.2f}", ...)

# Después (corregido)
self._kpi_card("Ganancia", f"${data['ventas_hoy'] - data['gastos_hoy']:.2f}", ...)
```

---

#### Bug #4 — Ancho de barra del gráfico sin escalar

| Campo | Detalle |
|-------|---------|
| **Tipo** | Error de lógica / presentación visual |
| **Qué lo causaba** | Se usaba el valor absoluto de `cant` como `width` en píxeles. La variable `max_cant` estaba calculada pero nunca se usó. |
| **Consecuencia** | Con cantidades pequeñas las barras eran invisibles; con valores grandes se salían de la pantalla. |

```python
# Antes (con error)
width=cant,

# Después (corregido)
width=max(4, int((cant / max_cant) * 220)),
```

---

### `historial_view.py` — 2 errores

---

#### Bug #5 — Productos mostrados como diccionario crudo

| Campo | Detalle |
|-------|---------|
| **Tipo** | Error de presentación / formato de dato |
| **Qué lo causaba** | Se convertía el diccionario de productos a texto con `str()`, mostrando `{'Taco': 2, 'Agua': 1}` en pantalla. |
| **Consecuencia** | El usuario veía texto técnico ilegible en la columna de Productos. |

```python
# Antes (con error)
detalle = str(productos)
# Resultado visible: "{'Taco': 2, 'Agua': 1}"

# Después (corregido)
detalle = ", ".join(f"{c}x {p}" for p, c in productos.items())
# Resultado visible: "2x Taco, 1x Agua"
```

---

#### Bug #6 — Botón de refresh usa variable local en vez de `self.lista`

| Campo | Detalle |
|-------|---------|
| **Tipo** | Error de POO / scope de variable |
| **Qué lo causaba** | `_recargar()` asignaba el resultado de `get_historial_hoy()` a una variable local `lista` (una `list` de Python) y luego llamaba `.controls.clear()` sobre ella como si fuera el `ft.ListView`. |
| **Consecuencia** | `AttributeError: 'list' object has no attribute 'controls'` cada vez que se presionaba el botón |

```python
# Antes (con error)
def _recargar(self):
    lista = self.dm.get_historial_hoy()   # list de Python, no el ListView
    lista.controls.clear()                # AttributeError aquí
    self._cargar_historial()

on_click=lambda e: self._recargar()

# Después (corregido) — se eliminó _recargar(), el botón apunta directo a _cargar_historial
on_click=lambda e: self._cargar_historial()
```

---

## Resumen General de Bugs

| # | Archivo | Tipo de error | Impacto | Visible |
|---|---------|--------------|---------|---------|
| 1 | `gastos_view.py` | Tipo de dato (`str` vs `float`) | Corrompe cálculos de totales | ✅ `TypeError` en Dashboard |
| 2 | `gastos_view.py` | Flujo del framework (falta `update()`) | UI no responde visualmente | ⚠️ Silencioso |
| 3 | `dashboard_view.py` | Lógica (operandos invertidos) | Ganancia aparece negativa | ✅ Dato incorrecto visible |
| 4 | `dashboard_view.py` | Lógica / visual (sin escalar) | Gráfico inutilizable | ✅ Barras incorrectas |
| 5 | `historial_view.py` | Formato de dato (`str(dict)`) | Texto ilegible en tabla | ✅ Visible en UI |
| 6 | `historial_view.py` | POO / scope (`lista` vs `self.lista`) | Crash al refrescar | ✅ `AttributeError` |

---

## Estado Final

Todos los bugs fueron identificados y corregidos. La aplicación funciona correctamente:

- Los gastos se guardan como `float` y los cálculos del Dashboard son precisos.
- La interfaz se actualiza visualmente después de cada operación.
- La ganancia se calcula correctamente como `ventas - gastos`.
- El gráfico de top productos escala proporcionalmente al valor máximo.
- El historial muestra los productos en formato legible (`2x Taco, 1x Agua`).
- El botón refresca el historial sin errores en ejecución.

  
<img width="1584" height="892" alt="image" src="https://github.com/user-attachments/assets/c2d0766b-f23a-41af-b69c-0f7544cfb5b9" />

---

<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/33ae12af-6638-4a4c-b5e2-7cd537ad8c1e" />

---

<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/21acedff-7f64-4e3c-8c60-ab106c62a292" />

---

<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/3d51855b-5774-4d04-ac9a-24bb7e64c73c" />

---

## Tecnologías

- **Python 3.x**
- **Flet** — Framework de UI multiplataforma basado en Flutter
-
