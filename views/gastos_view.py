import flet as ft
from flet.controls.material.icons import Icons

class GastosView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm = data_manager

        self.input_concepto = ft.TextField(label="Concepto del gasto", width=400, border_color="#38bdf8")
        self.input_monto = ft.TextField(label="Monto ($)", width=400, border_color="#38bdf8", keyboard_type=ft.KeyboardType.NUMBER)
        self.content = self._build_ui()

    def _guardar_gasto(self, e):
        if not self.input_concepto.value or not self.input_monto.value:
            self._show_snack("⚠ Por favor, llena ambos campos", ft.Colors.ORANGE_800)
            return

        try:
            monto = float(self.input_monto.value)
        except ValueError:
            self._show_snack("⚠ El monto debe ser un número válido", ft.Colors.RED_700)
            return

        # CORRECCIÓN BUG 3: Se envía 'monto' (float) en lugar del texto
        self.dm.registrar_gasto(self.input_concepto.value, monto)

        # CORRECCIÓN BUG 4: Limpiar y refrescar la UI
        self.input_concepto.value = ""
        self.input_monto.value = ""
        self._show_snack("✅ Gasto registrado exitosamente", ft.Colors.GREEN_700)
        self.main_page.update()

    def _show_snack(self, texto, color):
        self.main_page.snack_bar = ft.SnackBar(ft.Text(texto), bgcolor=color)
        self.main_page.snack_bar.open = True
        self.main_page.update()

    def _build_ui(self):
        formulario = ft.Container(
            bgcolor="#1e293b", padding=40, border_radius=15,
            content=ft.Column([
                ft.Text("Registrar Nuevo Gasto", size=22, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155", height=25),
                self.input_concepto,
                ft.Container(height=12),
                self.input_monto,
                ft.Container(height=24),
                ft.ElevatedButton("GUARDAR GASTO", icon=Icons.SAVE, bgcolor="#38bdf8", color="#0f172a", height=50, width=400, on_click=self._guardar_gasto),
            ], horizontal_alignment="center")
        )
        return ft.Column([
            ft.Text("Gestión de Gastos", size=28, weight="bold", color="white"),
            ft.Container(height=30),
            ft.Row([formulario], alignment="center"),
        ], expand=True)