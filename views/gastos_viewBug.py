import flet as ft
from flet.controls.material.icons import Icons


class GastosView(ft.Container):
    """
    Vista de Gastos - Formulario funcional con validaciones y persistencia.
    """
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm        = data_manager

        # Inputs con estilo moderno
        self.input_concepto = ft.TextField(
            label="Concepto del gasto",
            hint_text="Ej: Compra de ingredientes",
            text_size=16,
            border_color="#38bdf8",
            width=400,
        )
        self.input_monto = ft.TextField(
            label="Monto ($)",
            hint_text="Ej: 150.00",
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8",
            width=400,
        )

        self.btn_topicos = ft.PopupMenuButton(
            icon=Icons.ARROW_DROP_DOWN,
            tooltip="Tópicos recientes",
            items=[]
        )

        self.input_topico = ft.TextField(
            label="Tópico",
            hint_text="Ej: Insumos, Servicios, etc.",
            text_size=16,
            border_color="#38bdf8",
            width=400,
            suffix=self.btn_topicos
        )

        self.lista_gastos = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)
        self.content = self._build_ui()

    def did_mount(self):
        self._cargar_gastos()
        self._cargar_topicos()

    def _cargar_topicos(self):
        topicos = self.dm.get_topicos_historicos()
        self.btn_topicos.items.clear()
        for t in topicos:
            self.btn_topicos.items.append(
                ft.PopupMenuItem(content=ft.Text(t), data=t, on_click=self._seleccionar_topico)
            )
        self.btn_topicos.update()

    def _seleccionar_topico(self, e):
        self.input_topico.value = e.control.data
        self.input_topico.update()

    def _cargar_gastos(self):
        self.lista_gastos.controls.clear()
        gastos = self.dm.get_gastos_hoy()
        
        if not gastos:
            self.lista_gastos.controls.append(ft.Text("No hay gastos registrados hoy.", color="grey"))
        else:
            # Agrupar por topico
            agrupados = {}
            for g in gastos:
                t = g.get("topico", "General")
                if t not in agrupados:
                    agrupados[t] = []
                agrupados[t].append(g)
            
            for topico, lista in agrupados.items():
                self.lista_gastos.controls.append(
                    ft.Row([
                        ft.Text(f"Tópico: {topico}", size=18, weight="bold", color="#38bdf8", expand=True),
                        ft.IconButton(icon=Icons.DELETE, icon_color=ft.Colors.RED_400, tooltip="Eliminar gastos de este tópico",
                                      data=topico, on_click=self._eliminar_topico)
                    ], vertical_alignment="center")
                )
                for g in lista:
                    self.lista_gastos.controls.append(
                        ft.Container(
                            bgcolor="#1e293b",
                            padding=10,
                            border_radius=8,
                            content=ft.Row([
                                ft.Text(g['concepto'], expand=True, color="white"),
                                ft.Text(f"${g['monto']:.2f}", weight="bold", color="#f87171"),
                                ft.IconButton(icon=Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_300, 
                                              data=g.get('id'), on_click=self._eliminar_gasto, tooltip="Eliminar gasto")
                            ])
                        )
                    )
        self.lista_gastos.update()

    def _eliminar_topico(self, e):
        topico = e.control.data
        self.dm.eliminar_gastos_por_topico_hoy(topico)
        self._cargar_gastos()
        self._cargar_topicos()
        self.main_page.snack_bar = ft.SnackBar(ft.Text(f"Se eliminaron los gastos de {topico}"), bgcolor=ft.Colors.RED_700)
        self.main_page.snack_bar.open = True
        self.main_page.update()

    def _eliminar_gasto(self, e):
        id_gasto = e.control.data
        if id_gasto:
            self.dm.eliminar_gasto(id_gasto)
            self._cargar_gastos()
            self._cargar_topicos()
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Gasto eliminado"), bgcolor=ft.Colors.RED_700)
            self.main_page.snack_bar.open = True
            self.main_page.update()

    def _guardar_gasto(self, e):
        # 1. Validar campos vacios
        if not self.input_concepto.value or not self.input_monto.value:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ Por favor, llena ambos campos"), bgcolor=ft.Colors.ORANGE_800
            )
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        # 2. Validar que el monto sea un numero valido
        try:
            monto = float(self.input_monto.value)
        except ValueError:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ El monto debe ser un número válido"), bgcolor=ft.Colors.RED_700
            )
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        # 3. Guardar via DataManager
        topico = self.input_topico.value.strip() if self.input_topico.value else "General"
        # BUG CORREGIDO: Se pasaba el valor string del input ('self.input_monto.value') en vez de la variable float validada 'monto'.
        self.dm.registrar_gasto(self.input_concepto.value, monto, topico)

        # 4. Limpiar formulario
        self.input_concepto.value = ""
        self.input_monto.value    = ""
        self.input_topico.value   = ""
        
        self.input_concepto.update()
        self.input_monto.update()
        self.input_topico.update()
        self._cargar_gastos()
        self._cargar_topicos()

        self.main_page.snack_bar = ft.SnackBar(
            ft.Text("✅ Gasto registrado exitosamente"), bgcolor=ft.Colors.GREEN_700
        )
        self.main_page.snack_bar.open = True
        # BUG CORREGIDO: Faltaba llamar a update() en la página para que el SnackBar fuera visible.
        self.main_page.update()

    def _build_ui(self):
        formulario = ft.Container(
            bgcolor="#1e293b",
            padding=40,
            border_radius=15,
            content=ft.Column([
                ft.Text("Registrar Nuevo Gasto", size=22, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155", height=25),
                self.input_topico,
                ft.Container(height=12),
                self.input_concepto,
                ft.Container(height=12),
                self.input_monto,
                ft.Container(height=24),
                ft.ElevatedButton(
                    "GUARDAR GASTO",
                    icon=Icons.SAVE,
                    bgcolor="#38bdf8",
                    color="#0f172a",
                    height=50,
                    width=400,
                    on_click=self._guardar_gasto,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ], horizontal_alignment="center")
        )

        panel_lista = ft.Container(
            bgcolor="#0f172a",
            padding=20,
            border_radius=15,
            border=ft.border.all(1, "#334155"),
            expand=True,
            content=ft.Column([
                ft.Text("Gastos de Hoy (Agrupados por Tópico)", size=22, weight="bold", color="white"),
                ft.Divider(color="#334155", height=20),
                self.lista_gastos
            ], expand=True)
        )

        return ft.Column([
            ft.Text("Gestión de Gastos", size=28, weight="bold", color="white"),
            ft.Container(height=30),
            ft.Row([formulario, ft.Container(width=20), panel_lista], alignment="start", vertical_alignment="start", expand=True),
        ], expand=True)
