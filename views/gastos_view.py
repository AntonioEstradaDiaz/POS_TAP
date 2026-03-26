import flet as ft
from flet.controls.material.icons import Icons


class GastosView(ft.Container):
    """
    Vista de Gastos - SOLO ESTRUCTURA DE INTERFAZ
    Sin datos ni logica funcional.
    """
    def __init__(self):
        super().__init__(expand=True, padding=30)

        input_concepto = ft.TextField(
            label="Concepto del gasto",
            hint_text="Ej: Compra de ingredientes",
            text_size=16,
            border_color="#38bdf8",
            width=400,
        )
        input_monto = ft.TextField(
            label="Monto ($)",
            hint_text="Ej: 150.00",
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8",
            width=400,
        )

        formulario = ft.Container(
            bgcolor="#1e293b",
            padding=40,
            border_radius=15,
            content=ft.Column([
                ft.Text("Registrar Nuevo Gasto", size=22, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155", height=25),
                input_concepto,
                ft.Container(height=12),
                input_monto,
                ft.Container(height=24),
                ft.ElevatedButton(
                    "GUARDAR GASTO",
                    icon=Icons.SAVE,
                    bgcolor="#38bdf8",
                    color="#0f172a",
                    height=50,
                    width=400,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ], horizontal_alignment="center")
        )

        self.content = ft.Column([
            ft.Text("Gestión de Gastos", size=28, weight="bold", color="white"),
            ft.Container(height=30),
            ft.Row([formulario], alignment="center"),
        ], expand=True)
