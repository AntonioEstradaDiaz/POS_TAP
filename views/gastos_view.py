import flet as ft
from flet.controls.material.icons import Icons


class GastosView(ft.Container):
    """
    Vista de Gastos - Formulario funcional con validaciones y persistencia.
    """
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm        = data_manager

        # Inputs con estilo moderno
        self.input_concepto = ft.TextField(
            label="Concepto del gasto",
            hint_text="Ej: Compra de ingredientes",
            text_size=16,
            border_color="#38bdf8",
            width=400,
        )
        self.input_monto = ft.TextField(
            label="Monto ($)",
            hint_text="Ej: 150.00",
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8",
            width=400,
        )

        self.content = self._build_ui()

    def _guardar_gasto(self, e):
        # 1. Validar campos vacios
        if not self.input_concepto.value or not self.input_monto.value:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ Por favor, llena ambos campos"), bgcolor=ft.Colors.ORANGE_800
            )
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        # 2. Validar que el monto sea un numero valido
        try:
            monto = float(self.input_monto.value)
        except ValueError:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ El monto debe ser un número válido"), bgcolor=ft.Colors.RED_700
            )
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        # 3. Guardar via DataManager
        #error 1 self.dm.registrar_gasto(self.input_concepto.value, self.input_monto.value)
       # Antes:
# El vaor del monto (self.input_monto.value) se enviaba como string es decir:
# "150.00 Aunque antes se hacia la validacion:
# monto = float(self.input_monto.value) ese valor convertido no se utilizaba.

# Problema:
#El sistema guarda el monto como texto en lugar de número, lo que puede provocar:
#- errores en operaciones matemáticas (sumas, restas)
#- resultados incorrectos en el dashboard (totales mal calculados)

#- EXPLICACION DEL ERROR
  #- Tipo de error:
   # tipo de dato/ logico:
    #- string (incorrecto)
   # - float (correcto) 
 # - Que causaba el error:
   # No usar la variable ya convertida (monto)
  #- Como se soluciono:
    #self.dm.registrar_gasto(self.input_concepto.value, monto) ```
  #- Resultado:
   # Ahora los datos se almacenan como números (float), permitiendo cálculos correctos en toda la      aplicación.
        
        self.dm.registrar_gasto(self.input_concepto.value, monto)

        # 4. Limpiar formulario
        self.input_concepto.value = ""
        self.input_monto.value    = ""

        self.main_page.snack_bar = ft.SnackBar(
            ft.Text("✅ Gasto registrado exitosamente"), bgcolor=ft.Colors.GREEN_700
        )
        # error 2 self.main_page.snack_bar.open = True
        #Antes:
#El mensaje (SnackBar) no siempre aparecía en pantalla.

#Problema:
#En Flet, los cambios en la interfaz no se reflejan automáticamente, se necesita actualizar la #vista manualmente.

#- EXPLICACION DEL ERROR
 # - Tipo de error:
  # Flujo del framework (Flet) 
  #- Que causaba el error:
   # Falta de actualización de la UI
  #- Como se soluciono:
   # ``` self.main_page.snack_bar.open = True
    #    self.main_page.update()```
  #- Resultado:
   # El mensaje ahora se muestra correctamente cada vez que se registra un gasto.
        
        self.main_page.snack_bar.open = True
        self.main_page.update()
        
    def _build_ui(self):
        formulario = ft.Container(
            bgcolor="#1e293b",
            padding=40,
            border_radius=15,
            content=ft.Column([
                ft.Text("Registrar Nuevo Gasto", size=22, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155", height=25),
                self.input_concepto,
                ft.Container(height=12),
                self.input_monto,
                ft.Container(height=24),
                ft.ElevatedButton(
                    "GUARDAR GASTO",
                    icon=Icons.SAVE,
                    bgcolor="#38bdf8",
                    color="#0f172a",
                    height=50,
                    width=400,
                    on_click=self._guardar_gasto,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ], horizontal_alignment="center")
        )

        return ft.Column([
            ft.Text("Gestión de Gastos", size=28, weight="bold", color="white"),
            ft.Container(height=30),
            ft.Row([formulario], alignment="center"),
        ], expand=True)
