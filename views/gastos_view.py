import flet as ft
from flet.controls.material.icons import Icons


class GastosView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm = data_manager

        # Inputs del formulario
        self.input_concepto = ft.TextField(
            label="Concepto del gasto", text_size=18,
            border_color="#38bdf8", width=400
        )
        self.input_monto = ft.TextField(
            label="Monto ($)", text_size=18,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8", width=400
        )

        # Lista de gastos del día
        self.lista_gastos = ft.ListView(expand=True, spacing=6)

        self.content = self._build_ui()

    # ─── ciclo de vida ───────────────────────────────────────────────────────

    def did_mount(self):
        self._cargar_gastos()

    # ─── acciones formulario ─────────────────────────────────────────────────

    def _guardar_gasto(self, e):
        if not self.input_concepto.value or not self.input_monto.value:
            self._snack("Por favor, llena ambos campos", ft.Colors.ORANGE_800)
            return

        try:
            monto = float(self.input_monto.value)
        except ValueError:
            self._snack("El monto debe ser un número", ft.Colors.RED_700)
            return

        self.dm.registrar_gasto(self.input_concepto.value, monto)
        self.input_concepto.value = ""
        self.input_monto.value = ""
        self._snack("Gasto registrado exitosamente", ft.Colors.GREEN_700)
        self._cargar_gastos()

    # ─── historial ───────────────────────────────────────────────────────────

    def _cargar_gastos(self):
        self.lista_gastos.controls.clear()
        gastos = self.dm.get_gastos_hoy()

        if not gastos:
            self.lista_gastos.controls.append(
                ft.Container(
                    ft.Text("Sin gastos registrados hoy.", color="#64748b", size=15),
                    padding=ft.padding.only(top=20)
                )
            )
        else:
            for i, g in enumerate(reversed(gastos), 1):
                self.lista_gastos.controls.append(
                    self._fila_gasto(g, i)
                )

        self.lista_gastos.update()

    def _fila_gasto(self, g: dict, idx: int):
        return ft.Container(
            bgcolor="#0f172a" if idx % 2 == 0 else "#1e293b",
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=ft.Row([
                ft.Text(
                    g["concepto"],
                    size=14, color="#cbd5e1", expand=True
                ),
                ft.Text(
                    f"${g['monto']:.2f}",
                    size=15, weight="bold", color="white", width=90
                ),
                ft.IconButton(
                    icon=Icons.EDIT,
                    icon_color="#38bdf8",
                    tooltip="Editar",
                    on_click=lambda e, gasto=g: self._abrir_dialogo_editar(gasto)
                ),
                ft.IconButton(
                    icon=Icons.DELETE,
                    icon_color="#f87171",
                    tooltip="Eliminar",
                    on_click=lambda e, gasto=g: self._confirmar_eliminar(gasto)
                ),
            ], vertical_alignment="center")
        )

    # ─── diálogo editar ──────────────────────────────────────────────────────

    def _abrir_dialogo_editar(self, gasto: dict):
        campo_concepto = ft.TextField(
            label="Concepto", value=gasto["concepto"],
            border_color="#38bdf8", width=340
        )
        campo_monto = ft.TextField(
            label="Monto ($)", value=str(gasto["monto"]),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8", width=340
        )

        def guardar_cambios(e):
            if not campo_concepto.value or not campo_monto.value:
                self._snack("Llena ambos campos", ft.Colors.ORANGE_800)
                return
            try:
                nuevo_monto = float(campo_monto.value)
            except ValueError:
                self._snack("El monto debe ser un número", ft.Colors.RED_700)
                return

            self.dm.editar_gasto(gasto["id"], campo_concepto.value, nuevo_monto)
            dialogo.open = False
            self.main_page.update()
            self._snack("Gasto actualizado", ft.Colors.GREEN_700)
            self._cargar_gastos()

        def cancelar(e):
            dialogo.open = False
            self.main_page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Gasto", color="#38bdf8", weight="bold"),
            bgcolor="#1e293b",
            content=ft.Column([
                campo_concepto,
                ft.Container(height=10),
                campo_monto,
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar,
                              style=ft.ButtonStyle(color="#64748b")),
                ft.ElevatedButton(
                    "Guardar", icon=Icons.SAVE, on_click=guardar_cambios,
                    color="#0f172a", bgcolor="#38bdf8",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.main_page.overlay.append(dialogo)
        dialogo.open = True
        self.main_page.update()

    # ─── diálogo confirmar eliminar ───────────────────────────────────────────

    def _confirmar_eliminar(self, gasto: dict):
        def eliminar(e):
            self.dm.eliminar_gasto(gasto["id"])
            dialogo.open = False
            self.main_page.update()
            self._snack("Gasto eliminado", ft.Colors.RED_700)
            self._cargar_gastos()

        def cancelar(e):
            dialogo.open = False
            self.main_page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar Gasto", color="#f87171", weight="bold"),
            bgcolor="#1e293b",
            content=ft.Text(
                f'¿Eliminar "{gasto["concepto"]}" (${gasto["monto"]:.2f})?',
                color="#cbd5e1"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar,
                              style=ft.ButtonStyle(color="#64748b")),
                ft.ElevatedButton(
                    "Eliminar", icon=Icons.DELETE, on_click=eliminar,
                    color="white", bgcolor="#ef4444",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.main_page.overlay.append(dialogo)
        dialogo.open = True
        self.main_page.update()

    # ─── helpers ─────────────────────────────────────────────────────────────

    def _snack(self, mensaje: str, color):
        self.main_page.snack_bar = ft.SnackBar(ft.Text(mensaje), bgcolor=color)
        self.main_page.snack_bar.open = True
        self.main_page.update()

    # ─── UI ──────────────────────────────────────────────────────────────────

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
                ft.ElevatedButton(
                    "GUARDAR GASTO", icon=Icons.SAVE, on_click=self._guardar_gasto,
                    color="#0f172a", bgcolor="#38bdf8", height=50, width=400,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ], horizontal_alignment="center")
        )

        historial = ft.Container(
            expand=True,
            bgcolor="#1e293b",
            border_radius=12,
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Icon(Icons.RECEIPT_LONG, color="#38bdf8", size=22),
                    ft.Text("Gastos de Hoy", size=18, weight="bold", color="#38bdf8"),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=Icons.REFRESH,
                        icon_color="#38bdf8",
                        tooltip="Actualizar",
                        on_click=lambda e: self._cargar_gastos()
                    )
                ], vertical_alignment="center"),
                ft.Divider(color="#334155"),
                ft.Row([
                    ft.Text("CONCEPTO", size=13, weight="bold", color="#64748b", expand=True),
                    ft.Text("MONTO", size=13, weight="bold", color="#64748b", width=90),
                    ft.Container(width=96),  # espacio para botones
                ]),
                ft.Divider(color="#334155", height=4),
                self.lista_gastos,
            ], expand=True)
        )

        return ft.Column([
            ft.Text("Gestión de Gastos", size=28, weight="bold", color="white"),
            ft.Container(height=20),
            ft.Row([
                formulario,
                ft.Container(width=30),
                historial,
            ], expand=True, vertical_alignment="start")
        ], expand=True)
