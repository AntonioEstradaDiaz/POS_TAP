import flet as ft
from flet.controls.material.icons import Icons


class AddProductDialog(ft.AlertDialog):
    """
    Dialogo modal para agregar un nuevo platillo al sistema.
    """
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success

        # Componentes UI
        self.txt_nombre = ft.TextField(label="Nombre del Platillo", width=300)
        self.txt_precio = ft.TextField(label="Precio", width=300, keyboard_type=ft.KeyboardType.NUMBER)

        self.title = ft.Text("Agregar Nuevo Platillo", weight="bold")
        self.content = ft.Column([self.txt_nombre, self.txt_precio], tight=True)
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            #  Se reemplazo el uso de ft.ElevatedButton por ft.Button en las líneas
            ft.Button("Guardar", on_click=self._guardar, bgcolor="#38bdf8", color="#0f172a")
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _guardar(self, e):
        nombre    = self.txt_nombre.value.strip()
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
    """
    Dialogo modal para confirmar la eliminacion permanente de un platillo del sistema.
    """
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
             #  Se reemplazo el uso de ft.ElevatedButton por ft.Button en las líneas
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.Button("Eliminar Definitivamente", on_click=self._eliminar, bgcolor="#ef4444", color="white")
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
            self.main_page.update() 
            # faltaba self.main_page.update() al final, lo que causaba que el diálogo no se cerrara visualmente tras eliminar un producto aunque internamente self.open = False ya estaba presente.

class CartItemRow(ft.Row):
    """
    Componente visual interactivo que representa un renglon del carrito de compras.
    Encapsula toda la logica de presentacion individual por elemento (Aumentar, Reducir, Borrar).
    """
    def __init__(self, nombre_prod: str, precio: float, cantidad: int, on_change):
        super().__init__(alignment="spaceBetween")
        self.nombre_prod = nombre_prod
        self.precio      = precio
        self.cantidad    = cantidad
        self.on_change   = on_change

        self.info_text   = ft.Text(f"{self.nombre_prod} (${self.precio:.2f})", expand=True)
        self.btn_minus   = ft.IconButton(icon=Icons.REMOVE, icon_color="#f87171",
                                         on_click=self._decrementar, tooltip="Quitar uno")
        self.txt_cantidad = ft.Text(str(self.cantidad), weight="bold", size=16,
                                    text_align="center", width=25)
        self.btn_plus    = ft.IconButton(icon=Icons.ADD, icon_color="#a3e635",
                                         on_click=self._incrementar, tooltip="Agregar uno")
        self.btn_delete  = ft.IconButton(icon=Icons.DELETE, icon_color="#ef4444",
                                         on_click=self._eliminar, tooltip="Remover todo")
        self.subtotal_text = ft.Text(f"${self.cantidad * self.precio:.2f}",
                                     weight="bold", width=60, text_align="right")

        self.controls = [
            self.info_text,
            ft.Row([self.btn_minus, self.txt_cantidad, self.btn_plus], tight=True, spacing=0),
            self.subtotal_text,
            self.btn_delete
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
        """Renderiza los cambios dentro de este propio componente."""
        self.txt_cantidad.value  = str(self.cantidad)
        self.subtotal_text.value = f"${self.cantidad * self.precio:.2f}"
        self.update()


class VentasView(ft.Container):
    """
    Vista principal del Punto de Venta.
    Controla el catalogo de platillos y el flujo de caja (carrito de compras).
    """
    def __init__(self, page, data_manager):
        super().__init__(expand=True)
        self.main_page = page
        self.dm        = data_manager

        # Estado de Datos
        self.carrito   = {}
        self.inventario = self.dm.get_inventario()

        # Elementos UI Globales de la Vista
        self.lista_ticket       = ft.ListView(expand=True, spacing=10)
        self.txt_total          = ft.Text("$0.00", size=32, weight="bold", color="#38bdf8")
        self.productos_grid     = self._create_empty_grid()
        self.add_product_dialog    = AddProductDialog(self.main_page, self.dm, self._on_product_added)
        self.delete_product_dialog = DeleteProductDialog(self.main_page, self.dm, self._on_product_deleted)

        self.content = self._build_layout()
        self._renderizar_catalogo()

    def _create_empty_grid(self) -> ft.GridView:
        """Helper para generar el contenedor flexible del listado de tarjetas."""
        return ft.GridView(expand=True, max_extent=250, child_aspect_ratio=1.2,
                           spacing=15, run_spacing=15)

    def _renderizar_catalogo(self):
        """Dibuja en pantalla todas las tarjetas del grid (Nuevo prod + Inventario actual)."""
        self.productos_grid.controls.clear()

        # Tarjeta Especial: "Agregar Nuevo Platillo"
        self.productos_grid.controls.append(
            ft.Card(content=ft.Container(
                content=ft.Column([
                    ft.Text("Agregar Platillo", weight="bold", size=16),
                    ft.Text("+", color="#a3e635", size=24, weight="bold"),
                ], alignment="center", horizontal_alignment="center"),
                padding=10, ink=True, on_click=self._abrir_dialogo_producto,
                bgcolor="#1e293b", border_radius=10
            ))
        )

        # Tarjetas dinamicas desde el inventario JSON
        for prod, data in self.inventario.items():
            self.productos_grid.controls.append(
                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text(prod, weight="bold", size=16, text_align="center"),
                        ft.Row([
                            ft.Text(f"${data['precio']}", color="#38bdf8", size=18),
                            ft.IconButton(icon=Icons.DELETE, icon_color="#ef4444",
                                          icon_size=18, tooltip="Eliminar menu",
                                          on_click=lambda e, p=prod: self.delete_product_dialog.abrir(p))
                        ], alignment="center", tight=True),
                    ], alignment="center", horizontal_alignment="center"),
                    padding=10, ink=True,
                    on_click=lambda e, p=prod: self._add_to_cart(p, e),
                    bgcolor="#1e293b", border_radius=10
                ))
            )
        try:
            self.update()
        except RuntimeError:
            pass

    def _abrir_dialogo_producto(self, e):
        """Muestra la ventana emergente para registrar un nuevo platillo."""
        if self.add_product_dialog not in self.main_page.overlay:
            self.main_page.overlay.append(self.add_product_dialog)
        self.add_product_dialog.open = True
        self.main_page.update()

    def _on_product_added(self):
        """Callback de AddProductDialog: refresca el catalogo."""
        self.inventario = self.dm.get_inventario()
        self._renderizar_catalogo()

    def _on_product_deleted(self, nombre_eliminado: str):
        """Callback al eliminar un producto. Refresca e invalida el carrito si aplica."""
        self.inventario = self.dm.get_inventario()
        if nombre_eliminado in self.carrito:
            del self.carrito[nombre_eliminado]
            self._update_ticket()
        self._renderizar_catalogo()

    def _add_to_cart(self, prod: str, e):
        """Sube en +1 el producto al carrito."""
        self.carrito[prod] = self.carrito.get(prod, 0) + 1
        self._update_ticket()

    def _on_cart_item_change(self, prod: str, nueva_cantidad: int):
        """Escucha los avisos de CartItemRow sobre cambios de cantidad."""
        if nueva_cantidad <= 0:
            if prod in self.carrito:
                del self.carrito[prod]
        else:
            self.carrito[prod] = nueva_cantidad
        self._update_ticket()

    def _update_ticket(self):
        """Reconstruye la lista del ticket y recalcula el total."""
        self.lista_ticket.controls.clear()
        total = 0

        for prod, cant in list(self.carrito.items()):
            if cant > 0:
                precio = self.inventario[prod]["precio"]
                total += cant * precio
                self.lista_ticket.controls.append(
                    CartItemRow(nombre_prod=prod, precio=precio,
                                cantidad=cant, on_change=self._on_cart_item_change)
                )

        self.txt_total.value = f"${total:.2f}"
        self.update()

    def _cobrar(self, e):
        """Verifica que el carrito no este vacio y guarda la venta."""
        total = sum(self.carrito[p] * self.inventario[p]["precio"] for p in self.carrito)
        if total > 0:
            self.dm.registrar_venta({k: v for k, v in self.carrito.items() if v > 0}, total)
            self.carrito.clear()
            self.inventario = self.dm.get_inventario()
            self._update_ticket()
            snack = ft.SnackBar(ft.Text("✅ Cobro exitoso"), bgcolor="#166534")
            self.main_page.overlay.append(snack)
            snack.open = True
            self.main_page.update()

    def _deshacer(self, e):
        """Deshace la ultima venta usando DataManager."""
        resultado = self.dm.deshacer_ultima_venta()
        if resultado:
            self.inventario = self.dm.get_inventario()
            snack = ft.SnackBar(
                ft.Text(f"↩ Ultima venta (${resultado['total']:.2f}) deshecha correctamente"),
                bgcolor="#92400e"
            )
        else:
            snack = ft.SnackBar(
                ft.Text("⚠ No hay ventas registradas para deshacer"),
                bgcolor="#475569"
            )
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()
        self.update()

    def _build_layout(self):
        """Genera y une las columnas de Productos (Izq) y el Panel de Cobro (Der)."""
        panel_cobro = ft.Container(
            width=430, padding=20, bgcolor="#1e293b", border_radius=10,
            content=ft.Column([
                ft.Text("ORDEN ACTUAL", size=20, weight="bold"),
                ft.Divider(),
                self.lista_ticket,
                ft.Divider(),
                ft.Row([ft.Text("TOTAL", size=20), self.txt_total], alignment="spaceBetween"),
                ft.Container(height=10),
                 #  Se reemplazo el uso de ft.ElevatedButton por ft.Button en las líneas
                ft.Button("COBRAR", on_click=self._cobrar,
                                  bgcolor="#38bdf8", color="#0f172a", height=60,
                                  width=float('inf'),
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
                ft.Container(height=6),
                ft.OutlinedButton("↩ Deshacer ultima venta", on_click=self._deshacer,
                                  width=float('inf'), height=44,
                                  style=ft.ButtonStyle(
                                      color="#f87171",
                                      side=ft.BorderSide(color="#f87171", width=1),
                                      shape=ft.RoundedRectangleBorder(radius=8)
                                  )),
            ], expand=True)
        )

        return ft.Row([
            ft.Container(content=self.productos_grid, expand=True, padding=20),
            panel_cobro
        ], expand=True)
