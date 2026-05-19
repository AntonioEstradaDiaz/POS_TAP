import flet as ft
from flet.controls.material.icons import Icons


class HistorialView(ft.Container):
    """
    Vista de Historial - Muestra las ventas realizadas hoy.
    es_admin=True habilita el botón para agregar productos al inventario.
    """
    def __init__(self, page, data_manager, es_admin: bool = False):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm = data_manager
        self.es_admin = es_admin                          # ← NUEVO

        self.lista = ft.ListView(expand=True, spacing=6)

        # El diálogo solo se construye si es admin
        self._add_dialog = self._crear_dialogo() if self.es_admin else None

        self.content = self._build_ui()

    def did_mount(self):
        self._cargar_historial()

    # ------------------------------------------------------------------
    # Diálogo "Agregar producto" — solo se usa si es_admin=True
    # ------------------------------------------------------------------
    def _crear_dialogo(self):
        txt_nombre   = ft.TextField(label="Nombre del Platillo", width=300)
        txt_precio   = ft.TextField(
            label="Precio", width=300, keyboard_type=ft.KeyboardType.NUMBER
        )
        dd_categoria = ft.Dropdown(
            label="Categoría", width=300, value="comida",
            options=[
                ft.dropdown.Option("comida", "🍽 Comida"),
                ft.dropdown.Option("bebida", "🥤 Bebida"),
                ft.dropdown.Option("postre", "🍮 Postre"),
            ],
        )

        def cancelar(e):
            dialogo.open = False
            self.main_page.update()

        def guardar(e):
            nombre     = txt_nombre.value.strip()
            precio_str = txt_precio.value.strip()
            categoria  = dd_categoria.value or "comida"

            if not nombre or not precio_str:
                self._snack("⚠ Llena todos los campos", "#92400e")
                return
            try:
                precio = float(precio_str)
            except ValueError:
                self._snack("⚠ El precio debe ser un número válido", "#92400e")
                return

            if self.dm.agregar_producto(nombre, precio, categoria=categoria):
                dialogo.open = False
                txt_nombre.value = ""
                txt_precio.value = ""
                self._snack(f"✅ '{nombre}' agregado exitosamente.", "#166534")
            else:
                self._snack("⚠ El platillo ya existe.", "#92400e")
            self.main_page.update()

        dialogo = ft.AlertDialog(
            title=ft.Text("Agregar Nuevo Platillo", weight="bold"),
            content=ft.Column([txt_nombre, txt_precio, dd_categoria], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Guardar", on_click=guardar,
                    style=ft.ButtonStyle(bgcolor="#38bdf8", color="#0f172a"),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        return dialogo

    def _abrir_dialogo(self, e):
        if self._add_dialog not in self.main_page.overlay:
            self.main_page.overlay.append(self._add_dialog)
        self._add_dialog.open = True
        self.main_page.update()

    def _snack(self, texto, color):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        acciones = [
            ft.IconButton(
                icon=Icons.REFRESH,
                icon_color="#38bdf8",
                tooltip="Actualizar",
                on_click=lambda e: self._cargar_historial(),
            )
        ]
        if self.es_admin:
            acciones.append(
                ft.ElevatedButton(
                    "＋ Agregar producto",
                    on_click=self._abrir_dialogo,
                    style=ft.ButtonStyle(
                        bgcolor="#38bdf8",
                        color="#0f172a",
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    height=38,
                )
            )

        return ft.Column([
            ft.Row([
                ft.Icon(Icons.HISTORY, color="#38bdf8", size=30),
                ft.Text("Historial de Ventas – Hoy", size=26, weight="bold", color="#38bdf8"),
                ft.Container(expand=True),
                *acciones,
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
                ], expand=True),
            ),
        ], expand=True)

    def _cargar_historial(self):
        self.lista.controls.clear()
        ventas = self.dm.get_historial_hoy()

        if not ventas:
            self.lista.controls.append(
                ft.Container(
                    ft.Text("Sin ventas registradas hoy.", color="#64748b", size=15),
                    padding=ft.padding.only(top=20),
                )
            )
        else:
            for i, v in enumerate(reversed(ventas), 1):
                hora      = v.get("hora", "--:--")
                total     = v.get("total", 0)
                productos = v.get("productos", {})
                detalle   = ", ".join(f"{c}x {p}" for p, c in productos.items())

                self.lista.controls.append(
                    ft.Container(
                        bgcolor="#0f172a" if i % 2 == 0 else "#1e293b",
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        content=ft.Row([
                            ft.Container(
                                ft.Text(hora, size=14, color="#38bdf8", weight="bold"),
                                width=80,
                            ),
                            ft.Text(
                                detalle if detalle else "—",
                                size=13, color="#cbd5e1",
                                expand=True, no_wrap=False,
                            ),
                            ft.Text(f"${total:.2f}", size=15, weight="bold", color="white"),
                        ], vertical_alignment="center"),
                    )
                )

        self.lista.update()