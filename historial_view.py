import flet as ft
from flet.controls.material.icons import Icons


class EditarVentaDialog(ft.AlertDialog):
    """
    Diálogo para modificar los productos y cantidades de una venta ya registrada.
    Muestra todos los productos del inventario; los que ya están en la orden
    aparecen con su cantidad actual, el resto en 0.
    """

    def __init__(self, page, data_manager, on_guardado):
        super().__init__()
        self.main_page    = page
        self.dm           = data_manager
        self.on_guardado  = on_guardado   # callback para refrescar la lista
        self._venta_id    = None
        self._carrito     = {}            # {nombre: cantidad}
        self._inventario  = {}            # {nombre: {precio, stock}}
        self._lista_items = ft.ListView(spacing=4, height=400)

        self.modal   = True
        self.bgcolor = "#1e293b"
        self.title   = ft.Row([
            ft.Icon(Icons.EDIT_NOTE, color="#38bdf8"),
            ft.Text("Editar Orden", color="#38bdf8", weight="bold", size=18),
        ])
        self.txt_total = ft.Text("$0.00", size=22, weight="bold", color="#38bdf8")
        self.content = ft.Column([
            ft.Container(
                bgcolor="#0f172a",
                border_radius=8,
                padding=12,
                content=self._lista_items,
            ),
            ft.Row([
                ft.Text("NUEVO TOTAL:", size=15, color="#64748b"),
                self.txt_total,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], tight=True, width=480)

        self.actions = [
            ft.TextButton(
                "Cancelar",
                on_click=self._cancelar,
                style=ft.ButtonStyle(color="#64748b"),
            ),
            ft.ElevatedButton(
                "GUARDAR CAMBIOS",
                icon=Icons.SAVE,
                on_click=self._guardar,
                color="#0f172a",
                bgcolor="#38bdf8",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            ),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    # ─── API pública ─────────────────────────────────────────────────────────

    def abrir(self, venta: dict):
        """Recibe la venta completa (con id y productos) y abre el diálogo."""
        self._venta_id   = venta["id"]
        self._inventario = self.dm.get_inventario()
        # Copia del carrito original para que el usuario pueda modificarlo
        self._carrito    = dict(venta["productos"])

        self._render_items()

        if self not in self.main_page.overlay:
            self.main_page.overlay.append(self)
        self.open = True
        self.main_page.update()

    # ─── render ──────────────────────────────────────────────────────────────

    def _render_items(self):
        self._lista_items.controls.clear()

        # Encabezado de columnas
        self._lista_items.controls.append(
            ft.Row([
                ft.Text("PRODUCTO", size=12, weight="bold", color="#64748b", expand=True),
                ft.Text("CANT.", size=12, weight="bold", color="#64748b", width=100, text_align="center"),
                ft.Text("SUBTOTAL", size=12, weight="bold", color="#64748b", width=80, text_align="right"),
            ])
        )
        self._lista_items.controls.append(ft.Divider(color="#334155", height=6))

        for i, (prod, data) in enumerate(self._inventario.items()):
            precio  = data["precio"]
            cant    = self._carrito.get(prod, 0)
            subtotal = cant * precio

            txt_cant    = ft.Text(str(cant), size=15, weight="bold", width=30, text_align="center")
            txt_sub     = ft.Text(f"${subtotal:.2f}", size=13, color="#cbd5e1", width=80, text_align="right")

            def cambiar(delta, p=prod, tc=txt_cant, ts=txt_sub):
                nueva = max(0, self._carrito.get(p, 0) + delta)
                if nueva == 0:
                    self._carrito.pop(p, None)
                else:
                    self._carrito[p] = nueva
                tc.value = str(nueva)
                ts.value = f"${nueva * self._inventario[p]['precio']:.2f}"
                self._actualizar_total()
                self._lista_items.update()

            fila = ft.Container(
                bgcolor="#1e293b" if i % 2 == 0 else "#0f172a",
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                content=ft.Row([
                    ft.Text(prod, size=13, color="white", expand=True),
                    ft.Row([
                        ft.IconButton(
                            icon=Icons.REMOVE,
                            icon_color="#f87171",
                            icon_size=16,
                            tooltip="Quitar uno",
                            on_click=lambda e, d=-1, p=prod, tc=txt_cant, ts=txt_sub: cambiar(d, p, tc, ts),
                        ),
                        txt_cant,
                        ft.IconButton(
                            icon=Icons.ADD,
                            icon_color="#a3e635",
                            icon_size=16,
                            tooltip="Agregar uno",
                            on_click=lambda e, d=1, p=prod, tc=txt_cant, ts=txt_sub: cambiar(d, p, tc, ts),
                        ),
                    ], spacing=0, tight=True),
                    txt_sub,
                ], vertical_alignment="center"),
            )
            self._lista_items.controls.append(fila)

        self._actualizar_total()

    def _actualizar_total(self):
        total = sum(
            cant * self._inventario[p]["precio"]
            for p, cant in self._carrito.items()
            if p in self._inventario
        )
        self.txt_total.value = f"${total:.2f}"
        try:
            self.txt_total.update()
        except Exception:
            pass

    # ─── acciones ────────────────────────────────────────────────────────────

    def _guardar(self, e):
        if not self._carrito:
            self._snack("La orden no puede quedar vacía", ft.Colors.ORANGE_800)
            return

        ok = self.dm.editar_venta(self._venta_id, self._carrito)
        self.open = False
        self.main_page.update()
        if ok:
            self._snack("Orden actualizada correctamente", ft.Colors.GREEN_700)
            self.on_guardado()
        else:
            self._snack("No se pudo actualizar la orden", ft.Colors.RED_700)

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _snack(self, mensaje, color):
        self.main_page.snack_bar = ft.SnackBar(ft.Text(mensaje), bgcolor=color)
        self.main_page.snack_bar.open = True
        self.main_page.update()


class HistorialView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm        = data_manager
        self.lista     = ft.ListView(expand=True, spacing=6)
        self.dialogo_editar = EditarVentaDialog(page, data_manager, self._cargar_historial)
        self.content   = self._build_ui()

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
                    on_click=lambda e: self._cargar_historial()
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
                        ft.Container(ft.Text("HORA",     size=13, weight="bold", color="#64748b"), width=80),
                        ft.Container(ft.Text("PRODUCTOS", size=13, weight="bold", color="#64748b"), expand=True),
                        ft.Text("TOTAL",   size=13, weight="bold", color="#64748b", width=80),
                        ft.Container(width=48),   # espacio botón editar
                    ]),
                    ft.Divider(color="#334155"),
                    self.lista,
                ], expand=True)
            ),
        ], expand=True)

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
                hora     = v.get("hora", "--:--")
                total    = v.get("total", 0)
                productos = v.get("productos", {})
                detalle  = ", ".join(f"{c}x {p}" for p, c in productos.items())

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
                                size=13, color="#cbd5e1", expand=True, no_wrap=False,
                            ),
                            ft.Text(
                                f"${total:.2f}",
                                size=15, weight="bold", color="white", width=80
                            ),
                            ft.IconButton(
                                icon=Icons.EDIT_NOTE,
                                icon_color="#38bdf8",
                                tooltip="Editar orden",
                                on_click=lambda e, venta=v: self.dialogo_editar.abrir(venta),
                            ),
                        ], vertical_alignment="center")
                    )
                )

        self.lista.update()
