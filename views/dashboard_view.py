import flet as ft
from flet.controls.material.icons import Icons


class DashboardView(ft.Container):
    """
    Vista de Dashboard - SOLO ESTRUCTURA DE INTERFAZ
    Sin datos ni logica funcional. Valores en cero.
    """
    def __init__(self):
        super().__init__(expand=True, padding=30)

        # --- Tarjetas KPI vacias ---
        kpi_data = [
            {"titulo": "Ventas Hoy",  "valor": "$0.00", "icono": Icons.TRENDING_UP,           "color": "#4ade80"},
            {"titulo": "Gastos Hoy",  "valor": "$0.00", "icono": Icons.TRENDING_DOWN,          "color": "#f87171"},
            {"titulo": "Ganancia",    "valor": "$0.00", "icono": Icons.ACCOUNT_BALANCE_WALLET, "color": "#38bdf8"},
        ]

        kpis = ft.Row([
            ft.Container(
                expand=1, bgcolor="#1e293b", padding=20, border_radius=10,
                content=ft.Row([
                    ft.Icon(k["icono"], size=40, color=k["color"]),
                    ft.Column([
                        ft.Text(k["titulo"], size=13, color="#64748b"),
                        ft.Text(k["valor"],  size=22, weight="bold", color="white"),
                    ], spacing=2)
                ], alignment="center")
            )
            for k in kpi_data
        ], alignment="spaceEvenly")

        # --- Grafica de barras vacia (solo estructura) ---
        panel_barras = ft.Container(
            expand=1, bgcolor="#1e293b", padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("Top Productos Hoy", size=18, weight="bold", color="white"),
                ft.Divider(color="#334155"),
                ft.Text("Sin ventas registradas", color="#64748b", italic=True, size=14),
            ])
        )

        # --- Grafica de historico vacia (barras en cero) ---
        dias = ["L", "M", "X", "J", "V", "S", "D"]
        columnas = ft.Row(
            spacing=0, expand=True, alignment="spaceAround", vertical_alignment="end",
            controls=[
                ft.Column([
                    ft.Text("$0", size=9, color="#38bdf8", text_align="center"),
                    ft.Container(width=28, height=4, bgcolor="#38bdf8",
                                 border_radius=ft.BorderRadius(4, 4, 0, 0)),
                    ft.Text(d, size=9, color="grey", text_align="center"),
                ], horizontal_alignment="center", spacing=4)
                for d in dias
            ]
        )
        panel_historico = ft.Container(
            expand=1, bgcolor="#1e293b", padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("Ventas - Últimos 7 Días", size=18, weight="bold", color="white"),
                ft.Divider(color="#334155"),
                ft.Container(content=columnas, height=150),
            ])
        )

        self.content = ft.Column([
            ft.Text("Dashboard & Analíticas", size=28, weight="bold", color="#38bdf8"),
            ft.Container(height=20),
            kpis,
            ft.Container(height=20),
            ft.Row([panel_barras, ft.Container(width=20), panel_historico], expand=True),
        ], expand=True)
