import flet as ft
from flet.controls.material.icons import Icons


# ---------------------------------------------------------------------------
# Dialogo: Agregar nuevo platillo al catalogo
# ---------------------------------------------------------------------------

class AddProductDialog(ft.AlertDialog):
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm        = data_manager
        self.on_success = on_success

        self.txt_nombre = ft.TextField(label="Nombre del Platillo", width=300)
        self.txt_precio = ft.TextField(label="Precio", width=300,
                                       keyboard_type=ft.KeyboardType.NUMBER)

        self.title   = ft.Text("Agregar Nuevo Platillo", weight="bold")
        self.content = ft.Column([self.txt_nombre, self.txt_precio], tight=True)
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.Button("Guardar", on_click=self._guardar,
                      bgcolor="#38bdf8", color="#0f172a"),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _guardar(self, e):
        nombre    = self.txt_nombre.value.strip()
        precio_str = self.txt_precio.value.strip()

        if not nombre or not precio_str:
            self._snack("⚠ Llena todos los campos", "#92400e")
            return
        try:
            float(precio_str)
        except ValueError:
            self._snack("⚠ El precio debe ser un número válido", "#92400e")
            return

        if self.dm.agregar_producto(nombre, float(precio_str)):
            self.open = False
            self.txt_nombre.value = ""
            self.txt_precio.value = ""
            self._snack(f"✅ Platillo '{nombre}' agregado.", "#166534")
            self.on_success()
        else:
            self._snack("⚠ El platillo ya existe.", "#92400e")

        self.main_page.update()

    def _snack(self, texto, color):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()


# ---------------------------------------------------------------------------
# Dialogo: Eliminar platillo del catalogo
# ---------------------------------------------------------------------------

class DeleteProductDialog(ft.AlertDialog):
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm        = data_manager
        self.on_success = on_success
        self.producto_a_eliminar = None

        self.title      = ft.Text("¿Eliminar Platillo?", weight="bold")
        self.txt_mensaje = ft.Text("")
        self.content    = self.txt_mensaje
        self.actions    = [
            ft.TextButton("Cancelar",  on_click=self._cancelar),
            ft.Button("Eliminar Definitivamente", on_click=self._eliminar,
                      bgcolor="#ef4444", color="white"),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def abrir(self, nombre_prod):
        self.producto_a_eliminar = nombre_prod
        self.txt_mensaje.value = (
            f"Estás a punto de eliminar '{nombre_prod}' permanentemente.\n¿Estás seguro?"
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


# ---------------------------------------------------------------------------
# Dialogo: Crear nueva cuenta (pide nombre)
# ---------------------------------------------------------------------------

class NuevaCuentaDialog(ft.AlertDialog):
    """
    Pide un nombre libre para la nueva cuenta (mesa, cliente, etc.)
    Llama on_confirm(nombre) al aceptar.
    """
    def __init__(self, page, on_confirm):
        super().__init__()
        self.main_page  = page
        self.on_confirm = on_confirm

        self.txt_nombre = ft.TextField(
            label="Nombre de la cuenta",
            hint_text="Ej: Mesa 3, Juan, Mesa VIP…",
            width=300,
            autofocus=True,
        )
        self.title   = ft.Text("Nueva Cuenta", weight="bold")
        self.content = self.txt_nombre
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.Button("Crear", on_click=self._crear,
                      bgcolor="#38bdf8", color="#0f172a"),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def abrir(self):
        self.txt_nombre.value = ""
        self.open = True
        if self not in self.main_page.overlay:
            self.main_page.overlay.append(self)
        self.main_page.update()

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _crear(self, e):
        nombre = self.txt_nombre.value.strip()
        if not nombre:
            return
        self.open = False
        self.main_page.update()
        self.on_confirm(nombre)


# ---------------------------------------------------------------------------
# Fila interactiva de producto en el carrito
# ---------------------------------------------------------------------------

class CartItemRow(ft.Row):
    def __init__(self, nombre_prod, precio, cantidad, on_change):
        super().__init__(alignment="spaceBetween")
        self.nombre_prod = nombre_prod
        self.precio      = precio
        self.cantidad    = cantidad
        self.on_change   = on_change

        self.info_text     = ft.Text(f"{nombre_prod} (${precio:.2f})", expand=True)
        self.btn_minus     = ft.IconButton(icon=Icons.REMOVE, icon_color="#f87171",
                                           on_click=self._decrementar, tooltip="Quitar uno")
        self.txt_cantidad  = ft.Text(str(cantidad), weight="bold", size=16,
                                     text_align="center", width=25)
        self.btn_plus      = ft.IconButton(icon=Icons.ADD, icon_color="#a3e635",
                                           on_click=self._incrementar, tooltip="Agregar uno")
        self.btn_delete    = ft.IconButton(icon=Icons.DELETE, icon_color="#ef4444",
                                           on_click=self._eliminar, tooltip="Remover todo")
        self.subtotal_text = ft.Text(f"${cantidad * precio:.2f}",
                                     weight="bold", width=60, text_align="right")

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
        self.txt_cantidad.value  = str(self.cantidad)
        self.subtotal_text.value = f"${self.cantidad * self.precio:.2f}"
        self.update()


# ---------------------------------------------------------------------------
# CuentaPanel — el carrito completo de UNA cuenta
# ---------------------------------------------------------------------------

class CuentaPanel(ft.Container):
    """
    Encapsula el carrito de una sola cuenta.
    cuenta_id: id de la fila en cuentas_abiertas (para persistir el carrito).
    dm: DataManager para guardar cambios en BD.
    carrito_inicial: dict con el carrito restaurado desde BD (opcional).
    """
    def __init__(self, nombre: str, inventario: dict,
                 on_cobrar, on_deshacer, on_add_producto, on_delete_producto,
                 dm, cuenta_id: int, carrito_inicial: dict = None):
        super().__init__(expand=True)
        self.nombre_cuenta      = nombre
        self.inventario         = inventario
        self.on_cobrar          = on_cobrar
        self.on_deshacer        = on_deshacer
        self.on_add_producto    = on_add_producto
        self.on_delete_producto = on_delete_producto
        self.dm                 = dm
        self.cuenta_id          = cuenta_id

        self.carrito       = carrito_inicial or {}
        self.lista_ticket  = ft.ListView(expand=True, spacing=10)
        self.txt_total     = ft.Text("$0.00", size=32, weight="bold", color="#38bdf8")
        self.productos_grid = self._crear_grid()

        self.content = self._build_layout()
        self._renderizar_catalogo()
        if self.carrito:
            self._update_ticket()

    # ---- Catalogo ----

    def _crear_grid(self):
        return ft.GridView(expand=True, max_extent=250, child_aspect_ratio=1.2,
                           spacing=15, run_spacing=15)

    def refrescar_inventario(self, inventario: dict):
        """Llamado por VentasView cuando cambia el inventario global."""
        self.inventario = inventario
        # Eliminar del carrito productos que ya no existen
        eliminados = [p for p in self.carrito if p not in inventario]
        for p in eliminados:
            del self.carrito[p]
        self._renderizar_catalogo()
        self._update_ticket()

    def _renderizar_catalogo(self):
        self.productos_grid.controls.clear()

        # Tarjeta "Agregar nuevo platillo"
        self.productos_grid.controls.append(
            ft.Card(content=ft.Container(
                content=ft.Column([
                    ft.Text("Agregar Platillo", weight="bold", size=16),
                    ft.Text("+", color="#a3e635", size=24, weight="bold"),
                ], alignment="center", horizontal_alignment="center"),
                padding=10, ink=True,
                on_click=lambda e: self.on_add_producto(),
                bgcolor="#1e293b", border_radius=10,
            ))
        )

        for prod, data in self.inventario.items():
            self.productos_grid.controls.append(
                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text(prod, weight="bold", size=16, text_align="center"),
                        ft.Row([
                            ft.Text(f"${data['precio']}", color="#38bdf8", size=18),
                            ft.IconButton(
                                icon=Icons.DELETE, icon_color="#ef4444",
                                icon_size=18, tooltip="Eliminar del menú",
                                on_click=lambda e, p=prod: self.on_delete_producto(p),
                            ),
                        ], alignment="center", tight=True),
                    ], alignment="center", horizontal_alignment="center"),
                    padding=10, ink=True,
                    on_click=lambda e, p=prod: self._add_to_cart(p),
                    bgcolor="#1e293b", border_radius=10,
                ))
            )
        try:
            self.update()
        except RuntimeError:
            pass

    # ---- Carrito ----

    def _add_to_cart(self, prod: str):
        self.carrito[prod] = self.carrito.get(prod, 0) + 1
        self.dm.actualizar_carrito_cuenta(self.cuenta_id, self.carrito)
        self._update_ticket()

    def _on_cart_item_change(self, prod: str, nueva_cantidad: int):
        if nueva_cantidad <= 0:
            self.carrito.pop(prod, None)
        else:
            self.carrito[prod] = nueva_cantidad
        self.dm.actualizar_carrito_cuenta(self.cuenta_id, self.carrito)
        self._update_ticket()

    def _update_ticket(self):
        self.lista_ticket.controls.clear()
        total = 0
        for prod, cant in list(self.carrito.items()):
            if cant > 0 and prod in self.inventario:
                precio = self.inventario[prod]["precio"]
                total += cant * precio
                self.lista_ticket.controls.append(
                    CartItemRow(nombre_prod=prod, precio=precio,
                                cantidad=cant, on_change=self._on_cart_item_change)
                )
        self.txt_total.value = f"${total:.2f}"
        try:
            self.update()
        except RuntimeError:
            pass

    def get_total(self) -> float:
        return sum(
            self.carrito[p] * self.inventario[p]["precio"]
            for p in self.carrito
            if p in self.inventario
        )

    # ---- Layout ----

    def _build_layout(self):
        panel_cobro = ft.Container(
            width=430, padding=20, bgcolor="#1e293b", border_radius=10,
            content=ft.Column([
                ft.Row([
                    ft.Icon(Icons.RECEIPT_LONG, color="#38bdf8"),
                    ft.Text(f"Cuenta: {self.nombre_cuenta}",
                            size=18, weight="bold", color="#38bdf8"),
                ], spacing=8),
                ft.Divider(),
                self.lista_ticket,
                ft.Divider(),
                ft.Row([ft.Text("TOTAL", size=20), self.txt_total],
                       alignment="spaceBetween"),
                ft.Container(height=10),
                ft.Button(
                    "COBRAR",
                    on_click=lambda e: self.on_cobrar(self),
                    bgcolor="#38bdf8", color="#0f172a", height=60,
                    width=float("inf"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
                ft.Container(height=6),
                ft.OutlinedButton(
                    "↩ Deshacer última venta",
                    on_click=lambda e: self.on_deshacer(),
                    width=float("inf"), height=44,
                    style=ft.ButtonStyle(
                        color="#f87171",
                        side=ft.BorderSide(color="#f87171", width=1),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ], expand=True),
        )

        return ft.Row([
            ft.Container(content=self.productos_grid, expand=True, padding=20),
            panel_cobro,
        ], expand=True)


# ---------------------------------------------------------------------------
# VentasView — vista principal con sistema de tabs por cuenta
# ---------------------------------------------------------------------------

class VentasView(ft.Container):
    """
    Vista principal del Punto de Venta.
    Soporta múltiples cuentas simultáneas, cada una con su propio carrito,
    gestionadas a través de una barra de tabs en la parte superior.
    """

    def __init__(self, page, data_manager):
        super().__init__(expand=True)
        self.main_page = page
        self.dm        = data_manager
        self.inventario = self.dm.get_inventario()

        # Estado de cuentas: list of CuentaPanel
        self.cuentas: list[CuentaPanel] = []
        self.cuenta_activa_idx: int     = -1

        # Diálogos globales
        self.add_product_dialog    = AddProductDialog(
            page, data_manager, self._on_producto_agregado)
        self.delete_product_dialog = DeleteProductDialog(
            page, data_manager, self._on_producto_eliminado)
        self.nueva_cuenta_dialog   = NuevaCuentaDialog(
            page, self._crear_cuenta)

        # Contenedor dinámico
        self._tabs_row    = ft.Row(spacing=0, scroll=ft.ScrollMode.AUTO)
        self._panel_body  = ft.Container(expand=True)
        self._empty_state = self._build_empty_state()

        self.content = ft.Column([
            self._build_tabs_bar(),
            ft.Divider(height=1, color="#334155"),
            self._panel_body,
        ], expand=True, spacing=0)

        # Restaurar cuentas guardadas en BD al iniciar la app
        self._cargar_cuentas_bd()

    # ------------------------------------------------------------------ #
    # Construcción de barra de tabs                                        #
    # ------------------------------------------------------------------ #

    def _build_tabs_bar(self) -> ft.Container:
        """Barra superior: tabs de cuentas abiertas + botón Nueva Cuenta."""
        return ft.Container(
            bgcolor="#0f172a",
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            content=ft.Row([
                self._tabs_row,
                # Botón Nueva Cuenta
                ft.Container(
                    content=ft.Row([
                        ft.Icon(Icons.ADD, size=16, color="#a3e635"),
                        ft.Text("Nueva Cuenta", size=13, color="#a3e635"),
                    ], tight=True, spacing=4),
                    bgcolor="#1e293b",
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=lambda e: self.nueva_cuenta_dialog.abrir(),
                ),
            ], vertical_alignment="center", spacing=8),
        )

    def _build_tab_chip(self, idx: int, nombre: str) -> ft.Container:
        """Genera la pastilla/tab de una cuenta con su botón de cerrar."""
        activo  = idx == self.cuenta_activa_idx
        bg      = "#1e3a5f" if activo else "#1e293b"
        border  = ft.Border.all(1, "#38bdf8") if activo else ft.Border.all(1, "#334155")

        return ft.Container(
            key=f"tab_{idx}",
            content=ft.Row([
                ft.Icon(Icons.RECEIPT, size=14,
                        color="#38bdf8" if activo else "#64748b"),
                ft.Text(nombre, size=13,
                        color="white" if activo else "#94a3b8",
                        weight="bold" if activo else "normal"),
                ft.Container(
                    content=ft.Icon(Icons.CLOSE, size=12, color="#64748b"),
                    on_click=lambda e, i=idx: self._cerrar_cuenta(i),
                    border_radius=6,
                    padding=2,
                    ink=True,
                    tooltip="Cerrar cuenta",
                ),
            ], tight=True, spacing=6),
            bgcolor=bg,
            border=border,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=7),
            ink=True,
            on_click=lambda e, i=idx: self._activar_cuenta(i),
        )

    def _render_tabs(self):
        self._tabs_row.controls.clear()
        for i, cuenta in enumerate(self.cuentas):
            self._tabs_row.controls.append(
                self._build_tab_chip(i, cuenta.nombre_cuenta)
            )
        try:
            self._tabs_row.update()
        except RuntimeError:
            pass

    # ------------------------------------------------------------------ #
    # Panel central                                                        #
    # ------------------------------------------------------------------ #

    def _build_empty_state(self) -> ft.Container:
        return ft.Container(
            expand=True,
            content=ft.Column([
                ft.Icon(Icons.RECEIPT_LONG, size=80, color="#334155"),
                ft.Text("Sin cuentas abiertas", size=22,
                        weight="bold", color="#475569"),
                ft.Text("Presiona '+ Nueva Cuenta' para comenzar.",
                        size=15, color="#334155"),
            ], alignment="center", horizontal_alignment="center",
               spacing=12),
            alignment=ft.Alignment(0, 0),
        )

    def _render_panel(self):
        if self.cuenta_activa_idx < 0 or not self.cuentas:
            self._panel_body.content = self._empty_state
        else:
            self._panel_body.content = self.cuentas[self.cuenta_activa_idx]
        try:
            self._panel_body.update()
        except RuntimeError:
            pass
        self._render_tabs()

    # ------------------------------------------------------------------ #
    # Gestión de cuentas                                                  #
    # ------------------------------------------------------------------ #

    def _cargar_cuentas_bd(self):
        """Al iniciar, restaura todas las cuentas abiertas guardadas en BD."""
        filas = self.dm.get_cuentas_abiertas()
        for fila in filas:
            # Filtrar del carrito productos que ya no existen en el inventario
            carrito = {p: c for p, c in fila["carrito"].items()
                       if p in self.inventario}
            panel = CuentaPanel(
                nombre=fila["nombre"],
                inventario=dict(self.inventario),
                on_cobrar=self._cobrar_cuenta,
                on_deshacer=self._deshacer,
                on_add_producto=self._abrir_dialogo_add_producto,
                on_delete_producto=self._abrir_dialogo_delete_producto,
                dm=self.dm,
                cuenta_id=fila["id"],
                carrito_inicial=carrito,
            )
            self.cuentas.append(panel)

        if self.cuentas:
            self.cuenta_activa_idx = 0
        self._render_panel()

    def _crear_cuenta(self, nombre: str):
        """Crea cuenta en BD, instancia el panel y lo activa."""
        cuenta_id = self.dm.crear_cuenta_abierta(nombre)
        panel = CuentaPanel(
            nombre=nombre,
            inventario=dict(self.inventario),
            on_cobrar=self._cobrar_cuenta,
            on_deshacer=self._deshacer,
            on_add_producto=self._abrir_dialogo_add_producto,
            on_delete_producto=self._abrir_dialogo_delete_producto,
            dm=self.dm,
            cuenta_id=cuenta_id,
        )
        self.cuentas.append(panel)
        self.cuenta_activa_idx = len(self.cuentas) - 1
        self._render_panel()

    def _activar_cuenta(self, idx: int):
        if 0 <= idx < len(self.cuentas):
            self.cuenta_activa_idx = idx
            self._render_panel()

    def _cerrar_cuenta(self, idx: int):
        """Cierra (sin cobrar) la cuenta: la elimina de BD y del estado."""
        if 0 <= idx < len(self.cuentas):
            self.dm.eliminar_cuenta_abierta(self.cuentas[idx].cuenta_id)
            self.cuentas.pop(idx)
            if not self.cuentas:
                self.cuenta_activa_idx = -1
            elif self.cuenta_activa_idx >= len(self.cuentas):
                self.cuenta_activa_idx = len(self.cuentas) - 1
            self._render_panel()

    # ------------------------------------------------------------------ #
    # Acciones de carrito / venta                                          #
    # ------------------------------------------------------------------ #

    def _cobrar_cuenta(self, panel: CuentaPanel):
        """Registra la venta, elimina la cuenta de BD y cierra el tab."""
        total = panel.get_total()
        if total <= 0:
            self._snack("⚠ La cuenta está vacía.", "#475569")
            return

        carrito_limpio = {k: v for k, v in panel.carrito.items() if v > 0}
        self.dm.registrar_venta(carrito_limpio, total)
        self.dm.eliminar_cuenta_abierta(panel.cuenta_id)

        idx = self.cuentas.index(panel)
        self.cuentas.pop(idx)
        if not self.cuentas:
            self.cuenta_activa_idx = -1
        elif self.cuenta_activa_idx >= len(self.cuentas):
            self.cuenta_activa_idx = len(self.cuentas) - 1

        self._render_panel()
        self._snack(f"✅ Cobro de '{panel.nombre_cuenta}' (${total:.2f}) exitoso.", "#166534")

    def _deshacer(self):
        resultado = self.dm.deshacer_ultima_venta()
        if resultado:
            self._snack(
                f"↩ Última venta (${resultado['total']:.2f}) deshecha.", "#92400e")
        else:
            self._snack("⚠ No hay ventas para deshacer.", "#475569")

    # ------------------------------------------------------------------ #
    # Diálogos de inventario                                               #
    # ------------------------------------------------------------------ #

    def _abrir_dialogo_add_producto(self):
        if self.add_product_dialog not in self.main_page.overlay:
            self.main_page.overlay.append(self.add_product_dialog)
        self.add_product_dialog.open = True
        self.main_page.update()

    def _abrir_dialogo_delete_producto(self, nombre: str):
        self.delete_product_dialog.abrir(nombre)

    def _on_producto_agregado(self):
        self.inventario = self.dm.get_inventario()
        self._propagar_inventario()

    def _on_producto_eliminado(self, nombre: str):
        self.inventario = self.dm.get_inventario()
        self._propagar_inventario()

    def _propagar_inventario(self):
        """Actualiza el inventario en todos los CuentaPanel abiertos."""
        for panel in self.cuentas:
            panel.refrescar_inventario(dict(self.inventario))

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

    def _snack(self, texto: str, color: str):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()