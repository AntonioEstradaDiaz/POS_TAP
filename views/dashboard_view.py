import flet as ft
from flet.controls.material.icons import Icons

class DashboardView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.dm = data_manager
        # Ya no usamos self.meta_actual, usamos self.dm.meta_diaria
        self.content = self._build_ui()

    def _actualizar_meta(self, e):
        """Función para cambiar la meta y guardarla en el DataManager"""
        try:
            nueva_meta = float(self.input_meta.value)
            if nueva_meta > 0:
                # GUARDAR EN EL CEREBRO DE LA APP
                self.dm.meta_diaria = nueva_meta
                # Refrescamos la UI
                self.content = self._build_ui()
                self.update()
        except ValueError:
            pass

    def _build_ui(self):
        data = self.dm.get_kpis_y_graficos()
        historico = self.dm.get_historico_7_dias()
        
        # Recuperamos la meta guardada en el data_manager
        meta_actual = self.dm.meta_diaria
        
        ventas_hoy = data['ventas_hoy']
        progreso = min(ventas_hoy / meta_actual, 1.0)
        color_meta = "#4ade80" if progreso >= 1.0 else "#f59e0b"

        # --- Campo para cambiar la meta ---
        self.input_meta = ft.TextField(
            value=str(meta_actual),
            label="Ajustar Meta ($)",
            width=150,
            height=40,
            text_size=12,
            border_color="#334155",
            on_submit=self._actualizar_meta
        )

        # --- Panel de Meta Diaria ---
        panel_meta = ft.Container(
            bgcolor="#1e293b", padding=15, border_radius=10,
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(f"Vendido: ${ventas_hoy:.2f}", size=14, weight="bold", color="white"),
                        ft.Text(f"Objetivo actual: ${meta_actual:.2f}", size=11, color="#94a3b8"),
                    ], spacing=2),
                    ft.Row([
                        self.input_meta,
                        ft.IconButton(
                            icon=Icons.SAVE, 
                            icon_color="#38bdf8", 
                            tooltip="Guardar Meta",
                            on_click=self._actualizar_meta
                        )
                    ])
                ], alignment="spaceBetween"),
                ft.Container(height=5),
                ft.ProgressBar(value=progreso, color=color_meta, bgcolor="#334155", height=10),
                ft.Text(f"Progreso: {progreso*100:.1f}%", size=10, color=color_meta, italic=True)
            ])
        )

        # --- Tarjetas KPI ---
        kpis = ft.Row([
            self._kpi_card("Ventas Hoy", f"${data['ventas_hoy']:.2f}", Icons.TRENDING_UP, "#4ade80"),
            self._kpi_card("Gastos Hoy", f"${data['gastos_hoy']:.2f}", Icons.TRENDING_DOWN, "#f87171"),
            self._kpi_card("Ganancia", f"${data['ventas_hoy'] - data['gastos_hoy']:.2f}", Icons.ACCOUNT_BALANCE_WALLET, "#38bdf8"),
        ], alignment="spaceEvenly")

        # --- Gráfico de barras: Top Productos ---
        top = data["top_productos"]
        max_cant = max(top.values(), default=1)

        barras = ft.Column(
            spacing=8,
            controls=[
                ft.Row([
                    ft.Container(ft.Text(prod, size=12, color="white", no_wrap=True), width=120),
                    ft.Container(
                        width=max(4, int((cant / max_cant) * 200)),
                        height=22,
                        bgcolor="#f59e0b" if cant == max_cant and cant > 0 else "#38bdf8",
                        border_radius=4
                    ),
                    # ESTRELLA AL PRODUCTO MÁS VENDIDO
                    ft.Icon(Icons.STAR, color="#f59e0b", size=18) if cant == max_cant and cant > 0 else ft.Container(width=18),
                    ft.Text(f" {cant}", size=12, color="white", weight="bold"),
                ], vertical_alignment="center")
                for prod, cant in top.items()
            ] if top else [ft.Text("Sin ventas hoy", color="grey")]
        )

        panel_barras = ft.Container(
            expand=1, bgcolor="#1e293b", padding=20, border_radius=10,
            content=ft.Column([
                ft.Row([ft.Text("Top Productos", size=18, weight="bold"), ft.Icon(Icons.LEADERBOARD, size=18, color="#38bdf8")]),
                ft.Divider(color="#334155"),
                barras,
            ])
        )

        # --- Gráfico histórico ---
        max_v = max((d["total"] for d in historico), default=1) or 1
        chart_h = 140
        puntos = ft.Row(
            spacing=0, expand=True, alignment="spaceAround", vertical_alignment="end",
            controls=[
                ft.Column([
                    ft.Text(f"${d['total']:.0f}", size=9, color="#38bdf8"),
                    ft.Container(
                        width=25,
                        height=max(4, int((d["total"] / max_v) * chart_h)),
                        bgcolor="#38bdf8",
                        border_radius=ft.BorderRadius(4, 4, 0, 0),
                    ),
                    ft.Text(d["fecha"], size=9, color="grey"),
                ], horizontal_alignment="center", spacing=4)
                for d in historico
            ]
        )

        panel_historico = ft.Container(
            expand=1, bgcolor="#1e293b", padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("Ventas - Últimos 7 Días", size=18, weight="bold"),
                ft.Divider(color="#334155"),
                ft.Container(content=puntos, height=chart_h + 30),
            ])
        )

        return ft.Column([
            ft.Row([
                ft.Text("Dashboard & Analíticas", size=28, weight="bold", color="#38bdf8"),
                ft.Icon(Icons.AUTO_GRAPH, color="#38bdf8", size=30)
            ], alignment="spaceBetween"),
            panel_meta,
            ft.Container(height=10),
            kpis,
            ft.Container(height=20),
            ft.Row([panel_barras, ft.Container(width=20), panel_historico], expand=True),
        ], expand=True)

    def _kpi_card(self, titulo, valor, icono, color):
        return ft.Container(
            bgcolor="#1e293b", padding=20, border_radius=10, expand=1,
            content=ft.Row([
                ft.Icon(icono, size=35, color=color),
                ft.Column([
                    ft.Text(titulo, size=13, color="#94a3b8"),
                    ft.Text(valor, size=22, weight="bold", color="white"),
                ], spacing=1)
            ], alignment="center")
        )