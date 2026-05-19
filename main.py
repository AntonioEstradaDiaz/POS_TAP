import flet as ft
from data_manager import DataManager

# Vistas compartidas
from views.login_view     import LoginView
from views.empleado_view  import EmpleadoView

# Vistas solo Admin
from views.gastos_view    import GastosView
from views.dashboard_view import DashboardView
from views.historial_view import HistorialView
from views.usuarios_view  import UsuariosView


def main(page: ft.Page):
    page.title            = "POS TAP"
    page.theme_mode       = ft.ThemeMode.DARK
    page.bgcolor          = "#0f172a"
    page.padding          = 0
    page.window_width     = 1050
    page.window_height    = 720
    page.window_resizable = True

    dm = DataManager()

    # ------------------------------------------------------------------
    # Helpers de navegación
    # ------------------------------------------------------------------

    def cambiar_vista(vista):
        page.controls.clear()
        page.controls.append(vista)
        page.update()

    def ir_login():
        cambiar_vista(LoginView(page, dm, on_login=on_login))

    # ------------------------------------------------------------------
    # Callback de login: redirige según rol
    # ------------------------------------------------------------------

    def on_login(usuario: dict):
        """Recibe {'id', 'usuario', 'rol'} y carga la vista correcta."""
        if usuario["rol"] == "admin":
            cambiar_vista(_panel_admin(usuario))
        else:
            cambiar_vista(EmpleadoView(page, dm, usuario, on_logout=ir_login))

    # ------------------------------------------------------------------
    # Panel Admin
    # ------------------------------------------------------------------

    def _panel_admin(usuario: dict) -> ft.Row:
        area = ft.Container(expand=True)

        vistas = {
            0: lambda: EmpleadoView(page, dm, usuario, on_logout=ir_login),
            1: lambda: GastosView(page, dm),
            2: lambda: DashboardView(page, dm),
            3: lambda: HistorialView(page, dm),
            4: lambda: UsuariosView(page, dm),
        }

        def cambiar(index):
            area.content = vistas[index]()
            try:
                area.update()
            except Exception:
                pass

        rail = ft.NavigationRail(
            selected_index=2,
            label_type=ft.NavigationRailLabelType.ALL,
            bgcolor="#1e293b",
            indicator_color="#38bdf8",
            min_width=100,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.POINT_OF_SALE_OUTLINED,
                    selected_icon=ft.Icons.POINT_OF_SALE,
                    label="Ventas",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ATTACH_MONEY_OUTLINED,
                    selected_icon=ft.Icons.ATTACH_MONEY,
                    label="Gastos",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD,
                    label="Dashboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.HISTORY_OUTLINED,
                    selected_icon=ft.Icons.HISTORY,
                    label="Historial",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.MANAGE_ACCOUNTS_OUTLINED,
                    selected_icon=ft.Icons.MANAGE_ACCOUNTS,
                    label="Usuarios",
                ),
            ],
            on_change=lambda e: cambiar(e.control.selected_index),
            leading=ft.Column([
                ft.Container(height=8),
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS,
                        color="#38bdf8", size=28),
                ft.Text(usuario["usuario"], size=11,
                        color="#64748b", text_align="center"),  
                ft.Container(height=4),
            ]),
            trailing=ft.IconButton(
                ft.Icons.LOGOUT,
                icon_color="#f87171",
                tooltip="Cerrar sesión",
                on_click=lambda e: ir_login()
            ),
        )

        # Cargar Dashboard al entrar (directo, sin update)
        area.content = DashboardView(page, dm)

        return ft.Row([
            rail,
            ft.VerticalDivider(width=1, color="#334155"),
            area,
        ], expand=True)

    # ------------------------------------------------------------------
    # Arrancar en el login
    # ------------------------------------------------------------------
    ir_login()


ft.app(target=main)