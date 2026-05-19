import flet as ft


class AddProductDialog(ft.AlertDialog):
    """
    Dialogo modal para agregar un nuevo platillo al sistema.
    """
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success

        self.txt_nombre = ft.TextField(label="Nombre del Platillo", width=300)
        self.txt_precio = ft.TextField(
            label="Precio", width=300, keyboard_type=ft.KeyboardType.NUMBER
        )
        self.dd_categoria = ft.Dropdown(
            label="Categoría",
            width=300,
            value="comida",
            options=[
                ft.dropdown.Option("comida",  "🍽 Comida"),
                ft.dropdown.Option("bebida",  "🥤 Bebida"),
                ft.dropdown.Option("postre",  "🍮 Postre"),
            ]
        )

        self.title = ft.Text("Agregar Nuevo Platillo", weight="bold")
        self.content = ft.Column(
            [self.txt_nombre, self.txt_precio, self.dd_categoria], tight=True
        )
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.Button(
                "Guardar",
                on_click=self._guardar,
                style=ft.ButtonStyle(bgcolor="#38bdf8", color="#0f172a")
            ),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _guardar(self, e):
        nombre     = self.txt_nombre.value.strip()
        precio_str = self.txt_precio.value.strip()
        categoria  = self.dd_categoria.value or "comida"

        if not nombre or not precio_str:
            self._mostrar_snackbar("⚠ Llena todos los campos", "#92400e")
            return
        try:
            precio = float(precio_str)
        except ValueError:
            self._mostrar_snackbar("⚠ El precio debe ser un numero valido", "#92400e")
            return

        agregado = self.dm.agregar_producto(nombre, precio, categoria=categoria)
        if agregado:
            self.open = False
            self.txt_nombre.value = ""
            self.txt_precio.value = ""
            self._mostrar_snackbar(f"✅ '{nombre}' agregado exitosamente.", "#166534")
            self.on_success()
        else:
            self._mostrar_snackbar("⚠ El platillo ya existe.", "#92400e")
        self.main_page.update()

    def _mostrar_snackbar(self, texto, color):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()


class DeleteProductDialog(ft.AlertDialog):
    """
    Dialogo modal para confirmar la eliminacion permanente de un platillo.
    """
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success
        self.producto_a_eliminar = None

        self.title = ft.Text("¿Eliminar Platillo?", weight="bold")
        self.txt_mensaje = ft.Text("")
        self.content = self.txt_mensaje
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.Button(
                "Eliminar Definitivamente",
                on_click=self._eliminar,
                style=ft.ButtonStyle(bgcolor="#ef4444", color="white")
            ),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def abrir(self, nombre_prod):
        self.producto_a_eliminar = nombre_prod
        self.txt_mensaje.value = (
            f"Estas a punto de eliminar '{nombre_prod}' permanentemente.\n"
            "¿Estas seguro?"
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


class CartItemRow(ft.Row):
    """
    Renglon interactivo del carrito de compras.
    """
    def __init__(self, nombre_prod: str, precio: float, cantidad: int, on_change):
        super().__init__(alignment="spaceBetween")
        self.nombre_prod = nombre_prod
        self.precio      = precio
        self.cantidad    = cantidad
        self.on_change   = on_change

        self.info_text    = ft.Text(f"{self.nombre_prod} (${self.precio:.2f})", expand=True)
        self.btn_minus    = ft.IconButton(
            icon=ft.Icons.REMOVE, icon_color="#f87171",
            on_click=self._decrementar, tooltip="Quitar uno"
        )
        self.txt_cantidad = ft.Text(
            str(self.cantidad), weight="bold", size=16,
            text_align="center", width=25
        )
        self.btn_plus     = ft.IconButton(
            icon=ft.Icons.ADD, icon_color="#a3e635",
            on_click=self._incrementar, tooltip="Agregar uno"
        )
        self.btn_delete   = ft.IconButton(
            icon=ft.Icons.DELETE, icon_color="#ef4444",
            on_click=self._eliminar, tooltip="Remover todo"
        )
        self.subtotal_text = ft.Text(
            f"${self.cantidad * self.precio:.2f}",
            weight="bold", width=60, text_align="right"
        )

        self.controls = [
            self.info_text,
            ft.Row([self.btn_minus, self.txt_cantidad, self.btn_plus],
                   tight=True, spacing=0),
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
        self.txt_cantidad.value  = str(self.cantidad)
        self.subtotal_text.value = f"${self.cantidad * self.precio:.2f}"
        self.update()


class VentasView(ft.Container):
    """
    Vista principal del Punto de Venta.
    Recibe es_admin para mostrar u ocultar controles de gestion.
    """
    def __init__(self, page, data_manager, es_admin: bool = False):
        super().__init__(expand=True)
        self.main_page = page
        self.dm        = data_manager
        self.es_admin  = es_admin

        # Estado
        self.carrito    = {}
        self.inventario = self.dm.get_inventario()
        self.categoria_activa = "todos"  # todos | comida | bebida | postre
        self.filtro_texto     = ""

        # UI global
        self.lista_ticket = ft.ListView(expand=True, spacing=10)
        self.txt_total    = ft.Text("$0.00", size=32, weight="bold", color="#38bdf8")
        self.productos_grid = self._create_empty_grid()

        self.add_product_dialog    = AddProductDialog(self.main_page, self.dm, self._on_product_added)
        self.delete_product_dialog = DeleteProductDialog(self.main_page, self.dm, self._on_product_deleted)

        self.content = self._build_layout()
        self._renderizar_catalogo()

    # ------------------------------------------------------------------
    # Grid helpers
    # ------------------------------------------------------------------
    def _create_empty_grid(self) -> ft.GridView:
        return ft.GridView(
            expand=True, max_extent=200,
            child_aspect_ratio=1.1,
            spacing=12, run_spacing=12
        )

    def _card_producto(self, prod, data):
        """Tarjeta de un producto del catalogo."""
        controles = [
            ft.Text(prod, weight="bold", size=14,
                    text_align="center", max_lines=2),
            ft.Text(f"${data['precio']:.2f}", color="#38bdf8", size=16),
        ]
        # Boton eliminar solo para admin
        if self.es_admin:
            controles.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE, icon_color="#ef4444",
                    icon_size=16, tooltip="Eliminar",
                    on_click=lambda e, p=prod: self.delete_product_dialog.abrir(p)
                )
            )
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controles,
                    alignment="center",
                    horizontal_alignment="center",
                    spacing=4,
                ),
                padding=10, ink=True,
                on_click=lambda e, p=prod: self._add_to_cart(p, e),
                bgcolor="#1e293b", border_radius=10,
            )
        )

    def _renderizar_catalogo(self):
        """Filtra por categoría y texto, luego dibuja las tarjetas."""
        self.productos_grid.controls.clear()

        # Tarjeta "Agregar" solo para admin
        if self.es_admin:
            self.productos_grid.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Agregar", weight="bold", size=14),
                            ft.Text("+", color="#a3e635", size=24, weight="bold"),
                        ], alignment="center", horizontal_alignment="center"),
                        padding=10, ink=True,
                        on_click=self._abrir_dialogo_producto,
                        bgcolor="#1e293b", border_radius=10,
                    )
                )
            )

        # Filtrar inventario
        for prod, data in self.inventario.items():
            cat = data.get("categoria", "comida")
            # Filtro de categoría
            if self.categoria_activa != "todos" and cat != self.categoria_activa:
                continue
            # Filtro de texto
            if self.filtro_texto and self.filtro_texto not in prod.lower():
                continue
            self.productos_grid.controls.append(self._card_producto(prod, data))

        try:
            self.update()
        except RuntimeError:
            pass

    # ------------------------------------------------------------------
    # Barra de busqueda y tabs de categoria
    # ------------------------------------------------------------------
    def _on_buscar(self, e):
        self.filtro_texto = e.control.value.lower().strip()
        self._renderizar_catalogo()

    def _on_categoria(self, e):
        # Los botones de categoria envian su valor por data
        self.categoria_activa = e.control.data
        # Resaltar boton activo
        for btn in self._categoria_btns:
            btn.style = self._btn_style(btn.data == self.categoria_activa)
        self._renderizar_catalogo()

    def _btn_style(self, activo: bool) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            bgcolor="#38bdf8" if activo else "#1e293b",
            color="#0f172a"   if activo else "white",
            shape=ft.RoundedRectangleBorder(radius=8),
        )

    def _build_filtros(self) -> ft.Column:
        """Buscador + botones de categoría."""
        buscador = ft.TextField(
            hint_text="🔍 Buscar platillo...",
            border_color="#334155",
            focused_border_color="#38bdf8",
            bgcolor="#1e293b",
            color="white",
            on_change=self._on_buscar,
            expand=True,
            height=42,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=6),
        )

        categorias = [
            ("todos",  "Todos"),
            ("comida", "🍽 Comida"),
            ("bebida", "🥤 Bebida"),
            ("postre", "🍮 Postre"),
        ]
        self._categoria_btns = []
        for valor, label in categorias:
            btn = ft.ElevatedButton(
                label,
                data=valor,
                on_click=self._on_categoria,
                style=self._btn_style(valor == self.categoria_activa),
                height=38,
            )
            self._categoria_btns.append(btn)

        return ft.Column([
            buscador,
            ft.Row(self._categoria_btns, spacing=8),
        ], spacing=8)

    # ------------------------------------------------------------------
    # Dialogo callbacks
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Carrito
    # ------------------------------------------------------------------
    def _add_to_cart(self, prod: str, e):
        self.carrito[prod] = self.carrito.get(prod, 0) + 1
        self._update_ticket()

    def _on_cart_item_change(self, prod: str, nueva_cantidad: int):
        if nueva_cantidad <= 0:
            self.carrito.pop(prod, None)
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
                        nombre_prod=prod, precio=precio,
                        cantidad=cant, on_change=self._on_cart_item_change
                    )
                )
        self.txt_total.value = f"${total:.2f}"
        self.update()

    def _cobrar(self, e):
        total = sum(self.carrito[p] * self.inventario[p]["precio"] for p in self.carrito)
        if total > 0:
            self.dm.registrar_venta(
                {k: v for k, v in self.carrito.items() if v > 0}, total
            )
            self.carrito.clear()
            self.inventario = self.dm.get_inventario()
            self._update_ticket()
            snack = ft.SnackBar(ft.Text("✅ Cobro exitoso"), bgcolor="#166534")
            self.main_page.overlay.append(snack)
            snack.open = True
            self.main_page.update()

    def _deshacer(self, e):
        resultado = self.dm.deshacer_ultima_venta()
        if resultado:
            self.inventario = self.dm.get_inventario()
            snack = ft.SnackBar(
                ft.Text(f"↩ Ultima venta (${resultado['total']:.2f}) deshecha"),
                bgcolor="#92400e"
            )
        else:
            snack = ft.SnackBar(
                ft.Text("⚠ No hay ventas para deshacer"),
                bgcolor="#475569"
            )
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()
        self.update()

    # ------------------------------------------------------------------
    # Layout principal
    # ------------------------------------------------------------------
    def _build_layout(self):
        panel_cobro = ft.Container(
            width=430, padding=20, bgcolor="#1e293b", border_radius=10,
            content=ft.Column([
                ft.Text("ORDEN ACTUAL", size=20, weight="bold"),
                ft.Divider(),
                self.lista_ticket,
                ft.Divider(),
                ft.Row(
                    [ft.Text("TOTAL", size=20), self.txt_total],
                    alignment="spaceBetween"
                ),
                ft.Container(height=10),
                ft.Button(
                    "COBRAR", on_click=self._cobrar,
                    style=ft.ButtonStyle(
                        bgcolor="#38bdf8", color="#0f172a",
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    height=60, width=float('inf'),
                ),
                ft.Container(height=6),
                ft.OutlinedButton(
                    "↩ Deshacer ultima venta", on_click=self._deshacer,
                    width=float('inf'), height=44,
                    style=ft.ButtonStyle(
                        color="#f87171",
                        side=ft.BorderSide(color="#f87171", width=1),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    )
                ),
            ], expand=True)
        )

        catalogo = ft.Container(
            expand=True, padding=20,
            content=ft.Column([
                self._build_filtros(),
                ft.Container(height=8),
                self.productos_grid,
            ], expand=True, spacing=0)
        )

        return ft.Row([catalogo, panel_cobro], expand=True)