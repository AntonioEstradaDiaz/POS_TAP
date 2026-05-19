import flet as ft


class UsuariosView(ft.Container):
    """
    Vista de Gestión de Usuarios (solo Admin).
    - Lista todos los usuarios con su rol.
    - Permite agregar nuevos usuarios (admin o empleado).
    - Permite eliminar usuarios (no al último admin).
    - Permite cambiar contraseña.
    """

    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm        = data_manager
        self.lista     = ft.Column(spacing=8, scroll="auto")
        self.content   = self._build_ui()

    def did_mount(self):
        self._cargar_usuarios()

    # ------------------------------------------------------------------
    # Cargar lista
    # ------------------------------------------------------------------

    def _cargar_usuarios(self):
        self.lista.controls.clear()
        usuarios = self.dm.get_usuarios()

        for u in usuarios:
            es_admin = u["rol"] == "admin"
            color_rol = "#38bdf8" if es_admin else "#4ade80"
            icono_rol = ft.Icons.ADMIN_PANEL_SETTINGS if es_admin else ft.Icons.BADGE

            self.lista.controls.append(
                ft.Container(
                    bgcolor="#1e293b",
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border=ft.border.all(1, "#334155"),
                    content=ft.Row([
                        ft.Icon(icono_rol, color=color_rol, size=22),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(u["usuario"], size=15,
                                    weight="bold", color="white"),
                            ft.Text(u["rol"].capitalize(),
                                    size=12, color=color_rol),
                        ], spacing=2, expand=True),
                        # Botón cambiar contraseña
                        ft.IconButton(
                            ft.Icons.KEY,
                            icon_color="#f59e0b",
                            tooltip="Cambiar contraseña",
                            on_click=lambda e, uid=u["id"], unm=u["usuario"]:
                                self._dialogo_cambiar_pass(uid, unm)
                        ),
                        # Botón eliminar
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_color="#f87171",
                            tooltip="Eliminar usuario",
                            on_click=lambda e, uid=u["id"], unm=u["usuario"]:
                                self._confirmar_eliminar(uid, unm)
                        ),
                    ], vertical_alignment="center")
                )
            )

        try:
            self.lista.update()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Agregar usuario
    # ------------------------------------------------------------------

    def _dialogo_agregar(self, e):
        input_usr = ft.TextField(
            label="Usuario", border_color="#38bdf8", width=280
        )
        input_pass = ft.TextField(
            label="Contraseña", border_color="#38bdf8",
            width=280, password=True, can_reveal_password=True
        )
        dropdown_rol = ft.Dropdown(
            label="Rol",
            width=280,
            border_color="#38bdf8",
            options=[
                ft.dropdown.Option("empleado", "Empleado"),
                ft.dropdown.Option("admin",    "Administrador"),
            ],
            value="empleado",
        )
        txt_err = ft.Text("", color=ft.Colors.RED_400, size=12)

        def guardar(e):
            ok, msg = self.dm.agregar_usuario(
                input_usr.value, input_pass.value, dropdown_rol.value
            )
            if ok:
                dlg.open = False
                self.main_page.update()
                self._cargar_usuarios()
                self._snack(" Usuario creado correctamente", ft.Colors.GREEN_700)
            else:
                txt_err.value = f"❌ {msg}"
                txt_err.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("➕ Nuevo Usuario", color="#38bdf8", weight="bold"),
            content=ft.Container(
                width=320,
                content=ft.Column([
                    input_usr,
                    ft.Container(height=8),
                    input_pass,
                    ft.Container(height=8),
                    dropdown_rol,
                    txt_err,
                ], spacing=4)
            ),
            actions=[
                ft.TextButton("Cancelar",
                              on_click=lambda e: self._cerrar_dlg(dlg),
                              style=ft.ButtonStyle(color="#64748b")),
                ft.ElevatedButton(
                    "Guardar", bgcolor="#38bdf8", color="#0f172a",
                    on_click=guardar
                ),
            ],
            bgcolor="#1e293b",
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    # ------------------------------------------------------------------
    # Cambiar contraseña
    # ------------------------------------------------------------------

    def _dialogo_cambiar_pass(self, user_id, username):
        input_nueva = ft.TextField(
            label="Nueva contraseña", border_color="#38bdf8",
            width=280, password=True, can_reveal_password=True
        )
        txt_err = ft.Text("", color=ft.Colors.RED_400, size=12)

        def guardar(e):
            ok, msg = self.dm.cambiar_password(user_id, input_nueva.value)
            if ok:
                dlg.open = False
                self.main_page.update()
                self._snack("✅ Contraseña actualizada", ft.Colors.GREEN_700)
            else:
                txt_err.value = f"❌ {msg}"
                txt_err.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"🔑 Cambiar contraseña de '{username}'",
                          color="#f59e0b", weight="bold"),
            content=ft.Container(
                width=320,
                content=ft.Column([input_nueva, txt_err], spacing=6)
            ),
            actions=[
                ft.TextButton("Cancelar",
                              on_click=lambda e: self._cerrar_dlg(dlg),
                              style=ft.ButtonStyle(color="#64748b")),
                ft.ElevatedButton(
                    "Guardar", bgcolor="#f59e0b", color="#0f172a",
                    on_click=guardar
                ),
            ],
            bgcolor="#1e293b",
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    # ------------------------------------------------------------------
    # Eliminar usuario
    # ------------------------------------------------------------------

    def _confirmar_eliminar(self, user_id, username):
        def eliminar(e):
            ok, msg = self.dm.eliminar_usuario(user_id)
            dlg.open = False
            self.main_page.update()
            if ok:
                self._cargar_usuarios()
                self._snack(f"🗑 Usuario '{username}' eliminado", ft.Colors.ORANGE_700)
            else:
                self._snack(f"❌ {msg}", ft.Colors.RED_700)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠ Confirmar eliminación", color="#f87171",
                          weight="bold"),
            content=ft.Text(
                f"¿Seguro que deseas eliminar al usuario '{username}'?\nEsta acción no se puede deshacer.",
                color="#cbd5e1", size=14
            ),
            actions=[
                ft.TextButton("Cancelar",
                              on_click=lambda e: self._cerrar_dlg(dlg),
                              style=ft.ButtonStyle(color="#64748b")),
                ft.ElevatedButton(
                    "Eliminar", bgcolor="#f87171", color="white",
                    on_click=eliminar
                ),
            ],
            bgcolor="#1e293b",
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cerrar_dlg(self, dlg):
        dlg.open = False
        self.main_page.update()

    def _snack(self, mensaje, color):
        self.main_page.snack_bar = ft.SnackBar(
            ft.Text(mensaje), bgcolor=color
        )
        self.main_page.snack_bar.open = True
        self.main_page.update()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        return ft.Column([
            ft.Row([
                ft.Text("Gestión de Usuarios", size=26,
                        weight="bold", color="white"),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "NUEVO USUARIO",
                    icon=ft.Icons.PERSON_ADD,
                    bgcolor="#38bdf8",
                    color="#0f172a",
                    height=40,
                    on_click=self._dialogo_agregar,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),
            ]),
            ft.Container(height=16),
            ft.Container(
                expand=True,
                bgcolor="#1e293b",
                border_radius=12,
                padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Text("USUARIO", size=12, weight="bold",
                                color="#64748b", expand=True),
                        ft.Text("ROL", size=12, weight="bold",
                                color="#64748b", width=100),
                        ft.Text("ACCIONES", size=12, weight="bold",
                                color="#64748b", width=90),
                    ]),
                    ft.Divider(color="#334155"),
                    self.lista,
                ], expand=True)
            ),
        ], expand=True)