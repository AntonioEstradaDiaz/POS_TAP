import flet as ft
from flet.controls.material.icons import Icons

from core.data_manager import DataManager
from views.ventas_view import VentasView
from views.gastos_view import GastosView
from views.dashboard_view import DashboardView
from views.historial_view import HistorialView
from views.cierre_dia_view import CierreDiaView


def main(page: ft.Page):
    # 1. Configuracion de la ventana
    page.title = "POS_TAP - Taller Flet"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    page.padding = 0

    # 2. Instanciar el cerebro de datos (unico para toda la app)
    dm = DataManager()

    # 3. Contenedor dinamico donde se inyectan las vistas
    content_area = ft.Container(expand=True, bgcolor="#0f172a")

    # 4. Logica de navegacion
    def change_route(e):
        idx = e.control.selected_index
        content_area.content = None
        if idx == 0:
            content_area.content = VentasView(page, dm)   # Dia 1: Funcional
        elif idx == 1:
            content_area.content = GastosView(page, dm)   # Dia 1: Funcional
        elif idx == 2:
            content_area.content = DashboardView(page, dm)   # Dia 2: Funcional
        elif idx == 3:
            content_area.content = HistorialView(page, dm)    # Dia 2: Funcional
        elif idx == 4:
            content_area.content = CierreDiaView()        # Dia 3: Pendiente
        page.update()

    # 5. Barra lateral de navegacion
    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        bgcolor="#1e293b",
        on_change=change_route,
        destinations=[
            ft.NavigationRailDestination(icon=Icons.SHOPPING_CART, label="Ventas"),
            ft.NavigationRailDestination(icon=Icons.PAYMENT,       label="Gastos"),
            ft.NavigationRailDestination(icon=Icons.ANALYTICS,     label="Dashboard"),
            ft.NavigationRailDestination(icon=Icons.HISTORY,       label="Historial"),
            ft.NavigationRailDestination(icon=Icons.NIGHTLIGHT,    label="Cerrar Dia"),
        ]
    )

    # 6. Vista inicial (Ventas - Dia 1)
    content_area.content = VentasView(page, dm)

    # 7. Ensamblar la interfaz
    page.add(
        ft.Row([
            sidebar,
            ft.VerticalDivider(width=1, color="#334155"),
            content_area
        ], expand=True)
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)
