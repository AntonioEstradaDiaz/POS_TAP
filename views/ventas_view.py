import flet as ft
from flet.controls.material.icons import Icons


class VentasView(ft.Container):
    """
    Vista del Punto de Venta - SOLO ESTRUCTURA DE INTERFAZ
    Sin datos ni logica funcional.
    """
    def __init__(self):
        super().__init__(expand=True)

        # --- Catalogo vacio ---
        grid = ft.GridView(
            expand=True,
            max_extent=200,
            child_aspect_ratio=1.2,
            spacing=12,
            run_spacing=12,
        )
        # Tarjeta de placeholder vacia
        for _ in range(6):
            grid.controls.append(
                ft.Card(
                    content=ft.Container(
                        bgcolor="#1e293b",
                        border_radius=10,
                        padding=15,
                        content=ft.Column([
                            ft.Text("Nombre Platillo", weight="bold", size=14,
                                    text_align="center", color="#64748b"),
                            ft.Text("$0.00", color="#38bdf8", size=18, text_align="center"),
                        ], alignment="center", horizontal_alignment="center"),
                    )
                )
            )

        # --- Panel de ticket vacio ---
        lista_ticket = ft.ListView(
            expand=True,
            spacing=8,
            controls=[
                ft.Text("El carrito está vacío", color="#64748b", italic=True, size=14)
            ]
        )

        panel_cobro = ft.Container(
            width=400,
            padding=20,
            bgcolor="#1e293b",
            border_radius=10,
            content=ft.Column([
                ft.Text("ORDEN ACTUAL", size=20, weight="bold"),
                ft.Divider(),
                lista_ticket,
                ft.Divider(),
                ft.Row([
                    ft.Text("TOTAL", size=18),
                    ft.Text("$0.00", size=28, weight="bold", color="#38bdf8")
                ], alignment="spaceBetween"),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "COBRAR",
                    bgcolor="#38bdf8",
                    color="#0f172a",
                    height=55,
                    width=float("inf"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.Container(height=6),
                ft.OutlinedButton(
                    "↩ Deshacer ultima venta",
                    width=float("inf"),
                    height=44,
                    style=ft.ButtonStyle(
                        color="#f87171",
                        side=ft.BorderSide(color="#f87171", width=1),
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),
            ], expand=True)
        )

        self.content = ft.Row([
            ft.Container(content=grid, expand=True, padding=20),
            panel_cobro,
        ], expand=True)
