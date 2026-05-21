import flet as ft
from flet.controls.material.icons import Icons


class DashboardView(ft.Container):

    def __init__(self, page, data_manager):
        super().__init__(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.dm = data_manager
        self.page_ref = page

        self.content = self._build_ui()

    # ==========================================================
    # REFRESCAR
    # ==========================================================

    def refrescar(self):
        self.content = self._build_ui()
        self.update()

    # ==========================================================
    # CAMBIAR TEMA
    # ==========================================================

    def cambiar_tema(self, e):

        if self.page_ref.theme_mode == ft.ThemeMode.DARK:
            self.page_ref.theme_mode = ft.ThemeMode.LIGHT
        else:
            self.page_ref.theme_mode = ft.ThemeMode.DARK

        self.page_ref.update()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):

        data = self.dm.get_kpis_y_graficos()
        historico = self.dm.get_historico_7_dias()

        # ======================================================
        # KPI CARDS
        # ======================================================

        kpis = ft.Row([

            self._kpi_card(
                "Ventas Hoy",
                f"${data['ventas_hoy']:.2f}",
                Icons.TRENDING_UP,
                "#4ade80"
            ),

            self._kpi_card(
                "Gastos Hoy",
                f"${data['gastos_hoy']:.2f}",
                Icons.TRENDING_DOWN,
                "#f87171"
            ),

            self._kpi_card(
                "Ganancia",
                f"${data['ventas_hoy'] - data['gastos_hoy']:.2f}",
                Icons.ACCOUNT_BALANCE_WALLET,
                "#38bdf8"
            ),

        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # ======================================================
        # TOP PRODUCTOS
        # ======================================================

        top = data["top_productos"]

        max_top = max(top.values()) if top else 1

        barras = ft.Column(
            spacing=10,

            controls=[

                ft.Row([

                    # ==========================================
                    # NOMBRE PRODUCTO
                    # ==========================================

                    ft.Container(
                        width=220,

                        content=ft.Row([

                            ft.Text(

                                (
                                    "🥇 " + prod if i == 0 else
                                    "🥈 " + prod if i == 1 else
                                    "🥉 " + prod if i == 2 else
                                    prod
                                ),

                                size=13,

                                color=(

                                    "#FFD700" if i == 0 else
                                    "#C0C0C0" if i == 1 else
                                    "#CD7F32" if i == 2 else
                                    ft.Colors.ON_SURFACE
                                ),

                                weight="bold"
                            ),

                            ft.Container(

                                visible=i < 3,

                                bgcolor=(

                                    "#FFD700" if i == 0 else
                                    "#C0C0C0" if i == 1 else
                                    "#CD7F32"
                                ),

                                border_radius=8,

                                padding=ft.padding.symmetric(
                                    horizontal=6,
                                    vertical=2
                                ),

                                content=ft.Text(

                                    (
                                        "TOP #1" if i == 0 else
                                        "TOP #2" if i == 1 else
                                        "TOP #3"
                                    ),

                                    size=9,
                                    color="black",
                                    weight="bold"
                                )
                            )

                        ], spacing=6)
                    ),

                    # ==========================================
                    # BARRA
                    # ==========================================

                    ft.Container(

                        width=max(20, (cant / max_top) * 250),

                        height=24,

                        bgcolor=(

                            "#FFD700" if i == 0 else
                            "#C0C0C0" if i == 1 else
                            "#CD7F32" if i == 2 else
                            "#38bdf8"
                        ),

                        border_radius=6,
                    ),

                    # ==========================================
                    # CANTIDAD
                    # ==========================================

                    ft.Text(

                        (
                            f"🔥 {cant}" if i == 0 else
                            f"⭐ {cant}" if i == 1 else
                            f"✨ {cant}" if i == 2 else
                            f"{cant}"
                        ),

                        size=13,

                        color=(

                            "#FFD700" if i == 0 else
                            "#C0C0C0" if i == 1 else
                            "#CD7F32" if i == 2 else
                            "#38bdf8"
                        ),

                        weight="bold"
                    )

                ])

                for i, (prod, cant) in enumerate(top.items())
            ]
        )

        panel_barras = ft.Container(

            expand=1,

            bgcolor=ft.Colors.SURFACE,

            padding=20,

            border_radius=10,

            content=ft.Column([

                ft.Text(
                    "Top Productos Hoy",
                    size=18,
                    weight="bold",
                    color=ft.Colors.ON_SURFACE
                ),

                ft.Divider(color="#334155"),

                barras,

            ])
        )

        # ======================================================
        # HISTÓRICO 7 DÍAS
        # ======================================================

        max_v = max((d["total"] for d in historico), default=1) or 1

        chart_h = 140

        puntos = ft.Row(

            spacing=0,

            expand=True,

            alignment="spaceAround",

            vertical_alignment="end",

            controls=[

                ft.Column([

                    ft.Text(
                        f"${d['total']:.0f}",
                        size=9,
                        color="#38bdf8",
                        text_align="center"
                    ),

                    ft.Container(

                        width=28,

                        height=max(
                            4,
                            int((d["total"] / max_v) * chart_h)
                        ),

                        bgcolor="#38bdf8",

                        border_radius=ft.BorderRadius(
                            top_left=4,
                            top_right=4,
                            bottom_left=0,
                            bottom_right=0
                        ),
                    ),

                    ft.Text(
                        d["fecha"],
                        size=9,
                        color="grey",
                        text_align="center"
                    ),

                ],

                horizontal_alignment="center",
                spacing=4)

                for d in historico
            ]
        )

        panel_historico = ft.Container(

            expand=1,

            bgcolor=ft.Colors.SURFACE,

            padding=20,

            border_radius=10,

            content=ft.Column([

                ft.Text(
                    "Ventas - Últimos 7 Días",
                    size=18,
                    weight="bold",
                    color=ft.Colors.ON_SURFACE
                ),

                ft.Divider(color="#334155"),

                ft.Container(
                    content=puntos,
                    height=chart_h + 30
                ),

            ])
        )

        # ======================================================
        # MAIN LAYOUT
        # ======================================================

        return ft.Column([

            # ==================================================
            # HEADER
            # ==================================================

            ft.Row([

                ft.Text(
                    "Dashboard & Analíticas",
                    size=28,
                    weight="bold",
                    color="#38bdf8"
                ),

                ft.Container(expand=True),

                ft.IconButton(

                    icon=

                    Icons.LIGHT_MODE
                    if self.page_ref.theme_mode == ft.ThemeMode.DARK
                    else Icons.DARK_MODE,

                    icon_color="#38bdf8",

                    tooltip="Cambiar tema",

                    on_click=self.cambiar_tema
                )

            ]),

            ft.Container(height=20),

            kpis,

            ft.Container(height=20),

            ft.Row([
                panel_barras,
                ft.Container(width=20),
                panel_historico
            ], expand=True),

        ], expand=True)

    # ==========================================================
    # KPI CARD
    # ==========================================================

    def _kpi_card(self, titulo, valor, icono, color):

        return ft.Container(

            bgcolor=ft.Colors.SURFACE,

            padding=20,

            border_radius=10,

            expand=1,

            content=ft.Row([

                ft.Icon(
                    icono,
                    size=40,
                    color=color
                ),

                ft.Column([

                    ft.Text(
                        titulo,
                        size=14,
                        color="grey"
                    ),

                    ft.Text(
                        valor,
                        size=24,
                        weight="bold",
                        color=ft.Colors.ON_SURFACE
                    ),

                ], spacing=2)

            ], alignment="center")
        )
