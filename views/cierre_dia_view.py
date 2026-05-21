import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime

class CierreDiaView(ft.Container):
    """
    Vista de Cierre de Dia - Conectada a la Base de Datos.
    """
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        # CAMBIO: Usamos main_page en lugar de page para evitar conflictos
        self.main_page = page 
        self.dm = data_manager 
        self.content = self._build_ui()

    def _ejecutar_cierre(self, e):
        # Llamamos a la función de tu data_manager que guarda en SQLite
        resumen, ruta_respaldo = self.dm.cerrar_dia()
        
        # Mostramos una notificación de éxito usando self.main_page
        self.main_page.snack_bar = ft.SnackBar(
            ft.Text(f"✅ Día cerrado con éxito. Ganancia: ${resumen['ganancia']}"), 
            bgcolor=ft.Colors.GREEN_700
        )
        self.main_page.snack_bar.open = True
        self.main_page.update()

    def _build_ui(self):
        fecha_str = datetime.now().strftime("%d/%m/%Y")
        
        # Obtenemos los datos reales del día desde la base de datos
        datos_hoy = self.dm.get_kpis_y_graficos()
        ventas_hoy = datos_hoy["ventas_hoy"]
        gastos_hoy = datos_hoy["gastos_hoy"]
        ganancia_neta = ventas_hoy - gastos_hoy

        resumen = [
            {"titulo": "Ventas del Día",  "valor": f"${ventas_hoy:.2f}", "icono": Icons.TRENDING_UP,           "color": "#4ade80"},
            {"titulo": "Gastos del Día",  "valor": f"${gastos_hoy:.2f}", "icono": Icons.TRENDING_DOWN,          "color": "#f87171"},
            {"titulo": "Ganancia Neta",   "valor": f"${ganancia_neta:.2f}", "icono": Icons.ACCOUNT_BALANCE_WALLET, "color": "#38bdf8"},
        ]

        tarjetas = ft.Row([
            ft.Container(
                expand=1, bgcolor="#1e293b", border_radius=12, padding=20,
                content=ft.Row([
                    ft.Icon(r["icono"], size=38, color=r["color"]),
                    ft.Column([
                        ft.Text(r["titulo"], size=13, color="#64748b"),
                        ft.Text(r["valor"],  size=24, weight="bold", color="white"),
                    ], spacing=2)
                ], alignment="center")
            )
            for r in resumen
        ], alignment="spaceEvenly")

        zona_cierre = ft.Container(
            bgcolor="#1e293b",
            border_radius=12,
            padding=30,
            content=ft.Column([
                ft.Text(
                    "Al presionar el botón se guardará el resumen del día en la base de datos.",
                    size=14, color="#94a3b8",
                ),
                ft.Container(height=16),
                ft.ElevatedButton(
                    "🌙  Cerrar Día",
                    bgcolor="#f59e0b",
                    color="#0f172a",
                    height=55,
                    on_click=self._ejecutar_cierre, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
            ], horizontal_alignment="start")
        )

        return ft.Column([
            ft.Row([
                ft.Icon(Icons.NIGHTLIGHT, color="#f59e0b", size=30),
                ft.Text("Cerrar Día", size=26, weight="bold", color="#f59e0b"),
            ], vertical_alignment="center"),
            ft.Text(fecha_str, size=14, color="#64748b"),
            ft.Container(height=20),
            tarjetas,
            ft.Container(height=30),
            zona_cierre,
        ], expand=True)
