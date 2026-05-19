import flet as ft
from flet.controls.material.icons import Icons


class GastosView(ft.Container):
    """
    Vista de Gastos Avanzada - Incluye Panel de Insumos Rápidos ($600.00)
    que se registra directamente en la base de datos `pos.db` como un egreso.
    """
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=20)
        self.main_page = page
        self.dm        = data_manager

        # ─── CONFIGURACIÓN DE INSUMOS POR PLATILLO ───
        # Cada uno de estos generará un botón automático con costo fijo de $600
        self.platillos_insumos = [
            "Mole Poblano",
            "Tacos al Pastor",
            "Enchiladas Verdes",
            "Chiles en Nogada",
            "Tamales Oaxaqueños"
        ]

        # ─── COMPONENTES DEL FORMULARIO TRADICIONAL ───
        self.input_concepto = ft.TextField(
            label="Concepto del gasto manual",
            hint_text="Ej: Pago de flete o mantenimiento",
            text_size=15,
            border_color="#38bdf8",
            expand=True,
        )
        self.input_monto = ft.TextField(
            label="Monto ($)",
            hint_text="Ej: 150.00",
            text_size=15,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8",
            width=140,
        )

        # ─── COMPONENTES DEL HISTORIAL ───
        self.lista_gastos = ft.ListView(expand=True, spacing=8)

        # Inicializar interfaz
        self.content = self._build_layout()

    def did_mount(self):
        self._cargar_historial_gastos()
        self.main_page.pubsub.subscribe(self._escuchar_cambios_pubsub)

    def will_unmount(self):
        self.main_page.pubsub.unsubscribe()

    def _escuchar_cambios_pubsub(self, message):
        if message == "actualizar_gastos":
            self._cargar_historial_gastos()

    # 🚀 NUEVA FUNCIÓN: Registro automático de insumos a un toque
    def _comprar_insumos_rapido(self, platillo: str):
        concepto_final = f"[Materia Prima] Insumos para {platillo}"
        monto_fijo = 600.0

        # Persistencia directa en tu base de datos mediante tu DataManager existente
        self.dm.registrar_gasto(concepto_final, monto_fijo)

        # Notificación visual y sincronización en tiempo real
        self._mostrar_snackbar(f"📦 Compra registrada: Insumos para {platillo} ($600.00)", ft.Colors.GREEN_700)
        self.main_page.pubsub.send_all("actualizar_gastos")
        self.update()

    def _guardar_gasto_manual(self, e):
        concepto = self.input_concepto.value.strip() if self.input_concepto.value else ""
        monto_raw = self.input_monto.value.strip() if self.input_monto.value else ""

        if not concepto or not monto_raw:
            self._mostrar_snackbar("⚠ Llena los campos para gasto manual", ft.Colors.ORANGE_800)
            return

        try:
            monto = float(monto_raw)
            if monto <= 0:
                self._mostrar_snackbar("⚠ El monto debe ser mayor a cero", ft.Colors.RED_700)
                return
        except ValueError:
            self._mostrar_snackbar("⚠ El monto debe ser un número válido", ft.Colors.RED_700)
            return

        self.dm.registrar_gasto(f"[Otros] {concepto}", monto)
        
        self.input_concepto.value = ""
        self.input_monto.value = ""
        self._mostrar_snackbar("✅ Gasto manual registrado con éxito", ft.Colors.GREEN_700)
        self.main_page.pubsub.send_all("actualizar_gastos")
        self.update()

    def _cargar_historial_gastos(self):
        self.lista_gastos.controls.clear()
        gastos = self.dm.get_gastos_hoy() if hasattr(self.dm, "get_gastos_hoy") else []

        if not gastos:
            self.lista_gastos.controls.append(
                ft.Row(
                    [ft.Text("No hay egresos registrados hoy.", color="#64748b", italic=True)],
                    alignment=ft.MainAxisAlignment.CENTER, # <─── Solución nativa directa
                )
            )
        else:
            for i, g in enumerate(reversed(gastos), 1):
                g_id = g.get("id") if isinstance(g, dict) else g[0]
                g_concepto = g.get("concepto", "Gasto") if isinstance(g, dict) else g[1]
                g_monto = g.get("monto", 0.0) if isinstance(g, dict) else g[2]
                g_hora = g.get("hora", "--:--") if isinstance(g, dict) else "--:--"

                self.lista_gastos.controls.append(
                    ft.Container(
                        bgcolor="#0f172a" if i % 2 == 0 else "#1e293b",
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                        content=ft.Row([
                            ft.Icon(Icons.MONEY_OFF if "[Otros]" in g_concepto else Icons.INVENTORY, 
                                    color="#f87171" if "[Otros]" in g_concepto else "#a3e635", size=20),
                            ft.Column([
                                ft.Text(g_concepto, size=14, weight="bold", color="white", max_lines=1),
                                ft.Text(f"Hora: {g_hora}", size=11, color="#64748b"),
                            ], expand=True, spacing=2),
                            ft.Text(f"${g_monto:.2f}", size=15, weight="bold", color="#f87171"),
                        ], vertical_alignment="center")
                    )
                )
        self.lista_gastos.update()

    def _mostrar_snackbar(self, texto, color_fondo):
        self.main_page.snack_bar = ft.SnackBar(ft.Text(texto), bgcolor=color_fondo)
        self.main_page.snack_bar.open = True
        self.main_page.update()

    def _build_layout(self):
        # 🚀 1. NUEVO PANEL: Insumos rápidos de un solo toque
        grid_insumos = ft.GridView(
            expand=True,
            max_extent=180,
            child_aspect_ratio=1.6,
            spacing=10,
            run_spacing=10,
        )

        # Generamos los botones dinámicamente según la lista configurada arriba
        for platillo in self.platillos_insumos:
            grid_insumos.controls.append(
                ft.Container(
                    bgcolor="#0f172a",
                    border=ft.border.all(1, "#334155"),
                    border_radius=8,
                    padding=8,
                    ink=True,
                    on_click=lambda e, p=platillo: self._comprar_insumos_rapido(p),
                    content=ft.Column([
                        ft.Text(f"Insumos para\n{platillo}", size=12, weight="bold", text_align="center", color="white"),
                        ft.Text("$600.00", size=13, color="#a3e635", weight="bold")
                    ], alignment="center", horizontal_alignment="center", spacing=4)
                )
            )

        panel_insumos_rapidos = ft.Container(
            bgcolor="#1e293b",
            padding=20,
            border_radius=12,
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Icon(Icons.PLAYLIST_ADD_CHECK, color="#a3e635", size=22),
                    ft.Text("Compra de Insumos Fijos ($600)", size=16, weight="bold", color="white")
                ]),
                ft.Divider(color="#334155", height=10),
                grid_insumos
            ], expand=True)
        )

        # 2. PANEL IZQUIERDO TRADICIONAL: Gasto manual (reducido para dar espacio)
        panel_manual = ft.Container(
            bgcolor="#1e293b",
            padding=20,
            border_radius=12,
            content=ft.Column([
                ft.Text("Gasto Manual / Extraordinario", size=16, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155", height=10),
                ft.Row([self.input_concepto]),
                ft.Row([
                    self.input_monto,
                    ft.ElevatedButton(
                        "GUARDAR",
                        icon=Icons.SAVE,
                        bgcolor="#38bdf8",
                        color="#0f172a",
                        expand=True,
                        height=45,
                        on_click=self._guardar_gasto_manual,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
                    )
                ], spacing=10)
            ], tight=True)
        )

        # Columna que junta el formulario manual arriba y el grid rápido abajo
        columna_izquierda = ft.Column([
            panel_manual,
            panel_insumos_rapidos
        ], width=380, spacing=15)

        # 3. PANEL DERECHO: Historial diario
        panel_historial = ft.Container(
            bgcolor="#1e293b",
            padding=20,
            border_radius=12,
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Icon(Icons.LIST_ALT, color="#38bdf8", size=22),
                    ft.Text("Egresos de la Jornada", size=16, weight="bold", color="white"),
                ]),
                ft.Divider(color="#334155", height=10),
                self.lista_gastos
            ], expand=True)
        )

        # Distribución de toda la pantalla
        return ft.Column([
            ft.Text("Módulo de Egresos y Abastecimiento", size=26, weight="bold", color="white"),
            ft.Container(height=10),
            ft.Row([
                columna_izquierda,
                panel_historial
            ], expand=True, spacing=15, vertical_alignment="start")
        ], expand=True)
