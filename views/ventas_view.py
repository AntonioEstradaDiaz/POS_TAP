import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import urllib.parse


# ─────────────────────────────────────────────
#  TICKET DIALOG
# ─────────────────────────────────────────────
class TicketDialog(ft.AlertDialog):
    """
    Modal que muestra el ticket de compra con QR apuntando
    al validador web (GitHub Pages / Vercel).
    """

    # ← Pon aquí la URL de tu repositorio/vercel
    URL_BASE = "https://24680055-cell.github.io/post-validador/"

    def __init__(self, page, venta_id: int, productos: dict, total: float, fecha_hora: str):
        super().__init__()
        self.main_page = page

        # --- Texto estilo ticket térmico ---
        lineas = []
        prod_lista_url = []

        for prod, info in productos.items():
            subtotal = info["cantidad"] * info["precio"]
            lineas.append(f"{prod:<18} x{info['cantidad']}  ${subtotal:>6.2f}")
            prod_lista_url.append(f"{info['cantidad']}x {prod}")

        ticket_texto = (
            f"{'='*24}\n"
            f"      POS TAP\n"
            f"{'='*24}\n"
            f"Venta #{venta_id}\n"
            f"{fecha_hora}\n"
            f"{'-'*24}\n"
            + "\n".join(lineas) + "\n"
            + f"{'-'*24}\n"
            + f"TOTAL:             ${total:>7.2f}\n"
            + f"{'='*24}\n"
            f" ¡Gracias por su compra!\n"
        )

        # --- Construir URL para el QR ---
        productos_url = urllib.parse.quote(", ".join(prod_lista_url))
        fecha_url = urllib.parse.quote(fecha_hora)
        link_qr = (
            f"{self.URL_BASE}?id={venta_id}"
            f"&total={total}"
            f"&fecha={fecha_url}"
            f"&prods={productos_url}"
        )

        # --- Generar QR en base64 ---
        qr_img = qrcode.make(link_qr, box_size=4, border=2)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # --- UI del modal ---
        self.title = ft.Text("🧾 Ticket de Compra", weight="bold", size=20, color="#38bdf8")
        self.bgcolor = "#1e293b"
        self.content = ft.Column(
            [
                ft.Container(
                    bgcolor="#0f172a",
                    border_radius=10,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Row(
                                [ft.Image(src=qr_b64, width=160, height=160)],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(height=10),
                            ft.Row(
                                [ft.Text(ticket_texto, font_family="Courier", size=13, color="#e2e8f0")],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=5),
                ft.Text(
                    "📱 ¡Escanea el QR para ver la validación web!",
                    size=11,
                    color="#38bdf8",
                    text_align=ft.TextAlign.CENTER,
                    weight="bold",
                ),
            ],
            tight=True,
            width=360,
        )
        self.actions = [
            ft.ElevatedButton("Cerrar", on_click=self._cerrar, bgcolor="#334155", color="white")
        ]

    def _cerrar(self, e):
        self.open = False
        self.main_page.update()

    def mostrar(self):
        if self not in self.main_page.overlay:
            self.main_page.overlay.append(self)
        self.open = True
        self.main_page.update()


# ─────────────────────────────────────────────
#  DIALOGS DE PRODUCTOS
# ─────────────────────────────────────────────
class AddProductDialog(ft.AlertDialog):
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success

        self.txt_nombre = ft.TextField(label="Nombre del Platillo", width=300)
        self.txt_precio = ft.TextField(
            label="Precio", width=300, keyboard_type=ft.KeyboardType.NUMBER
        )

        self.title = ft.Text("Agregar Nuevo Platillo", weight="bold")
        self.content = ft.Column([self.txt_nombre, self.txt_precio], tight=True)
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.ElevatedButton(
                "Guardar", on_click=self._guardar, bgcolor="#38bdf8", color="#0f172a"
            ),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _guardar(self, e):
        nombre = self.txt_nombre.value.strip()
        precio_str = self.txt_precio.value.strip()

        if not nombre or not precio_str:
            self._mostrar_snackbar("⚠ Llena todos los campos", "#92400e")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            self._mostrar_snackbar("⚠ El precio debe ser un numero valido", "#92400e")
            return

        agregado = self.dm.agregar_producto(nombre, precio)
        if agregado:
            self.open = False
            self.txt_nombre.value = ""
            self.txt_precio.value = ""
            self._mostrar_snackbar(f"✅ Platillo '{nombre}' agregado exitosamente.", "#166534")
            self.on_success()
        else:
            self._mostrar_snackbar("⚠ El platillo ya existe, intenta con otro nombre.", "#92400e")

        self.main_page.update()

    def _mostrar_snackbar(self, texto, color):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()


class DeleteProductDialog(ft.AlertDialog):
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success
        self.producto_a_eliminar = None

        self.title = ft.Text("Eliminar Platillo?", weight="bold")
        self.txt_mensaje = ft.Text("")
        self.content = self.txt_mensaje
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.ElevatedButton(
                "Eliminar Definitivamente",
                on_click=self._eliminar,
                bgcolor="#ef4444",
                color="white",
            ),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def abrir(self, nombre_prod):
        self.producto_a_eliminar = nombre_prod
        self.txt_mensaje.value = (
            f"Estas a punto de eliminar '{nombre_prod}' permanentemente de tu catalogo.\n"
            "Estas seguro?"
        )
        self.open = True
        if self not in self.main_page.overlay:
            self.main_page.overlay.append(self)
        self.main_page.update()

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _eliminar(self, e):
        if self.producto_a_eliminar:
            self.dm.eliminar_producto(self.producto_a_eliminar)
            self.open = False
            self.on_success(self.producto_a_eliminar)


# ─────────────────────────────────────────────
#  CART ITEM ROW
# ─────────────────────────────────────────────
class CartItemRow(ft.Row):
    def __init__(self, nombre_prod: str, precio: float, cantidad: int, on_change):
        super().__init__(alignment="spaceBetween")
        self.nombre_prod = nombre_prod
        self.precio = precio
        self.cantidad = cantidad
        self.on_change = on_change

        self.info_text = ft.Text(f"{self.nombre_prod} (${self.precio:.2f})", expand=True)
        self.btn_minus = ft.IconButton(
            icon=Icons.REMOVE, icon_color="#f87171",
            on_click=self._decrementar, tooltip="Quitar uno"
        )
        self.txt_cantidad = ft.Text(
            str(self.cantidad), weight="bold", size=16, text_align="center", width=25
        )
        self.btn_plus = ft.IconButton(
            icon=Icons.ADD, icon_color="#a3e635",
            on_click=self._incrementar, tooltip="Agregar uno"
        )
        self.btn_delete = ft.IconButton(
            icon=Icons.DELETE, icon_color="#ef4444",
            on_click=self._eliminar, tooltip="Remover todo"
        )
        self.subtotal_text = ft.Text(
            f"${self.cantidad * self.precio:.2f}", weight="bold", width=60, text_align="right"
        )

        self.controls = [
            self.info_text,
            ft.Row([self.btn_minus, self.txt_cantidad, self.btn_plus], tight=True, spacing=0),
            self.subtotal_text,
            self.btn_delete,
        ]

    def _decrementar(self, e):
        if self.cantidad > 1:
            self.cantidad -= 1
            self._actualizar_ui()
            self.on_change(self.nombre_prod, self.cantidad)
        else:
            self._eliminar(e)

    def _incrementar(self, e):
        self.cantidad += 1
        self._actualizar_ui()
        self.on_change(self.nombre_prod, self.cantidad)

    def _eliminar(self, e):
        self.cantidad = 0
        self.on_change(self.nombre_prod, self.cantidad)

    def _actualizar_ui(self):
        self.txt_cantidad.value = str(self.cantidad)
        self.subtotal_text.value = f"${self.cantidad * self.precio:.2f}"
        self.update()


# ─────────────────────────────────────────────
#  VENTAS VIEW
# ─────────────────────────────────────────────
class VentasView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True)
        self.main_page = page
        self.dm = data_manager

        self.carrito = {}
        self.inventario = self.dm.get_inventario()

        self.lista_ticket = ft.ListView(expand=True, spacing=10)
        self.txt_total = ft.Text("$0.00", size=32, weight="bold", color="#38bdf8")
        self.productos_grid = self._create_empty_grid()
        self.add_product_dialog = AddProductDialog(self.main_page, self.dm, self._on_product_added)
        self.delete_product_dialog = DeleteProductDialog(
            self.main_page, self.dm, self._on_product_deleted
        )

        self.content = self._build_layout()
        self._renderizar_catalogo()

    def _create_empty_grid(self) -> ft.GridView:
        return ft.GridView(
            expand=True, max_extent=250, child_aspect_ratio=1.2, spacing=15, run_spacing=15
        )

    def _renderizar_catalogo(self):
        self.productos_grid.controls.clear()

        self.productos_grid.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Agregar Platillo", weight="bold", size=16),
                            ft.Text("+", color="#a3e635", size=24, weight="bold"),
                        ],
                        alignment="center",
                        horizontal_alignment="center",
                    ),
                    padding=10,
                    ink=True,
                    on_click=self._abrir_dialogo_producto,
                    bgcolor="#1e293b",
                    border_radius=10,
                )
            )
        )

        for prod, data in self.inventario.items():
            self.productos_grid.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(prod, weight="bold", size=16, text_align="center"),
                                ft.Row(
                                    [
                                        ft.Text(f"${data['precio']}", color="#38bdf8", size=18),
                                        ft.IconButton(
                                            icon=Icons.DELETE,
                                            icon_color="#ef4444",
                                            icon_size=18,
                                            tooltip="Eliminar menu",
                                            on_click=lambda e, p=prod: self.delete_product_dialog.abrir(p),
                                        ),
                                    ],
                                    alignment="center",
                                    tight=True,
                                ),
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                        ),
                        padding=10,
                        ink=True,
                        on_click=lambda e, p=prod: self._add_to_cart(p, e),
                        bgcolor="#1e293b",
                        border_radius=10,
                    )
                )
            )
        try:
            self.update()
        except RuntimeError:
            pass

    def _abrir_dialogo_producto(self, e):
        if self.add_product_dialog not in self.main_page.overlay:
            self.main_page.overlay.append(self.add_product_dialog)
        self.add_product_dialog.open = True
        self.main_page.update()

    def _on_product_added(self):
        self.inventario = self.dm.get_inventario()
        self._renderizar_catalogo()

    def _on_product_deleted(self, nombre_eliminado: str):
        self.inventario = self.dm.get_inventario()
        if nombre_eliminado in self.carrito:
            del self.carrito[nombre_eliminado]
            self._update_ticket()
        self._renderizar_catalogo()

    def _add_to_cart(self, prod: str, e):
        self.carrito[prod] = self.carrito.get(prod, 0) + 1
        self._update_ticket()

    def _on_cart_item_change(self, prod: str, nueva_cantidad: int):
        if nueva_cantidad <= 0:
            if prod in self.carrito:
                del self.carrito[prod]
        else:
            self.carrito[prod] = nueva_cantidad
        self._update_ticket()

    def _update_ticket(self):
        self.lista_ticket.controls.clear()
        total = 0
        for prod, cant in list(self.carrito.items()):
            if cant > 0:
                precio = self.inventario[prod]["precio"]
                total += cant * precio
                self.lista_ticket.controls.append(
                    CartItemRow(
                        nombre_prod=prod,
                        precio=precio,
                        cantidad=cant,
                        on_change=self._on_cart_item_change,
                    )
                )
        self.txt_total.value = f"${total:.2f}"
        self.update()

    def _cobrar(self, e):
        """Registra la venta y abre el ticket con QR."""
        total = sum(self.carrito[p] * self.inventario[p]["precio"] for p in self.carrito)
        if total <= 0:
            return

        # 1. Guardar venta en data_manager
        carrito_limpio = {k: v for k, v in self.carrito.items() if v > 0}
        self.dm.registrar_venta(carrito_limpio, total)

        # 2. Obtener el ID de la venta (ultima registrada)
        historial = self.dm.get_historial_hoy()
        venta_id = len(historial)

        # 3. Armar el dict de productos con cantidad y precio para el ticket
        productos_ticket = {
            prod: {
                "cantidad": cant,
                "precio": self.inventario[prod]["precio"],
            }
            for prod, cant in carrito_limpio.items()
        }

        # 4. Limpiar carrito
        self.carrito.clear()
        self.inventario = self.dm.get_inventario()
        self._update_ticket()

        # 5. Mostrar ticket
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
        ticket = TicketDialog(
            page=self.main_page,
            venta_id=venta_id,
            productos=productos_ticket,
            total=total,
            fecha_hora=fecha_hora,
        )
        ticket.mostrar()

    def _deshacer(self, e):
        resultado = self.dm.deshacer_ultima_venta()
        if resultado:
            self.inventario = self.dm.get_inventario()
            snack = ft.SnackBar(
                ft.Text(f"↩ Ultima venta (${resultado['total']:.2f}) deshecha correctamente"),
                bgcolor="#92400e",
            )
        else:
            snack = ft.SnackBar(
                ft.Text("⚠ No hay ventas registradas para deshacer"),
                bgcolor="#475569",
            )
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()
        self.update()

    def _build_layout(self):
        panel_cobro = ft.Container(
            width=430,
            padding=20,
            bgcolor="#1e293b",
            border_radius=10,
            content=ft.Column(
                [
                    ft.Text("ORDEN ACTUAL", size=20, weight="bold"),
                    ft.Divider(),
                    self.lista_ticket,
                    ft.Divider(),
                    ft.Row(
                        [ft.Text("TOTAL", size=20), self.txt_total],
                        alignment="spaceBetween",
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "COBRAR",
                        on_click=self._cobrar,
                        bgcolor="#38bdf8",
                        color="#0f172a",
                        height=60,
                        width=float("inf"),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.Container(height=6),
                    ft.OutlinedButton(
                        "↩ Deshacer ultima venta",
                        on_click=self._deshacer,
                        width=float("inf"),
                        height=44,
                        style=ft.ButtonStyle(
                            color="#f87171",
                            side=ft.BorderSide(color="#f87171", width=1),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
                expand=True,
            ),
        )

        return ft.Row(
            [
                ft.Container(content=self.productos_grid, expand=True, padding=20),
                panel_cobro,
            ],
            expand=True,
        )