import flet as ft

from core.data_manager import DataManager
from views.ventas_view import VentasView
from views.gastos_view import GastosView
from views.dashboard_view import DashboardView
from views.historial_view import HistorialView
from views.cierre_dia_view import CierreDiaView
from views.notas_view import NotasView


def main(page: ft.Page):
    page.title = "POS_TAP - Taller Flet"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    page.padding = 0

    dm = DataManager()

    content_area = ft.Container(expand=True, bgcolor="#0f172a")

    def change_route(e):
        idx = e.control.selected_index

        if idx == 0:
            content_area.content = VentasView(page, dm)

        elif idx == 1:
            content_area.content = GastosView(page, dm)

        elif idx == 2:
            content_area.content = DashboardView(page, dm)

        elif idx == 3:
            content_area.content = HistorialView(page, dm)

        elif idx == 4:
            content_area.content = CierreDiaView()

        elif idx == 5:
            content_area.content = NotasView(page)

        page.update()

    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        bgcolor="#1e293b",
        on_change=change_route,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.SHOPPING_CART,
                label="Ventas"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PAYMENT,
                label="Gastos"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ANALYTICS,
                label="Dashboard"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.HISTORY,
                label="Historial"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CHECK_CIRCLE,
                label="Cerrar Día"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.NOTE,
                label="Notas"
            ),
        ]
    )

    content_area.content = VentasView(page, dm)

    page.add(
        ft.Row(
            [
                sidebar,
                ft.VerticalDivider(width=1, color="#334155"),
                content_area
            ],
            expand=True
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
