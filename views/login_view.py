import flet as ft


class LoginView(ft.Container):
    """
    Pantalla de Login única para todos los usuarios.
    Detecta el rol (admin/empleado) y redirige a la vista correspondiente.
    """

    def __init__(self, page, data_manager, on_login):
        super().__init__(expand=True)
        self.main_page  = page
        self.dm         = data_manager
        self.on_login   = on_login   # callback(usuario_dict)

        self.input_usuario = ft.TextField(
            label="Usuario",
            hint_text="Ingresa tu usuario",
            text_size=15,
            border_color="#38bdf8",
            width=340,
            prefix_icon=ft.Icons.PERSON,
            autofocus=True,
        )
        self.input_password = ft.TextField(
            label="Contraseña",
            hint_text="Ingresa tu contraseña",
            text_size=15,
            border_color="#38bdf8",
            width=340,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            on_submit=self._intentar_login,   # Enter para ingresar
        )
        self.txt_error = ft.Text("", color=ft.Colors.RED_400, size=13)
        self.content   = self._build_ui()

    # ------------------------------------------------------------------
    # Lógica de login
    # ------------------------------------------------------------------

    def _intentar_login(self, e=None):
        self.txt_error.value = ""
        usuario  = self.input_usuario.value.strip()
        password = self.input_password.value.strip()

        if not usuario or not password:
            self.txt_error.value = "⚠ Completa ambos campos"
            self.txt_error.update()
            return

        resultado = self.dm.login(usuario, password)

        if resultado:
            self.input_usuario.value  = ""
            self.input_password.value = ""
            self.on_login(resultado)   # pasa {'id', 'usuario', 'rol'}
        else:
            self.txt_error.value = "❌ Usuario o contraseña incorrectos"
            self.input_password.value = ""
            self.main_page.update()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        card = ft.Container(
            width=420,
            bgcolor="#1e293b",
            border_radius=18,
            border=ft.border.all(2, "#38bdf8"),
            padding=ft.padding.symmetric(horizontal=40, vertical=40),
            content=ft.Column([
                # Logo / título
                ft.Icon(ft.Icons.RESTAURANT, size=54, color="#38bdf8"),
                ft.Text("POS TAP", size=30, weight="bold", color="white",
                        text_align="center"),
                ft.Text("Sistema de Punto de Venta", size=13,
                        color="#64748b", text_align="center"),
                ft.Container(height=28),

                # Campos
                self.input_usuario,
                ft.Container(height=10),
                self.input_password,
                ft.Container(height=6),
                self.txt_error,
                ft.Container(height=14),

                # Botón
                ft.ElevatedButton(
                    "INGRESAR",
                    icon=ft.Icons.LOGIN,
                    bgcolor="#38bdf8",
                    color="#0f172a",
                    height=48,
                    width=340,
                    on_click=self._intentar_login,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),
                ft.Container(height=10),
                ft.Text("Contacta al administrador si olvidaste\ntu contraseña.",
                        size=11, color="#475569", text_align="center"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        )

        return ft.Column([
            ft.Row([card], alignment="center"),
        ], expand=True, alignment="center")