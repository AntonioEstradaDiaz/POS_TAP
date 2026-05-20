import flet as ft


class RecetasView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True)
        self.main_page = page
        self.dm = data_manager
        self.padding = 20
        self.bgcolor = "#0f172a"

        # Variables de estado
        self.filas_insumos = []  # Guarda tuplas (dropdown, textfield, row)

        # ── Campos principales ──────────────────────────────────────────
        self.txt_nombre_platillo = ft.TextField(
            label="Nombre del Platillo",
            hint_text="Ej: Tacos de Canasta",
            width=400,
            bgcolor="#1e293b",
            color="white",
        )
        self.txt_precio_venta = ft.TextField(
            label="Precio de Venta",
            hint_text="Ej: 55.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200,
            bgcolor="#1e293b",
            color="white",
        )

        # Contenedor dinámico de filas de ingredientes
        self.contenedor_insumos = ft.Column(spacing=10)

        # Lista de recetas guardadas
        self.lista_recetas = ft.ListView(expand=True, spacing=5)

        # Opciones del dropdown (se cargan al montar)
        self.opciones_insumos = []

        # Construir la UI
        self.content = self._build_ui()

    # ────────────────────────────────────────────────────────────────────
    # CICLO DE VIDA
    # ────────────────────────────────────────────────────────────────────

    def did_mount(self):
        """Se ejecuta cuando la vista ya está montada en la página."""
        self._cargar_insumos_base()
        self._cargar_recetas()

    # ────────────────────────────────────────────────────────────────────
    # CARGA DE DATOS
    # ────────────────────────────────────────────────────────────────────

    def _cargar_insumos_base(self):
        """Carga los insumos disponibles para usar en los dropdowns."""
        try:
            datos = self.dm.get_lista_insumos_completa()
            self.opciones_insumos = []
            for ins in datos:
                try:
                    self.opciones_insumos.append(
                        ft.dropdown.Option(
                            str(ins["id"]),
                            f"{ins['nombre']} ({ins['unidad_medida']})"
                        )
                    )
                except Exception as e:
                    print(f"Error procesando insumo: {e}")
                    continue
        except Exception as e:
            print(f"Error cargando insumos: {e}")
            self.opciones_insumos = []

    def _cargar_recetas(self):
        """Consulta las recetas guardadas y refresca la lista derecha."""
        self.lista_recetas.controls.clear()
        try:
            recetas = self.dm.obtener_todas_recetas()

            if not recetas:
                self.lista_recetas.controls.append(
                    ft.Text("No hay recetas registradas.", color="#64748b")
                )
            else:
                for rec in recetas:
                    try:
                        nombre = rec["nombre"]
                        precio = float(rec["precio"] or 0)
                        costo  = float(rec["costo"]  or 0)
                    except Exception as e:
                        print(f"Error leyendo receta: {e}")
                        continue

                    ganancia = precio - costo

                    self.lista_recetas.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Column(
                                            [
                                                ft.Text(nombre, weight="bold", size=16, color="white"),
                                                ft.Text(
                                                    f"Costo: ${costo:.2f}  |  Venta: ${precio:.2f}",
                                                    size=12,
                                                    color="#94a3b8",
                                                ),
                                            ],
                                            expand=True,
                                        ),
                                        ft.Column(
                                            [
                                                ft.Text(
                                                    f"Ganancia: ${ganancia:.2f}",
                                                    color="#4ade80",
                                                    weight="bold",
                                                ),
                                                ft.TextButton(
                                                    "🗑 Eliminar",
                                                    style=ft.ButtonStyle(color="#f87171"),
                                                    on_click=lambda e, n=nombre: self._eliminar_receta(n),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                padding=10,
                            )
                        )
                    )

        except Exception as e:
            print(f"Error al cargar recetas: {e}")
            self.lista_recetas.controls.append(
                ft.Text("Error al cargar recetas.", color="#f87171")
            )

        self.lista_recetas.update()

    # ────────────────────────────────────────────────────────────────────
    # MANEJO DE FILAS DE INGREDIENTES
    # ────────────────────────────────────────────────────────────────────

    def _agregar_fila_insumo(self, e=None):
        """Agrega una nueva fila de selección de insumo + cantidad."""
        dropdown = ft.Dropdown(
            options=self.opciones_insumos,
            width=250,
            bgcolor="#1e293b",
            color="white",
            hint_text="Seleccionar insumo",
        )
        txt_cantidad = ft.TextField(
            label="Cantidad",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
            bgcolor="#1e293b",
            color="white",
            hint_text="Ej: 0.250",
        )

        fila = ft.Row(spacing=10)
        btn_quitar = ft.TextButton(
            "✕ Quitar",
            style=ft.ButtonStyle(color="#f87171"),
            on_click=lambda e: self._quitar_fila(fila),
        )
        fila.controls = [dropdown, txt_cantidad, btn_quitar]

        self.filas_insumos.append((dropdown, txt_cantidad, fila))
        self.contenedor_insumos.controls.append(fila)
        self.update()

    def _quitar_fila(self, fila):
        """Elimina una fila de ingrediente de la UI y del estado interno."""
        self.filas_insumos = [t for t in self.filas_insumos if t[2] is not fila]
        if fila in self.contenedor_insumos.controls:
            self.contenedor_insumos.controls.remove(fila)
        self.update()

    # ────────────────────────────────────────────────────────────────────
    # GUARDAR RECETA
    # ────────────────────────────────────────────────────────────────────

    def _guardar_receta(self, e):
        """Valida los datos del formulario y llama a dm.nueva_receta."""
        nombre     = self.txt_nombre_platillo.value.strip()
        precio_str = self.txt_precio_venta.value.strip()

        if not nombre or not precio_str:
            self._mostrar_mensaje("❌ Pon nombre y precio del platillo", "#991b1b")
            return

        try:
            precio_venta = float(precio_str)
        except ValueError:
            self._mostrar_mensaje("❌ El precio debe ser un número", "#991b1b")
            return

        if not self.filas_insumos:
            self._mostrar_mensaje("❌ Agrega al menos 1 ingrediente", "#991b1b")
            return

        ingredientes = []
        for dropdown, txt_cantidad, _ in self.filas_insumos:
            if not dropdown.value or not txt_cantidad.value.strip():
                self._mostrar_mensaje("❌ Revisa que todos los ingredientes estén completos", "#991b1b")
                return
            try:
                ingredientes.append({
                    "id":       int(dropdown.value),
                    "cantidad": float(txt_cantidad.value.strip()),
                })
            except ValueError:
                self._mostrar_mensaje("❌ La cantidad debe ser un número", "#991b1b")
                return

        try:
            self.dm.nueva_receta(nombre, precio_venta, ingredientes)
            self._mostrar_mensaje("✅ Receta guardada correctamente", "#166534")
            self._limpiar_formulario()
            self._cargar_recetas()
            self.update()
        except Exception as err:
            self._mostrar_mensaje(f"❌ Error al guardar: {err}", "#991b1b")
            print(f"ERROR DETALLADO: {err}")

    # ────────────────────────────────────────────────────────────────────
    # ELIMINAR RECETA
    # ────────────────────────────────────────────────────────────────────

    def _eliminar_receta(self, nombre_platillo):
        """Elimina la receta del platillo indicado y refresca la lista."""
        try:
            eliminado = self.dm.eliminar_receta(nombre_platillo)
            if eliminado:
                self._mostrar_mensaje(f"🗑 Receta de '{nombre_platillo}' eliminada", "#92400e")
            else:
                self._mostrar_mensaje("⚠️ No se encontró la receta", "#92400e")
            self._cargar_recetas()
        except Exception as err:
            self._mostrar_mensaje(f"❌ Error al eliminar: {err}", "#991b1b")
            print(f"ERROR DETALLADO: {err}")

    # ────────────────────────────────────────────────────────────────────
    # UTILIDADES
    # ────────────────────────────────────────────────────────────────────

    def _limpiar_formulario(self):
        """Resetea todos los campos del formulario al estado inicial."""
        self.txt_nombre_platillo.value = ""
        self.txt_precio_venta.value    = ""
        self.contenedor_insumos.controls.clear()
        self.filas_insumos.clear()

    def _mostrar_mensaje(self, texto, color):
        """Muestra un SnackBar con el mensaje y color indicados."""
        snack = ft.SnackBar(ft.Text(texto, color="white"), bgcolor=color)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()

    # ────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA UI
    # ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        return ft.Row(
            [
                # ── Columna izquierda: formulario ──────────────────────
                ft.Container(
                    width=470,
                    padding=20,
                    bgcolor="#1e293b",
                    border_radius=10,
                    content=ft.Column(
                        [
                            ft.Text("📝 Nueva Receta / Platillo", size=22, weight="bold", color="white"),
                            ft.Divider(color="#334155"),
                            self.txt_nombre_platillo,
                            ft.Container(height=8),
                            self.txt_precio_venta,
                            ft.Container(height=15),
                            ft.Text("🥣 Ingredientes:", weight="bold", color="white"),
                            ft.Divider(color="#334155"),
                            self.contenedor_insumos,
                            ft.Container(height=10),
                            ft.ElevatedButton(
                                "+ Agregar Ingrediente",
                                bgcolor="#0891b2",
                                color="white",
                                on_click=self._agregar_fila_insumo,
                            ),
                            ft.Container(height=15),
                            ft.ElevatedButton(
                                "💾 Guardar Receta",
                                bgcolor="#16a34a",
                                color="white",
                                expand=True,
                                on_click=self._guardar_receta,
                            ),
                        ],
                        scroll="auto",
                    ),
                ),

                # ── Columna derecha: lista de recetas ──────────────────
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text("📋 Recetas Guardadas", size=22, weight="bold", color="white"),
                            ft.Divider(color="#334155"),
                            self.lista_recetas,
                        ],
                        expand=True,
                    ),
                ),
            ],
            expand=True,
        )