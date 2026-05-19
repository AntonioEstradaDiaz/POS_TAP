import flet as ft
from flet.controls.material.icons import Icons

class HistorialView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm = data_manager
        self.lista = ft.ListView(expand=True, spacing=6)
        self.content = self._build_ui()

    def did_mount(self):
        self._cargar_historial()

    def _build_ui(self):
        return ft.Column([
            ft.Row([
                ft.Icon(Icons.HISTORY, color="#38bdf8", size=30),
                ft.Text("Historial de Ventas – Hoy", size=26, weight="bold", color="#38bdf8"),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=Icons.REFRESH,
                    icon_color="#38bdf8",
                    # CORRECCIÓN BUG 6: Referencia correcta a la función
                    on_click=self._recargar 
                )
            ], vertical_alignment="center"),
            ft.Container(height=10),
            ft.Container(
                expand=True, bgcolor="#1e293b", border_radius=12, padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Container(ft.Text("HORA", size=13, weight="bold", color="#64748b"), width=80),
                        ft.Container(ft.Text("PRODUCTOS", size=13, weight="bold", color="#64748b"), expand=True),
                        ft.Text("TOTAL", size=13, weight="bold", color="#64748b"),
                    ]),
                    ft.Divider(color="#334155"),
                    self.lista,
                ], expand=True)
            ),
        ], expand=True)

    def _recargar(self, e):
        # CORRECCIÓN BUG 6: Se simplificó para evitar errores de variables inexistentes
        self._cargar_historial()

    def _cargar_historial(self):
        self.lista.controls.clear()
        ventas = self.dm.get_historial_hoy()

        if not ventas:
            self.lista.controls.append(ft.Text("Sin ventas registradas hoy.", color="#64748b"))
        else:
            for i, v in enumerate(reversed(ventas), 1):
                # CORRECCIÓN BUG 5: Formatear productos de forma legible
                prods_dict = v.get("productos", {})
                detalle = ", ".join(f"{cant}x {prod}" for prod, cant in prods_dict.items())

                self.lista.controls.append(
                    ft.Container(
                        bgcolor="#0f172a" if i % 2 == 0 else "#1e293b",
                        border_radius=8, padding=10,
                        content=ft.Row([
                            ft.Container(ft.Text(v.get("hora", "--:--"), color="#38bdf8", weight="bold"), width=80),
                            ft.Text(detalle if detalle else "—", size=13, color="#cbd5e1", expand=True),
                            ft.Text(f"${v.get('total', 0):.2f}", weight="bold", color="white"),
                        ])
                    )
                )
        self.lista.update()