import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime, date
import calendar


class GastosView(ft.Row):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, vertical_alignment="start", spacing=0)
        self.main_page = page
        self.dm = data_manager

        self.selected_date = date.today()
        self.current_month = date.today().month
        self.current_year = date.today().year

        self.input_concepto = ft.TextField(
            label="Concepto del gasto",
            hint_text="Ej: Compra de ingredientes",
            text_size=15,
            border_color="#38bdf8",
        )
        self.input_monto = ft.TextField(
            label="Monto ($)",
            hint_text="Ej: 150.00",
            text_size=15,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#38bdf8",
        )

        self._gastos_dia_col = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO)
        self._gastos_dia_titulo = ft.Text(
            self._titulo_fecha(self.selected_date),
            size=13, weight="bold", color="#38bdf8",
        )
        self._total_dia_text = ft.Text("Total: $0.00", size=12, color="#94a3b8")
        self._cal_container = ft.Container()

        self.controls = self._build_controls()
        self._refresh_calendar()
        self._refresh_gastos_dia()

    def _titulo_fecha(self, d: date) -> str:
        meses = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]
        return f"{d.day} de {meses[d.month-1]} de {d.year}"

    def _get_gastos_del_dia(self, d: date) -> list:
        fecha_str = d.strftime("%Y-%m-%d")
        try:
            with self.dm._get_conn() as conn:
                rows = conn.execute(
                    "SELECT concepto, monto FROM gastos WHERE fecha = ? ORDER BY id",
                    (fecha_str,)
                ).fetchall()
            return [{"concepto": r["concepto"], "monto": r["monto"]} for r in rows]
        except Exception:
            return []

    def _get_dias_con_gastos_en_mes(self) -> set:
        try:
            mes_str = f"{self.current_year}-{self.current_month:02d}"
            with self.dm._get_conn() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT fecha FROM gastos WHERE fecha LIKE ?",
                    (f"{mes_str}%",)
                ).fetchall()
            dias = set()
            for r in rows:
                try:
                    dias.add(datetime.strptime(r["fecha"], "%Y-%m-%d").day)
                except Exception:
                    pass
            return dias
        except Exception:
            return set()

    def _guardar_gasto(self, e):
        if not self.input_concepto.value or not self.input_monto.value:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ Por favor, llena ambos campos"), bgcolor=ft.Colors.ORANGE_800
            )
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return
        try:
            monto = float(self.input_monto.value)
        except ValueError:
            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ El monto debe ser un número válido"), bgcolor=ft.Colors.RED_700
            )
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        self.dm.registrar_gasto(self.input_concepto.value, monto)
        self.input_concepto.value = ""
        self.input_monto.value = ""

        self.main_page.snack_bar = ft.SnackBar(
            ft.Text("✅ Gasto registrado exitosamente"), bgcolor=ft.Colors.GREEN_700
        )
        self.main_page.snack_bar.open = True

        self.selected_date = date.today()
        self.current_month = date.today().month
        self.current_year = date.today().year

        self._refresh_calendar()
        self._refresh_gastos_dia()
        self.main_page.update()

    def _seleccionar_dia(self, d: date):
        self.selected_date = d
        self._refresh_gastos_dia()
        self._refresh_calendar()
        self.main_page.update()

    def _mes_anterior(self, e):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._refresh_calendar()
        self.main_page.update()

    def _mes_siguiente(self, e):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._refresh_calendar()
        self.main_page.update()

    def _refresh_gastos_dia(self):
        gastos = self._get_gastos_del_dia(self.selected_date)
        self._gastos_dia_titulo.value = self._titulo_fecha(self.selected_date)
        self._gastos_dia_col.controls.clear()

        if not gastos:
            self._gastos_dia_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(Icons.RECEIPT_LONG, color="#334155", size=30),
                        ft.Text("Sin gastos este día", color="#475569", size=12),
                    ], horizontal_alignment="center", spacing=4),
                    padding=ft.padding.symmetric(vertical=16),
                )
            )
            self._total_dia_text.value = "Total: $0.00"
        else:
            total = 0.0
            for g in gastos:
                total += g["monto"]
                self._gastos_dia_col.controls.append(
                    ft.Container(
                        bgcolor="#0f172a",
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        content=ft.Row([
                            ft.Icon(Icons.CIRCLE, color="#38bdf8", size=7),
                            ft.Text(g["concepto"], color="white", size=12, expand=True),
                            ft.Text(f"${g['monto']:,.2f}", color="#4ade80", size=12, weight="bold"),
                        ], alignment="spaceBetween"),
                    )
                )
            self._total_dia_text.value = f"Total: ${total:,.2f}"

    def _refresh_calendar(self):
        meses_nombres = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        dias_con_gastos = self._get_dias_con_gastos_en_mes()
        hoy = date.today()

        header = ft.Row([
            ft.IconButton(
                icon=Icons.CHEVRON_LEFT, icon_color="#38bdf8",
                on_click=self._mes_anterior, icon_size=18,
            ),
            ft.Text(
                f"{meses_nombres[self.current_month-1]} {self.current_year}",
                size=13, weight="bold", color="white",
                expand=True, text_align="center",
            ),
            ft.IconButton(
                icon=Icons.CHEVRON_RIGHT, icon_color="#38bdf8",
                on_click=self._mes_siguiente, icon_size=18,
            ),
        ], alignment="center")

        dias_semana = ["Lu","Ma","Mi","Ju","Vi","Sá","Do"]
        header_dias = ft.Row(
            [ft.Text(d, size=10, color="#64748b", width=30, text_align="center")
             for d in dias_semana],
            spacing=2,
        )

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        filas = []
        for semana in cal:
            celdas = []
            for dia_num in semana:
                if dia_num == 0:
                    celdas.append(ft.Container(width=30, height=30))
                    continue

                d = date(self.current_year, self.current_month, dia_num)
                es_hoy = d == hoy
                es_sel = d == self.selected_date
                tiene_gastos = dia_num in dias_con_gastos

                if es_sel:
                    bg, txt_color = "#38bdf8", "#0f172a"
                elif es_hoy:
                    bg, txt_color = "#1e3a5f", "#38bdf8"
                else:
                    bg, txt_color = "transparent", "white"

                punto = ft.Container(
                    width=4, height=4, border_radius=2,
                    bgcolor="#4ade80" if not es_sel else "#0f172a",
                ) if tiene_gastos else ft.Container()

                celda = ft.Container(
                    width=30, height=30,
                    border_radius=15,
                    bgcolor=bg,
                    on_click=lambda e, fecha=d: self._seleccionar_dia(fecha),
                    content=ft.Stack([
                        ft.Container(
                            content=ft.Text(
                                str(dia_num), size=12, color=txt_color,
                                weight="bold" if es_sel or es_hoy else "normal",
                                text_align="center",
                            ),
                        ),
                        ft.Container(
                            bottom=1, left=0, right=0,
                            content=ft.Row([punto], alignment="center"),
                        ),
                    ]),
                )
                celdas.append(celda)
            filas.append(ft.Row(celdas, spacing=2))

        self._cal_container.content = ft.Column(
            [header, header_dias] + filas,
            spacing=2,
        )

    def _build_controls(self):
        formulario = ft.Container(
            bgcolor="#1e293b",
            padding=30,
            border_radius=15,
            expand=True,
            content=ft.Column([
                ft.Text("Gestión de Gastos", size=24, weight="bold", color="white"),
                ft.Container(height=8),
                ft.Text("Registrar Nuevo Gasto", size=18, weight="bold", color="#38bdf8"),
                ft.Divider(color="#334155", height=20),
                self.input_concepto,
                ft.Container(height=10),
                self.input_monto,
                ft.Container(height=20),
                ft.ElevatedButton(
                    "GUARDAR GASTO",
                    icon=Icons.SAVE,
                    bgcolor="#38bdf8",
                    color="#0f172a",
                    height=48,
                    on_click=self._guardar_gasto,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    expand=True,
                ),
            ], horizontal_alignment="stretch"),
        )

        panel_calendario = ft.Container(
            bgcolor="#1e293b",
            padding=16,
            border_radius=15,
            width=255,
            content=ft.Column([
                ft.Text("Calendario de Gastos", size=14, weight="bold", color="white"),
                ft.Divider(color="#334155", height=10),
                self._cal_container,
                ft.Divider(color="#334155", height=10),
                self._gastos_dia_titulo,
                ft.Container(height=2),
                self._total_dia_text,
                ft.Container(height=6),
                ft.Container(
                    height=170,
                    content=self._gastos_dia_col,
                ),
            ], spacing=3),
        )

        return [
            ft.Container(expand=True, padding=20, content=formulario),
            ft.Container(
                width=275,
                padding=ft.padding.only(top=20, right=20, bottom=20),
                content=panel_calendario,
            ),
        ]