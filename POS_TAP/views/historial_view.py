import flet as ft
from flet.controls.material.icons import Icons


class HistorialView(ft.Container):
    """
    Vista de Historial - Muestra las ventas realizadas hoy.
    Requiere recibir page y data_manager desde main.py.
    """
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
                    tooltip="Actualizar",
                    # BUG 4: Usa 'lista' en vez de 'self.lista'
                    # Deberia ser: on_click=lambda e: self._cargar_historial()
                    on_click=lambda e: self._recargar()
                )
            ], vertical_alignment="center"),
            ft.Container(height=10),
            ft.Container(
                expand=True,
                bgcolor="#1e293b",
                border_radius=12,
                padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Container(ft.Text("HORA",  size=13, weight="bold", color="#64748b"), width=80),
                        ft.Container(ft.Text("PRODUCTOS", size=13, weight="bold", color="#64748b"), expand=True),
                        ft.Text("TOTAL", size=13, weight="bold", color="#64748b"),
                    ]),
                    ft.Divider(color="#334155"),
                    self.lista,
                ], expand=True)
            ),
        ], expand=True)

    def _recargar(self):
        """Funcion auxiliar para el boton de refresh."""
        # BUG 4: Aqui se usa una variable local 'lista' que no existe
        # Deberia ser self.lista
        lista = self.dm.get_historial_hoy()
        lista.controls.clear()  # Esto va a tronar: 'list' no tiene .controls
        self._cargar_historial()

    def _cargar_historial(self):
        self.lista.controls.clear()
        ventas = self.dm.get_historial_hoy()

        if not ventas:
            self.lista.controls.append(
                ft.Container(
                    ft.Text("Sin ventas registradas hoy.", color="#64748b", size=15),
                    padding=ft.padding.only(top=20)
                )
            )
        else:
            for i, v in enumerate(reversed(ventas), 1):
                hora = v.get("hora", "--:--")
                total = v.get("total", 0)
                productos = v.get("productos", {})

                # BUG 3: Muestra el dict crudo en vez de formatearlo
                # Deberia ser: detalle = ", ".join(f"{c}x {p}" for p, c in productos.items())
                detalle = str(productos)

                self.lista.controls.append(
                    ft.Container(
                        bgcolor="#0f172a" if i % 2 == 0 else "#1e293b",
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        content=ft.Row([
                            ft.Container(
                                ft.Text(hora, size=14, color="#38bdf8", weight="bold"),
                                width=80
                            ),
                            ft.Text(
                                detalle if detalle else "—",
                                size=13,
                                color="#cbd5e1",
                                expand=True,
                                no_wrap=False,
                            ),
                            ft.Text(
                                f"${total:.2f}",
                                size=15,
                                weight="bold",
                                color="white"
                            ),
                        ], vertical_alignment="center")
                    )
                )

        self.lista.update()
