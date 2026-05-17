import flet as ft
from flet.controls.material.icons import Icons

class GastosView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm = data_manager
        
        # Inputs con estilo moderno
        self.input_concepto = ft.TextField(label="Concepto del gasto", text_size=18, border_color="#38bdf8", width=400)
        self.input_monto = ft.TextField(label="Monto ($)", text_size=18, keyboard_type=ft.KeyboardType.NUMBER, border_color="#38bdf8", width=400)
        
        # NUEVO: contenedor para la lista de gastos del día
        self.lista_gastos = ft.Column([], scroll="auto", spacing=6)
        self.txt_total = ft.Text("Total del día: $0.00", size=16, weight="bold", color="#38bdf8")
        
        self.content = self._build_ui()
        self._refrescar_lista()  # cargar gastos al abrir la pantalla

    def _refrescar_lista(self):
        """Recarga los gastos del día en la lista visual."""
        gastos = self.dm.get_gastos_hoy()
        self.lista_gastos.controls.clear()

        if not gastos:
            self.lista_gastos.controls.append(
                ft.Text("Sin gastos registrados hoy.", color="#64748b", italic=True)
            )
            self.txt_total.value = "Total del día: $0.00"
        else:
            total = 0
            for g in gastos:
                total += g["monto"]
                self.lista_gastos.controls.append(
                    ft.Row([
                        ft.Icon(Icons.RECEIPT_LONG, color="#94a3b8", size=18),
                        ft.Text(g["concepto"], expand=True, color="white"),
                        ft.Text(f"${g['monto']:.2f}", color="#f87171", weight="bold"),
                    ])
                )
            self.txt_total.value = f"Total del día: ${total:.2f}"

        if self.main_page:
            self.main_page.update()

    def _guardar_gasto(self, e):
        if not self.input_concepto.value or not self.input_monto.value:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Por favor, llena ambos campos"), bgcolor=ft.Colors.ORANGE_800)
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return
            
        try:
            monto = float(self.input_monto.value)
        except ValueError:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("El monto debe ser un número"), bgcolor=ft.Colors.RED_700)
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        # Llamada al DataManager
        self.dm.registrar_gasto(self.input_concepto.value, monto)
        
        # Limpiar formulario
        self.input_concepto.value = ""
        self.input_monto.value = ""
        
        self.main_page.snack_bar = ft.SnackBar(ft.Text("Gasto registrado exitosamente"), bgcolor=ft.Colors.GREEN_700)
        self.main_page.snack_bar.open = True
        self._refrescar_lista()  # NUEVO: refresca la lista al guardar

    def _build_ui(self):
        formulario = ft.Container(
            bgcolor="#1e293b",
            padding=40,
            border_radius=15,
            content=ft.Column([
                ft.Text("Registrar Nuevo Gasto", size=24, weight="bold", color="#38bdf8"),
                ft.Divider(color="#0f172a", height=20),
                self.input_concepto,
                ft.Container(height=10),
                self.input_monto,
                ft.Container(height=20),
                ft.ElevatedButton("GUARDAR GASTO", icon=Icons.SAVE, on_click=self._guardar_gasto,
                                  color="#0f172a", bgcolor="#38bdf8", height=50, width=400,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))
            ], horizontal_alignment="center")
        )
        
        # NUEVO: panel de gastos del día
        panel_gastos = ft.Container(
            bgcolor="#1e293b", padding=30, border_radius=15, width=400,
            content=ft.Column([
                ft.Text("Gastos de Hoy", size=20, weight="bold", color="white"),
                ft.Divider(color="#0f172a", height=10),
                self.lista_gastos,
                ft.Divider(color="#334155", height=10),
                self.txt_total,
            ], spacing=8)
        )
        
        return ft.Column([
            ft.Text("Gestión de Gastos", size=28, weight="bold", color="white"),
            ft.Container(height=30),
            ft.Row(
                [formulario, ft.Container(width=30), panel_gastos],
                alignment="center",
                vertical_alignment="start"
            )
        ], expand=True)