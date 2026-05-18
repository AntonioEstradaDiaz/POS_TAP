import flet as ft
from flet.controls.material.icons import Icons

class GastosView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page # <-- Aquí está la corrección
        self.dm = data_manager
        
        # Inputs con estilo moderno
        self.input_concepto = ft.TextField(label="Concepto del gasto", text_size=18, border_color="#38bdf8", width=400)
        self.input_monto = ft.TextField(label="Monto ($)", text_size=18, keyboard_type=ft.KeyboardType.NUMBER, border_color="#38bdf8", width=400)
        
        self.content = self._build_ui()

    def _guardar_gasto(self, e):
        if not self.input_concepto.value or not self.input_monto.value:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Por favor, llena ambos campos"), bgcolor=ft.Colors.ORANGE_800)
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return
            
        try:
            monto = float(self.input_monto.value)
        except ValueError:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("El monto debe ser un número"), bgcolor=ft.Colors.RED_700)
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        # Llamada al DataManager
        self.dm.registrar_gasto(self.input_concepto.value, monto)
        
        # Limpiar formulario
        self.input_concepto.value = ""
        self.input_monto.value = ""
        
        self.main_page.snack_bar = ft.SnackBar(ft.Text("Gasto registrado exitosamente"), bgcolor=ft.Colors.GREEN_700)
        self.main_page.snack_bar.open = True
        self.main_page.update()

    def _build_ui(self):
        formulario = ft.Container(
            bgcolor="#1e293b",
            padding=40,
            border_radius=15,
            content=ft.Column([
                ft.Text("Registrar Nuevo Gasto", size=24, weight="bold", color="#38bdf8"),
                ft.Divider(color="#0f172a", height=20),
                self.input_concepto,
                ft.Container(height=10),
                self.input_monto,
                ft.Container(height=20),
                ft.ElevatedButton("GUARDAR GASTO", icon=Icons.SAVE, on_click=self._guardar_gasto,
                                  color="#0f172a", bgcolor="#38bdf8", height=50, width=400,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))
            ], horizontal_alignment="center")
        )
        
        return ft.Column([
            ft.Text("Gestión de Gastos", size=28, weight="bold", color="white"),
            ft.Container(height=30),
            ft.Row([formulario], alignment="center") # Centrar el formulario en la pantalla
        ], expand=True)