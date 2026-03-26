import flet as ft
from flet.controls.material.icons import Icons


class HistorialView(ft.Container):
    """
    Vista de Historial - SOLO ESTRUCTURA DE INTERFAZ
    Sin datos ni logica funcional. Lista vacia.
    """
    def __init__(self):
        super().__init__(expand=True, padding=30)

        lista = ft.ListView(
            expand=True,
            spacing=6,
            controls=[
                ft.Container(
                    ft.Text("Sin ventas registradas por el momento.", color="#64748b", italic=True, size=14),
                    padding=ft.padding.only(top=20)
                )
            ]
        )

        self.content = ft.Column([
            ft.Row([
                ft.Icon(Icons.HISTORY, color="#38bdf8", size=30),
                ft.Text("Historial de Ventas – Hoy", size=26, weight="bold", color="#38bdf8"),
                ft.Container(expand=True),
                ft.IconButton(icon=Icons.REFRESH, icon_color="#38bdf8", tooltip="Actualizar"),
            ], vertical_alignment="center"),
            ft.Container(height=10),
            ft.Container(
                expand=True,
                bgcolor="#1e293b",
                border_radius=12,
                padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Container(ft.Text("HORA",      size=12, weight="bold", color="#64748b"), width=75),
                        ft.Container(ft.Text("PRODUCTOS", size=12, weight="bold", color="#64748b"), expand=True),
                        ft.Text("TOTAL", size=12, weight="bold", color="#64748b"),
                    ]),
                    ft.Divider(color="#334155"),
                    lista,
                ], expand=True)
            ),
        ], expand=True)
