import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime


class CierreDiaView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm = data_manager
        self._txt_estado = ft.Text("", size=14, color="#38bdf8")
        self.content = self._build_ui()

    def _build_ui(self):
        data = self.dm.get_kpis_y_graficos()
        fecha_str = datetime.now().strftime("%d/%m/%Y")

        def hacer_cierre(e):
            resumen, ruta = self.dm.cerrar_dia()
            self._txt_estado.value = (
                f"✅ Cierre guardado en:\n{ruta}"
            )
            self._txt_estado.color = "#4ade80"
            self._txt_estado.update()
            snack = ft.SnackBar(
                ft.Text(f"✅ Cierre del día guardado correctamente"),
                bgcolor="#166534"
            )
            self.main_page.overlay.append(snack)
            snack.open = True
            self.main_page.update()

        return ft.Column([
            # Encabezado
            ft.Row([
                ft.Icon(Icons.NIGHTLIGHT, color="#f59e0b", size=30),
                ft.Text("Cerrar Día", size=26, weight="bold", color="#f59e0b"),
            ], vertical_alignment="center"),
            ft.Text(fecha_str, size=14, color="#64748b"),
            ft.Container(height=20),

            # Tarjetas resumen
            ft.Row([
                self._card("Ventas del Día",   f"${data['ventas_hoy']:.2f}",   Icons.TRENDING_UP,           "#4ade80"),
                self._card("Gastos del Día",   f"${data['gastos_hoy']:.2f}",   Icons.TRENDING_DOWN,         "#f87171"),
                self._card("Ganancia",          f"${data['ganancia']:.2f}",     Icons.ACCOUNT_BALANCE_WALLET, "#38bdf8"),
            ], alignment="spaceEvenly"),

            ft.Container(height=30),

            # Zona de cierre
            ft.Container(
                bgcolor="#1e293b",
                border_radius=12,
                padding=30,
                content=ft.Column([
                    ft.Text(
                        "Al presionar el botón se guardará el resumen del día como archivo JSON.",
                        size=14,
                        color="#94a3b8",
                    ),
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "🌙  Cerrar Día",
                        on_click=hacer_cierre,
                        bgcolor="#f59e0b",
                        color="#0f172a",
                        height=55,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    ),
                    ft.Container(height=12),
                    self._txt_estado,
                    ft.Container(height=10),
                    ft.Text(
                        "El archivo se guarda en: data/cierres/YYYY-MM-DD.json",
                        size=12,
                        color="#475569",
                        italic=True
                    ),
                ], horizontal_alignment="start")
            ),
        ], expand=True)

    def _card(self, titulo, valor, icono, color):
        return ft.Container(
            expand=1,
            bgcolor="#1e293b",
            border_radius=12,
            padding=20,
            content=ft.Row([
                ft.Icon(icono, size=38, color=color),
                ft.Column([
                    ft.Text(titulo, size=13, color="#64748b"),
                    ft.Text(valor, size=26, weight="bold", color="white"),
                ], spacing=2)
            ], alignment="center")
        )
