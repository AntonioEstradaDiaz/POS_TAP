import flet as ft
from flet.controls.material.icons import Icons


class AddProductDialog(ft.AlertDialog):

    def __init__(self, page, data_manager, on_success):
        super().__init__()

        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success

        self.bgcolor = "#0f172a"

        self.txt_nombre = ft.TextField(
            label="Nombre del Platillo",
            width=300,
            border_color="#38bdf8",
        )

        self.txt_precio = ft.TextField(
            label="Precio",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8",
        )

        self.title = ft.Text(
            "Agregar Nuevo Platillo",
            color="white",
            weight="bold"
        )

        self.content = ft.Column([
            self.txt_nombre,
            self.txt_precio
        ], tight=True)

        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),

            ft.ElevatedButton(
                "Guardar",
                on_click=self._guardar,
                bgcolor="#38bdf8",
                color="#0f172a"
            )
        ]

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _guardar(self, e):

        nombre = self.txt_nombre.value.strip()
        precio_str = self.txt_precio.value.strip()

        if not nombre or not precio_str:
            self._snack("⚠ Llena todos los campos", "#92400e")
            return

        try:
            precio = float(precio_str)

        except:
            self._snack("⚠ Precio inválido", "#92400e")
            return

        agregado = self.dm.agregar_producto(nombre, precio)

        if agregado:

            self.open = False

            self.txt_nombre.value = ""
            self.txt_precio.value = ""

            self._snack(
                f"✅ '{nombre}' agregado",
                "#166534"
            )

            self.on_success()

        else:
            self._snack(
                "⚠ Ese producto ya existe",
                "#92400e"
            )

        self.main_page.update()

    def _snack(self, texto, color):

        snack = ft.SnackBar(
            ft.Text(texto),
            bgcolor=color
        )

        self.main_page.overlay.append(snack)

        snack.open = True

        self.main_page.update()


class DeleteProductDialog(ft.AlertDialog):

    def __init__(self, page, data_manager, on_success):
        super().__init__()

        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success

        self.bgcolor = "#0f172a"

        self.producto_a_eliminar = None

        self.title = ft.Text(
            "Eliminar Platillo",
            color="white",
            weight="bold"
        )

        self.txt_mensaje = ft.Text(color="white")

        self.content = self.txt_mensaje

        self.actions = [

            ft.TextButton(
                "Cancelar",
                on_click=self._cancelar
            ),

            ft.ElevatedButton(
                "Eliminar",
                on_click=self._eliminar,
                bgcolor="#ef4444",
                color="white"
            )
        ]

    def abrir(self, nombre_prod):

        self.producto_a_eliminar = nombre_prod

        self.txt_mensaje.value = (
            f"¿Eliminar '{nombre_prod}'?"
        )

        if self not in self.main_page.overlay:
            self.main_page.overlay.append(self)

        self.open = True

        self.main_page.update()

    def _cancelar(self, e):

        self.open = False
        self.main_page.update()

    def _eliminar(self, e):

        if self.producto_a_eliminar:

            self.dm.eliminar_producto(
                self.producto_a_eliminar
            )

            self.open = False

            self.on_success(
                self.producto_a_eliminar
            )

            self.main_page.update()


class CartItemRow(ft.Container):

    def __init__(
        self,
        nombre_prod,
        precio,
        cantidad,
        on_change
    ):

        super().__init__()

        self.nombre_prod = nombre_prod
        self.precio = precio
        self.cantidad = cantidad
        self.on_change = on_change

        self.bgcolor = "#1e293b"

        self.padding = 10

        self.border_radius = 12

        self.txt_cantidad = ft.Text(
            str(self.cantidad),
            color="white",
            weight="bold",
            width=20,
            text_align="center"
        )

        self.subtotal = ft.Text(
            f"${self.precio * self.cantidad:.2f}",
            color="#38bdf8",
            weight="bold"
        )

        self.content = ft.Row([

            ft.Column([

                ft.Text(
                    self.nombre_prod,
                    color="white",
                    weight="bold"
                ),

                ft.Text(
                    f"${self.precio:.2f}",
                    color="#94a3b8",
                    size=12
                )

            ],
            spacing=2,
            expand=True),

            ft.Row([

                ft.IconButton(
                    icon=Icons.REMOVE,
                    icon_color="#f87171",
                    on_click=self._menos
                ),

                self.txt_cantidad,

                ft.IconButton(
                    icon=Icons.ADD,
                    icon_color="#4ade80",
                    on_click=self._mas
                )

            ], spacing=0),

            self.subtotal,

            ft.IconButton(
                icon=Icons.DELETE,
                icon_color="#ef4444",
                on_click=self._eliminar
            )

        ])

    def _menos(self, e):

        if self.cantidad > 1:

            self.cantidad -= 1

            self._actualizar()

            self.on_change(
                self.nombre_prod,
                self.cantidad
            )

        else:
            self._eliminar(e)

    def _mas(self, e):

        self.cantidad += 1

        self._actualizar()

        self.on_change(
            self.nombre_prod,
            self.cantidad
        )

    def _eliminar(self, e):

        self.on_change(
            self.nombre_prod,
            0
        )

    def _actualizar(self):

        self.txt_cantidad.value = str(
            self.cantidad
        )

        self.subtotal.value = (
            f"${self.precio * self.cantidad:.2f}"
        )

        self.update()


class VentasView(ft.Container):

    def __init__(self, page, data_manager):

        super().__init__(expand=True)

        self.main_page = page
        self.dm = data_manager

        self.carrito = {}

        self.inventario = (
            self.dm.get_inventario()
        )

        self.lista_ticket = ft.ListView(
            expand=True,
            spacing=10
        )

        self.txt_total = ft.Text(
            "$0.00",
            size=32,
            weight="bold",
            color="#38bdf8"
        )

        self.productos_grid = ft.GridView(
            expand=True,
            max_extent=250,
            child_aspect_ratio=1.2,
            spacing=15,
            run_spacing=15
        )

        self.add_product_dialog = AddProductDialog(
            self.main_page,
            self.dm,
            self._on_product_added
        )

        self.delete_product_dialog = DeleteProductDialog(
            self.main_page,
            self.dm,
            self._on_product_deleted
        )

        self.content = self._build_layout()

        self._renderizar_catalogo()

    def _renderizar_catalogo(self):

        self.productos_grid.controls.clear()

        self.productos_grid.controls.append(

            ft.Card(

                bgcolor="#1e293b",

                content=ft.Container(

                    padding=15,

                    border_radius=12,

                    ink=True,

                    on_click=self._abrir_dialogo_producto,

                    content=ft.Column([

                        ft.Icon(
                            Icons.ADD_CIRCLE,
                            size=50,
                            color="#4ade80"
                        ),

                        ft.Text(
                            "Agregar Platillo",
                            color="white",
                            weight="bold"
                        )

                    ],
                    alignment="center",
                    horizontal_alignment="center")
                )
            )
        )
        # ==============================
# TOP PRODUCTOS
# ==============================

        kpis = self.dm.get_kpis_y_graficos()
        top_productos = list(kpis["top_productos"].keys())

        top1 = top_productos[0] if len(top_productos) > 0 else None
        top2 = top_productos[1] if len(top_productos) > 1 else None
        top3 = top_productos[2] if len(top_productos) > 2 else None
        for prod, data in self.inventario.items():

            # =========================
            # ESTILOS TOP
            # =========================

            card_color = "#1e293b"
            border_color = "#334155"
            badge = None

            if prod == top1:
                card_color = "#3b2f0b"
                border_color = "#FFD700"

                badge = ft.Container(
                    content=ft.Text(
                        "TOP #1",
                        size=10,
                        weight="bold",
                        color="black"
                    ),
                    bgcolor="#FFD700",
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=20
                )

            elif prod == top2:
                card_color = "#374151"
                border_color = "#c0c0c0"

                badge = ft.Container(
                    content=ft.Text(
                        "TOP #2",
                        size=10,
                        weight="bold",
                        color="black"
                    ),
                    bgcolor="#c0c0c0",
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=20
                )

            elif prod == top3:
                card_color = "#3f2a1d"
                border_color = "#cd7f32"

                badge = ft.Container(
                    content=ft.Text(
                        "TOP #3",
                        size=10,
                        weight="bold",
                        color="white"
                    ),
                    bgcolor="#cd7f32",
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=20
                )

            # =========================
            # TARJETA
            # =========================

            self.productos_grid.controls.append(

                ft.Card(

                    content=ft.Container(

                        padding=15,

                        bgcolor=card_color,

                        border_radius=15,

                        border=ft.border.all(2, border_color),

                        ink=True,

                        on_click=lambda e, p=prod: self._add_to_cart(p, e),

                        content=ft.Column([

                            ft.Row([
                                badge if badge else ft.Container()
                            ], alignment="end"),

                            ft.Container(height=5),

                            ft.Text(
                                prod,
                                size=18,
                                weight="bold",
                                color="white",
                                text_align="center"
                            ),

                            ft.Container(height=10),

                            ft.Text(
                                f"${data['precio']:.2f}",
                                size=24,
                                weight="bold",
                                color="#38bdf8"
                            ),

                            ft.Container(height=8),

                            ft.Text(
                                f"Stock: {data['stock']}",
                                size=12,
                                color="#94a3b8"
                            )

                        ],

                        alignment="center",

                        horizontal_alignment="center")
                    )
                )
            )
        try:
            self.update()
        except:
            pass
    def _abrir_dialogo_producto(self, e):

        if self.add_product_dialog not in self.main_page.overlay:
            self.main_page.overlay.append(
                self.add_product_dialog
            )

        self.add_product_dialog.open = True

        self.main_page.update()

    def _on_product_added(self):

        self.inventario = (
            self.dm.get_inventario()
        )

        self._renderizar_catalogo()

    def _on_product_deleted(self, nombre):

        self.inventario = (
            self.dm.get_inventario()
        )

        if nombre in self.carrito:
            del self.carrito[nombre]

        self._update_ticket()

        self._renderizar_catalogo()

    def _add_to_cart(self, prod, e=None):
        """Agrega un producto al carrito."""
        
        self.carrito[prod] = self.carrito.get(prod, 0) + 1

        self._update_ticket()

    def _on_cart_item_change(
        self,
        prod,
        cantidad
    ):

        if cantidad <= 0:

            if prod in self.carrito:
                del self.carrito[prod]

        else:
            self.carrito[prod] = cantidad

        self._update_ticket()

    def _update_ticket(self):

        self.lista_ticket.controls.clear()

        total = 0

        for prod, cant in self.carrito.items():

            precio = self.inventario[prod]["precio"]

            total += precio * cant

            self.lista_ticket.controls.append(

                CartItemRow(
                    prod,
                    precio,
                    cant,
                    self._on_cart_item_change
                )
            )

        self.txt_total.value = (
            f"${total:.2f}"
        )

        try:
            self.update()
        except:
            pass
    def _cobrar(self, e):

        total = sum(
            self.carrito[p] *
            self.inventario[p]["precio"]
            for p in self.carrito
        )

        if total <= 0:
            return

        self.dm.registrar_venta(
            self.carrito,
            total
        )

        self.carrito.clear()

        self.inventario = (
            self.dm.get_inventario()
        )

        self._update_ticket()

        self._renderizar_catalogo()

        snack = ft.SnackBar(
            ft.Text("✅ Cobro exitoso"),
            bgcolor="#166534"
        )

        self.main_page.overlay.append(snack)

        snack.open = True

        self.main_page.update()

    def _deshacer(self, e):

        resultado = (
            self.dm.deshacer_ultima_venta()
        )

        if resultado:

            mensaje = (
                f"↩ Venta ${resultado['total']:.2f} deshecha"
            )

            color = "#92400e"

        else:

            mensaje = "⚠ No hay ventas"

            color = "#475569"

        self.inventario = (
            self.dm.get_inventario()
        )

        self._renderizar_catalogo()

        snack = ft.SnackBar(
            ft.Text(mensaje),
            bgcolor=color
        )

        self.main_page.overlay.append(snack)

        snack.open = True

        try:
            self.update()
        except:
            pass

    def _build_layout(self):

        panel_cobro = ft.Container(

            width=430,

            padding=20,

            bgcolor="#0f172a",

            border_radius=16,

            border=ft.border.all(
                1,
                "#334155"
            ),

            content=ft.Column([

                ft.Text(
                    "ORDEN ACTUAL",
                    size=22,
                    weight="bold",
                    color="white"
                ),

                ft.Divider(
                    color="#334155"
                ),

                self.lista_ticket,

                ft.Divider(
                    color="#334155"
                ),

                ft.Row([

                    ft.Text(
                        "TOTAL",
                        size=22,
                        weight="bold",
                        color="white"
                    ),

                    self.txt_total

                ],
                alignment="spaceBetween"),

                ft.Container(height=10),

                ft.ElevatedButton(

                    "COBRAR",

                    on_click=self._cobrar,

                    bgcolor="#38bdf8",

                    color="#0f172a",

                    width=float("inf"),

                    height=60,

                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(
                            radius=12
                        )
                    )
                ),

                ft.Container(height=8),

                ft.OutlinedButton(

                    "↩ Deshacer ultima venta",

                    on_click=self._deshacer,

                    width=float("inf"),

                    height=45,

                    style=ft.ButtonStyle(

                        color="#f87171",

                        side=ft.BorderSide(
                            1,
                            "#f87171"
                        ),

                        shape=ft.RoundedRectangleBorder(
                            radius=12
                        )
                    )
                )

            ],
            expand=True)
        )

        return ft.Container(

            expand=True,

            bgcolor="#020617",

            padding=20,

            content=ft.Row([

                ft.Container(
                    content=self.productos_grid,
                    expand=True
                ),

                panel_cobro

            ],
            expand=True)
        )
