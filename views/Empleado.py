import flet as ft


class EmpleadoView(ft.Container):
    """
    Vista del Empleado: solo puede registrar ventas.
    - Ve el menú de platillos.
    - Agrega productos al carrito.
    - Confirma el pedido y muestra ticket.
    - Botón de cerrar sesión.
    """

    def __init__(self, page, data_manager, usuario, on_logout):
        super().__init__(expand=True, padding=20)
        self.main_page = page
        self.dm        = data_manager
        self.usuario   = usuario       # dict {'id', 'usuario', 'rol'}
        self.on_logout = on_logout
        self.carrito   = {}

        self.texto_total = ft.Text("$0.00", size=26, weight="bold", color="#4ade80")
        self.col_carrito = ft.Column(spacing=6, scroll="auto")
        self.col_menu    = ft.Column(spacing=10, scroll="auto")
        self.content     = self._build_ui()

    # ------------------------------------------------------------------
    # Carrito
    # ------------------------------------------------------------------

    def _agregar(self, nombre, precio):
        self.carrito[nombre] = self.carrito.get(nombre, 0) + 1
        self._refrescar_carrito()

    def _quitar(self, nombre):
        if nombre in self.carrito:
            self.carrito[nombre] -= 1
            if self.carrito[nombre] == 0:
                del self.carrito[nombre]
        self._refrescar_carrito()

    def _refrescar_carrito(self):
        inv = self.dm.get_inventario()
        self.col_carrito.controls.clear()

        if not self.carrito:
            self.col_carrito.controls.append(
                ft.Text("El carrito está vacío", color="#64748b", size=13)
            )
        else:
            for nombre, cant in self.carrito.items():
                precio = inv.get(nombre, {}).get("precio", 0)
                self.col_carrito.controls.append(
                    ft.Row([
                        ft.Text(nombre, size=13, color="white", expand=True),
                        ft.IconButton(
                            ft.Icons.REMOVE_CIRCLE_OUTLINE,
                            icon_color="#f87171", icon_size=18,
                            on_click=lambda e, n=nombre: self._quitar(n)
                        ),
                        ft.Text(f"{cant}", size=14, color="#38bdf8",
                                width=24, text_align="center"),
                        ft.IconButton(
                            ft.Icons.ADD_CIRCLE_OUTLINE,
                            icon_color="#4ade80", icon_size=18,
                            on_click=lambda e, n=nombre, p=precio: self._agregar(n, p)
                        ),
                        ft.Text(f"${precio * cant:.2f}", size=13,
                                color="#94a3b8", width=64, text_align="right"),
                    ], vertical_alignment="center")
                )

        inv = self.dm.get_inventario()
        total = sum(
            inv.get(n, {}).get("precio", 0) * c for n, c in self.carrito.items()
        )
        self.texto_total.value = f"${total:.2f}"
        self.main_page.update()

    # ------------------------------------------------------------------
    # Confirmar pedido → ticket
    # ------------------------------------------------------------------

    def _confirmar_pedido(self, e):
        if not self.carrito:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ Agrega al menos un producto"),
                bgcolor=ft.Colors.ORANGE_800
            )
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        inv   = self.dm.get_inventario()
        total = sum(
            inv.get(n, {}).get("precio", 0) * c for n, c in self.carrito.items()
        )
        self.dm.registrar_venta(dict(self.carrito), total)

        lineas = [
            ft.Row([
                ft.Text(nombre, size=14, color="white", expand=True),
                ft.Text(f"{cant}x", size=13, color="#94a3b8", width=32),
                ft.Text(
                    f"${inv.get(nombre, {}).get('precio', 0) * cant:.2f}",
                    size=14, color="#4ade80", width=72, text_align="right"
                ),
            ])
            for nombre, cant in self.carrito.items()
        ]

        def cerrar(e):
            dlg.open = False
            self.main_page.update()
            self.carrito = {}
            self._refrescar_carrito()
            self._cargar_menu()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("🧾 Ticket de Venta", color="#38bdf8", weight="bold"),
            content=ft.Container(
                width=340,
                content=ft.Column([
                    ft.Divider(color="#334155"),
                    *lineas,
                    ft.Divider(color="#334155"),
                    ft.Row([
                        ft.Text("TOTAL", size=16, weight="bold", color="white"),
                        ft.Text(f"${total:.2f}", size=20,
                                weight="bold", color="#4ade80"),
                    ], alignment="spaceBetween"),
                    ft.Container(height=6),
                    ft.Text("¡Venta registrada exitosamente! ✅",
                            color="#64748b", size=12, text_align="center"),
                ], spacing=8)
            ),
            actions=[
                ft.TextButton("NUEVA VENTA", on_click=cerrar,
                              style=ft.ButtonStyle(color="#38bdf8"))
            ],
            bgcolor="#1e293b",
        )
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    # ------------------------------------------------------------------
    # Menú
    # ------------------------------------------------------------------

    def _cargar_menu(self):
        inv = self.dm.get_inventario()
        self.col_menu.controls.clear()
        for nombre, datos in inv.items():
            precio = datos["precio"]
            stock  = datos["stock"]
            self.col_menu.controls.append(
                ft.Container(
                    bgcolor="#1e293b",
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border=ft.border.all(1, "#334155"),
                    content=ft.Row([
                        ft.Column([
                            ft.Text(nombre, size=15, weight="bold", color="white"),
                            ft.Text(
                                f"Disponibles: {stock}" if stock > 0 else "Sin stock",
                                size=12,
                                color="#64748b" if stock > 0 else "#f87171"
                            ),
                        ], expand=True, spacing=2),
                        ft.Text(f"${precio:.2f}", size=16, weight="bold",
                                color="#38bdf8", width=70, text_align="right"),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            "Agregar",
                            icon=ft.Icons.ADD_SHOPPING_CART,
                            bgcolor="#4ade80" if stock > 0 else "#334155",
                            color="#0f172a",
                            height=36,
                            disabled=stock == 0,
                            on_click=lambda e, n=nombre, p=precio: self._agregar(n, p),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8)
                            )
                        ),
                    ], vertical_alignment="center")
                )
            )
    def did_mount(self):
        self._cargar_menu()
        self._refrescar_carrito()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        panel_menu = ft.Container(
            expand=2, bgcolor="#0f172a", border_radius=14, padding=20,
            content=ft.Column([
                ft.Text("🍽️ Menú del Día", size=20, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155"),
                ft.Container(content=self.col_menu, expand=True),
            ], expand=True)
        )

        panel_carrito = ft.Container(
            expand=1, bgcolor="#0f172a", border_radius=14, padding=20,
            content=ft.Column([
                ft.Text("🛒 Carrito", size=20, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155"),
                ft.Container(content=self.col_carrito, expand=True),
                ft.Divider(color="#334155"),
                ft.Row([
                    ft.Text("Total:", size=16, color="white"),
                    self.texto_total,
                ], alignment="spaceBetween"),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "CONFIRMAR VENTA",
                    icon=ft.Icons.CHECK_CIRCLE,
                    bgcolor="#4ade80",
                    color="#0f172a",
                    height=48,
                    expand=True,
                    on_click=self._confirmar_pedido,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),
            ], expand=True)
        )

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PERSON, color="#64748b"),
                ft.Text(f"Empleado: {self.usuario['usuario']}",
                        size=14, color="#64748b"),
                ft.Container(expand=True),
                ft.TextButton(
                    "Cerrar sesión",
                    icon=ft.Icons.LOGOUT,
                    style=ft.ButtonStyle(color="#f87171"),
                    on_click=lambda e: self.on_logout()
                ),
            ]),
            ft.Container(height=8),
            ft.Row([
                panel_menu,
                ft.Container(width=16),
                panel_carrito,
            ], expand=True),
        ], expand=True)