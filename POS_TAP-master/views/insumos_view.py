import flet as ft


class InsumosView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True)
        self.main_page = page
        self.dm = data_manager
        self.padding = 20
        self.bgcolor = "#0f172a"

        # Campos de texto
        self.txt_nombre = ft.TextField(label="Nombre del Insumo", width=300, bgcolor="#1e293b", color="white")
        self.txt_unidad = ft.TextField(label="Unidad (pz, gr, kg, L)", width=200, bgcolor="#1e293b", color="white")
        self.txt_cantidad = ft.TextField(label="Cantidad Inicial", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="#1e293b", color="white")
        self.txt_minimo = ft.TextField(label="Stock Mínimo", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="#1e293b", color="white")
        self.txt_precio = ft.TextField(label="Precio de Compra", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="#1e293b", color="white")

        # Lista para ver lo que hay
        self.lista_insumos = ft.ListView(expand=True, spacing=5)

        # Construimos la estructura visual
        self.content = self._build_layout()

    # ✅ CARGAMOS DATOS AQUÍ
    def did_mount(self):
        self._cargar_insumos()

    def _guardar(self, e):
        try:
            self.dm.agregar_insumo(
                nombre=self.txt_nombre.value.strip(),
                unidad=self.txt_unidad.value.strip(),
                cantidad=float(self.txt_cantidad.value or 0),
                minimo=float(self.txt_minimo.value or 0),
                precio=float(self.txt_precio.value or 0)
            )
            self._mostrar_mensaje("✅ Insumo guardado correctamente", "#166534")
            # Limpiar
            self.txt_nombre.value = ""
            self.txt_unidad.value = ""
            self.txt_cantidad.value = ""
            self.txt_minimo.value = ""
            self.txt_precio.value = ""
            self._cargar_insumos()
            self.update()
        except Exception as err:
            self._mostrar_mensaje(f"❌ Error: {err}", "#92400e")

    # ✅ FUNCIÓN ELIMINAR
    def _eliminar_insumo(self, e, id_insumo):
        try:
            self.dm.eliminar_insumo(id_insumo)
            self._mostrar_mensaje("🗑️ Insumo eliminado correctamente", "#92400e")
            self._cargar_insumos()
            self.update()
        except Exception as err:
            self._mostrar_mensaje(f"❌ No se pudo eliminar: {err}", "#991b1b")

    def _cargar_insumos(self):
        self.lista_insumos.controls.clear()
        try:
            insumos = self.dm.get_lista_insumos_completa()
            for ins in insumos:
                self.lista_insumos.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(ins["nombre"], weight="bold"),
                                    ft.Text(f"Disp: {ins['cantidad_actual']} {ins['unidad_medida']} | Mín: {ins['stock_minimo']}", size=12)
                                ]),
                                ft.Row([
                                    ft.Text(f"${ins['precio_compra']}", weight="bold", color="#38bdf8"),
                                    # 🔴 BOTÓN ELIMINAR - Formato correcto 0.85
                                    ft.IconButton(
                                        0xe1b0,  # <-- El ícono va directo al inicio
                                        icon_color="#ef4444",
                                        tooltip="Eliminar insumo",
                                        on_click=lambda e, id=ins["id"]: self._eliminar_insumo(e, id)
                                    )
                                ], spacing=15)
                            ], alignment="spaceBetween"),
                            padding=ft.Padding(10, 8, 10, 8)
                        )
                    )
                )
            self.update()
        except Exception as err:
            print(f"Error al cargar insumos: {err}")

    def _mostrar_mensaje(self, texto, color):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()

    def _build_layout(self):
        return ft.Row([
            # Columna formulario
            ft.Container(
                width=400, 
                padding=20, 
                bgcolor="#1e293b", 
                border_radius=10, 
                content=ft.Column([
                    ft.Text("📦 Registrar Insumos", size=22, weight="bold"),
                    ft.Divider(),
                    self.txt_nombre,
                    ft.Container(height=10),
                    self.txt_unidad,
                    ft.Container(height=10),
                    self.txt_cantidad,
                    ft.Container(height=10),
                    self.txt_minimo,
                    ft.Container(height=10),
                    self.txt_precio,
                    ft.Container(height=20),
                    # 🔵 BOTÓN GUARDAR - FORMATO EXACTO VERSIÓN 0.85
                    ft.ElevatedButton(
                        "Guardar Insumo",  # <-- EL TEXTO VA DIRECTO, SIN NOMBRE 'label' NI 'text'
                        bgcolor="#2563eb",
                        color="white",
                        expand=True,
                        on_click=self._guardar
                    )
                ])
            ),
            # columna lista
            ft.Container(
                expand=True, 
                padding=20, 
                content=ft.Column([
                    ft.Text("📋 Inventario de Insumos", size=22, weight="bold"),
                    ft.Divider(),
                    self.lista_insumos
                ])
            )
        ])