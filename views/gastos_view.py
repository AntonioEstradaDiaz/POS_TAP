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
        self.dm.registrar_gasto(self.input_concepto.value, self.input_monto.value)

        # 4. Limpiar formulario
        self.input_concepto.value = ""
        self.input_monto.value    = ""

        self.main_page.snack_bar = ft.SnackBar(
            ft.Text("✅ Gasto registrado exitosamente"), bgcolor=ft.Colors.GREEN_700
        )
        self.main_page.snack_bar.open = True

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
