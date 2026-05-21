import flet as ft
from flet.controls.material.icons import Icons
import os
import shutil
import tkinter as tk
from tkinter import filedialog


class AddProductDialog(ft.AlertDialog):
    """
    Diálogo modal dinámico para agregar un platillo al sistema.
    Filtra automáticamente las opciones existentes y utiliza Tkinter 
    para la selección nativa de imágenes.
    """
    def __init__(self, page, data_manager, on_success):
        super().__init__()
        self.main_page = page
        self.dm = data_manager
        self.on_success = on_success
        
        self.ruta_imagen_seleccionada = None

        self.platillos_disponibles = {
            "Mole Poblano": {"precio": 45.00, "imagen": "mole_poblano.jpg"},
            "Enchiladas Verdes": {"precio": 35.00, "imagen": "enchiladas_verdes.jpg"},
            "Chilaquiles Rojos": {"precio": 30.00, "imagen": "chilaquiles_rojos.jpg"},
            "Tacos al Pastor": {"precio": 15.00, "imagen": None},
            "Quesadilla Sencilla": {"precio": 20.00, "imagen": None},
            "Agua de Jamaica": {"precio": 15.00, "imagen": None}
        }

        self.radio_modo = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="existente", label="Catálogo Maestro"),
                ft.Radio(value="nuevo", label="Platillo No Registrado")
            ], alignment="center", spacing=20),
            value="existente",
            on_change=self._cambiar_modo
        )

        self.dropdown_nombre = ft.Dropdown(
            label="Selecciona el Platillo",
            width=300,
            border_color="#38bdf8"
        )
        self.dropdown_nombre.on_change = self._al_seleccionar_platillo

        self.txt_nombre_nuevo = ft.TextField(
            label="Nombre del Platillo Nuevo", 
            width=300, 
            border_color="#38bdf8",
            visible=False
        )

        self.txt_precio = ft.TextField(
            label="Precio ($)", 
            width=300, 
            keyboard_type=ft.KeyboardType.NUMBER
        )

        self.btn_adjuntar_imagen = ft.ElevatedButton(
            "Adjuntar Imagen", 
            icon=Icons.IMAGE, 
            bgcolor="#334155",
            color="white",
            visible=False,
            on_click=self._al_seleccionar_archivo
        )
        
        self.lbl_imagen_status = ft.Text(
            "No se ha seleccionado imagen", 
            size=12, 
            color="#94a3b8", 
            visible=False
        )

        self.title = ft.Text("Gestionar Menú", weight="bold")
        self.content = ft.Column([
            self.radio_modo,
            ft.Divider(color="#334155"),
            self.dropdown_nombre,
            self.txt_nombre_nuevo,
            ft.Container(height=5),
            self.txt_precio,
            ft.Container(height=5),
            self.btn_adjuntar_imagen,
            self.lbl_imagen_status
        ], tight=True, spacing=10)

        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.ElevatedButton("Guardar", on_click=self._guardar, bgcolor="#38bdf8", color="#0f172a")
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def actualizar_opciones(self, inventario_actual):
        self.dropdown_nombre.options = [
            ft.dropdown.Option(platillo)
            for platillo in self.platillos_disponibles.keys()
            if platillo not in inventario_actual
        ]

    def _cambiar_modo(self, e):
        es_existente = self.radio_modo.value == "existente"
        
        self.dropdown_nombre.visible = es_existente
        self.txt_nombre_nuevo.visible = not es_existente
        self.btn_adjuntar_imagen.visible = not es_existente
        self.lbl_imagen_status.visible = not es_existente
        
        self.dropdown_nombre.value = None
        self.txt_nombre_nuevo.value = ""
        self.txt_precio.value = ""
        self.ruta_imagen_seleccionada = None
        self.lbl_imagen_status.value = "No se ha seleccionado imagen"
        self.lbl_imagen_status.color = "#94a3b8"
        
        self.main_page.update()

    def _al_seleccionar_platillo(self, e):
        nombre_seleccionado = self.dropdown_nombre.value
        if nombre_seleccionado in self.platillos_disponibles:
            precio_sugerido = self.platillos_disponibles[nombre_seleccionado]["precio"]
            self.txt_precio.value = str(precio_sugerido)
            self.main_page.update()

    def _al_seleccionar_archivo(self, e):
        """Abre el explorador nativo usando Tkinter."""
        root = tk.Tk()
        root.attributes('-topmost', True) # Asegura que la ventana se abra por encima de la aplicación
        root.withdraw() # Oculta la ventana principal de Tkinter
        
        ruta = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[("Archivos de Imagen", "*.png *.jpg *.jpeg")]
        )
        root.destroy()
        
        if ruta:
            self.ruta_imagen_seleccionada = ruta
            nombre_archivo = os.path.basename(ruta)
            self.lbl_imagen_status.value = f"✔ Cargada: {nombre_archivo}"
            self.lbl_imagen_status.color = "#4ade80"
            self.main_page.update()

    def _cancelar(self, e):
        self.open = False
        self.main_page.update()

    def _guardar(self, e):
        if self.radio_modo.value == "existente":
            nombre = self.dropdown_nombre.value
            imagen_final = self.platillos_disponibles[nombre]["imagen"] if nombre in self.platillos_disponibles else None
        else:
            nombre = self.txt_nombre_nuevo.value.strip()
            imagen_final = None

        precio_str = self.txt_precio.value.strip()

        if not nombre or not precio_str:
            self._mostrar_snackbar("⚠ Complete todos los campos requeridos", "#92400e")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            self._mostrar_snackbar("⚠ El precio debe ser un número válido", "#92400e")
            return

        if self.radio_modo.value == "nuevo":
            if self.ruta_imagen_seleccionada:
                try:
                    _, ext = os.path.splitext(self.ruta_imagen_seleccionada)
                    nombre_archivo = f"{nombre.lower().replace(' ', '_')}{ext}"
                    
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    dir_assets = os.path.join(base_dir, "..", "assets")
                    os.makedirs(dir_assets, exist_ok=True)
                    ruta_destino = os.path.join(dir_assets, nombre_archivo)
                    
                    shutil.copy(self.ruta_imagen_seleccionada, ruta_destino)
                    imagen_final = nombre_archivo
                except Exception as ex:
                    self._mostrar_snackbar(f"⚠ Error al procesar imagen: {ex}", "#92400e")
                    return

            self.platillos_disponibles[nombre] = {"precio": precio, "imagen": imagen_final}

        agregado = self.dm.agregar_producto(nombre, precio, imagen_final)
        if agregado:
            self.open = False
            self.dropdown_nombre.value = None
            self.txt_nombre_nuevo.value = ""
            self.txt_precio.value = ""
            self.ruta_imagen_seleccionada = None
            self._mostrar_snackbar(f"✅ '{nombre}' registrado exitosamente.", "#166534")
            self.on_success()
        else:
            self._mostrar_snackbar("⚠ El platillo ya se encuentra registrado en el menú.", "#92400e")

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

        self.title = ft.Text("¿Eliminar Platillo?", weight="bold")
        self.txt_mensaje = ft.Text("")
        self.content = self.txt_mensaje
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.ElevatedButton("Eliminar Definitivamente", on_click=self._eliminar, bgcolor="#ef4444", color="white")
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def abrir(self, nombre_prod):
        self.producto_a_eliminar = nombre_prod
        self.txt_mensaje.value = (
            f"Estás a punto de eliminar '{nombre_prod}' permanentemente de tu catálogo.\n"
            "¿Estás seguro?"
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
        self.txt_cantidad.value  = str(self.cantidad)
        self.subtotal_text.value = f"${self.cantidad * self.precio:.2f}"
        self.update()


class VentasView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True)
        self.main_page = page
        self.dm        = data_manager

        self.carrito   = {}
        self.inventario = self.dm.get_inventario()

        self.lista_ticket       = ft.ListView(expand=True, spacing=10)
        self.txt_total          = ft.Text("$0.00", size=32, weight="bold", color="#38bdf8")
        self.productos_grid     = self._create_empty_grid()
        self.add_product_dialog    = AddProductDialog(self.main_page, self.dm, self._on_product_added)
        self.delete_product_dialog = DeleteProductDialog(self.main_page, self.dm, self._on_product_deleted)

        self.content = self._build_layout()
        self._renderizar_catalogo()

    def _create_empty_grid(self) -> ft.GridView:
        return ft.GridView(expand=True, max_extent=250, child_aspect_ratio=1.1,
                           spacing=15, run_spacing=15)

    def _renderizar_catalogo(self):
        self.productos_grid.controls.clear()

        self.productos_grid.controls.append(
            ft.Card(content=ft.Container(
                content=ft.Column([
                    ft.Icon(Icons.ADD_PHOTO_ALTERNATE, size=44, color="#a3e635"),
                    ft.Text("Gestionar Menú", weight="bold", size=16),
                ], alignment="center", horizontal_alignment="center"),
                padding=10, ink=True, on_click=self._abrir_dialogo_producto,
                bgcolor="#1e293b", border_radius=10
            ))
        )

        for prod, data in self.inventario.items():
            ruta_imagen = data.get("imagen")
            elementos_tarjeta = []
            
            if ruta_imagen:
                elementos_tarjeta.append(
                    ft.Image(
                        src=ruta_imagen,
                        width=120,
                        height=90,
                        fit="cover",
                        border_radius=8
                    )
                )
            else:
                elementos_tarjeta.append(
                    ft.Container(
                        content=ft.IconButton(
                            icon=Icons.ADD_A_PHOTO,
                            icon_size=40,
                            icon_color="#94a3b8",
                            tooltip="Haz clic para añadir una foto a este platillo",
                            on_click=lambda e, p=prod: self._iniciar_actualizacion_imagen(p)
                        ),
                        height=90,
                        alignment=ft.Alignment(0, 0)
                    )
                )

            elementos_tarjeta.extend([
                ft.Text(prod, weight="bold", size=15, text_align="center", no_wrap=True),
                ft.Row([
                    ft.Text(f"${data['precio']:.2f}", color="#38bdf8", size=16, weight="bold"),
                    ft.IconButton(icon=Icons.DELETE, icon_color="#ef4444",
                                  icon_size=18, tooltip="Eliminar menú",
                                  on_click=lambda e, p=prod: self.delete_product_dialog.abrir(p))
                ], alignment="center", tight=True)
            ])

            self.productos_grid.controls.append(
                ft.Card(content=ft.Container(
                    content=ft.Column(elementos_tarjeta, alignment="center", horizontal_alignment="center"),
                    padding=10, ink=True,
                    on_click=lambda e, p=prod: self._add_to_cart(p, e) if e.control_id else None,
                    bgcolor="#1e293b", border_radius=10
                ))
            )
        try:
            self.update()
        except RuntimeError:
            pass

    def _iniciar_actualizacion_imagen(self, nombre_prod):
        """Abre el explorador nativo y actualiza la base de datos con la imagen elegida."""
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        
        ruta_origen = filedialog.askopenfilename(
            title=f"Imagen para {nombre_prod}",
            filetypes=[("Archivos de Imagen", "*.png *.jpg *.jpeg")]
        )
        root.destroy()

        if ruta_origen:
            try:
                _, ext = os.path.splitext(ruta_origen)
                nombre_archivo = f"{nombre_prod.lower().replace(' ', '_')}{ext}"
                
                base_dir = os.path.dirname(os.path.abspath(__file__))
                dir_assets = os.path.join(base_dir, "..", "assets")
                os.makedirs(dir_assets, exist_ok=True)
                ruta_destino = os.path.join(dir_assets, nombre_archivo)
                
                shutil.copy(ruta_origen, ruta_destino)

                self.dm.actualizar_imagen_producto(nombre_prod, nombre_archivo)
                self.inventario = self.dm.get_inventario()
                self._renderizar_catalogo()
                
                snack = ft.SnackBar(ft.Text(f"✅ Imagen de '{nombre_prod}' actualizada"), bgcolor="#166534")
                self.main_page.overlay.append(snack)
                snack.open = True
            except Exception as ex:
                snack = ft.SnackBar(ft.Text(f"⚠ Error al guardar imagen: {ex}"), bgcolor="#92400e")
                self.main_page.overlay.append(snack)
                snack.open = True
            
            self.main_page.update()

    def _abrir_dialogo_producto(self, e):
        if self.add_product_dialog not in self.main_page.overlay:
            self.main_page.overlay.append(self.add_product_dialog)
        
        self.add_product_dialog.actualizar_opciones(self.inventario)
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
        if e.control.content.controls[0].__class__.__name__ == 'Container':
            pass
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
                    CartItemRow(nombre_prod=prod, precio=precio,
                                cantidad=cant, on_change=self._on_cart_item_change)
                )

        self.txt_total.value = f"${total:.2f}"
        self.update()

    def _cobrar(self, e):
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
        resultado = self.dm.deshacer_ultima_venta()
        if resultado:
            self.inventario = self.dm.get_inventario()
            snack = ft.SnackBar(
                ft.Text(f"↩ Última venta (${resultado['total']:.2f}) deshecha correctamente"),
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
        panel_cobro = ft.Container(
            width=430, padding=20, bgcolor="#1e293b", border_radius=10,
            content=ft.Column([
                ft.Text("ORDEN ACTUAL", size=20, weight="bold"),
                ft.Divider(),
                self.lista_ticket,
                ft.Divider(),
                ft.Row([ft.Text("TOTAL", size=20), self.txt_total], alignment="spaceBetween"),
                ft.Container(height=10),
                ft.ElevatedButton("COBRAR", on_click=self._cobrar,
                                  bgcolor="#38bdf8", color="#0f172a", height=60,
                                  width=float('inf'),
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
                ft.Container(height=6),
                ft.OutlinedButton("↩ Deshacer última venta", on_click=self._deshacer,
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