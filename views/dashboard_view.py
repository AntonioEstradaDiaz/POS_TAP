import flet as ft
from flet.controls.material.icons import Icons


class DashboardView(ft.Container):
    """
    Vista de Dashboard - Muestra KPIs del dia, top productos y historico 7 dias.
    Requiere recibir page y data_manager desde main.py.
    """
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.dm = data_manager
        self.content = self._build_ui()

    def _build_ui(self):
        data = self.dm.get_kpis_y_graficos()
        historico = self.dm.get_historico_7_dias()

        # --- Tarjetas KPI ---
        kpis = ft.Row([
            self._kpi_card("Ventas Hoy",  f"${data['ventas_hoy']:.2f}",  Icons.TRENDING_UP,            "#4ade80"),
            self._kpi_card("Gastos Hoy",  f"${data['gastos_hoy']:.2f}",  Icons.TRENDING_DOWN,           "#f87171"),
            # BUG 1: error de tipo logico ya que estaban invertidas las variables
            # La ganancia esta calculada al reves (gastos - ventas)
            self._kpi_card("Ganancia",    f"${data['ventas_hoy'] - data['gastos_hoy']:.2f}",  Icons.ACCOUNT_BALANCE_WALLET,  "#38bdf8"),
        ], alignment="spaceEvenly")

        # --- Grafico de barras: Top Productos ---
        top = data["top_productos"]
        max_cant = max(top.values(), default=1)

        barras = ft.Column(
            spacing=8,
            controls=[
                ft.Row([
                    ft.Container(
                        ft.Text(prod, size=12, color="white", no_wrap=True),
                        width=130
                    ),
                    ft.Container(
                        # BUG 2: Usa la cantidad directamente como altura, sin escalar
                        # Un error de logica, asignaba directamente el valor de cant al ancho y
                        # deberia ser: width=max(4, int((cant / max_cant) * 220))
                        width=max(4, int((cant / max_cant) * 220)),
                        height=22,
                        bgcolor="#38bdf8",
                        border_radius=4
                    ),
                    ft.Text(f" {cant}", size=12, color="#38bdf8"),
                ], vertical_alignment="center")
                for prod, cant in top.items()
            ] if top else [ft.Text("Sin ventas hoy", color="grey")]
        )

        panel_barras = ft.Container(
            expand=1, bgcolor="#1e293b", padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("Top Productos Hoy", size=18, weight="bold", color="white"),
                ft.Divider(color="#334155"),
                barras,
            ])
        )

        # --- Grafico historico: Ultimos 7 dias ---
        max_v = max((d["total"] for d in historico), default=1) or 1
        chart_h = 140

        puntos = ft.Row(
            spacing=0,
            expand=True,
            alignment="spaceAround",
            vertical_alignment="end",
            controls=[
                ft.Column([
                    ft.Text(f"${d['total']:.0f}", size=9, color="#38bdf8", text_align="center"),
                    ft.Container(
                        width=28,
                        height=max(4, int((d["total"] / max_v) * chart_h)),
                        bgcolor="#38bdf8",
                        border_radius=ft.BorderRadius(top_left=4, top_right=4, bottom_left=0, bottom_right=0),
                    ),
                    ft.Text(d["fecha"], size=9, color="grey", text_align="center"),
                ], horizontal_alignment="center", spacing=4)
                for d in historico
            ]
        )

        panel_historico = ft.Container(
            expand=1, bgcolor="#1e293b", padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("Ventas - Últimos 7 Días", size=18, weight="bold", color="white"),
                ft.Divider(color="#334155"),
                ft.Container(content=puntos, height=chart_h + 30),
            ])
        )

        return ft.Column([
            ft.Text("Dashboard & Analíticas", size=28, weight="bold", color="#38bdf8"),
            ft.Container(height=20),
            kpis,
            ft.Container(height=20),
            ft.Row([panel_barras, ft.Container(width=20), panel_historico], expand=True),
        ], expand=True)

    def _kpi_card(self, titulo, valor, icono, color):
        return ft.Container(
            bgcolor="#1e293b", padding=20, border_radius=10, expand=1,
            content=ft.Row([
                ft.Icon(icono, size=40, color=color),
                ft.Column([
                    ft.Text(titulo, size=14, color="grey"),
                    ft.Text(valor, size=24, weight="bold", color="white"),
                ], spacing=2)
            ], alignment="center")
        )
