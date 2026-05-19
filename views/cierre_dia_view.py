import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime


class CierreDiaView(ft.Container):
    def __init__(self, page: ft.Page, dm, es_admin: bool = False):
        super().__init__(expand=True, padding=30)

        self.pg       = page
        self.dm       = dm
        self.es_admin = es_admin

        fecha_str     = datetime.now().strftime("%d/%m/%Y")
        fecha_archivo = datetime.now().strftime("%Y-%m-%d")

        # ── Datos reales del dia ──────────────────────────────────────
        kpis        = self.dm.get_kpis_y_graficos()
        ventas_hoy  = kpis.get("ventas_hoy", 0)
        gastos_hoy  = kpis.get("gastos_hoy", 0)
        ganancia    = kpis.get("ganancia",   0)

        # ── Textos actualizables ──────────────────────────────────────
        self.txt_ventas   = ft.Text(f"${ventas_hoy:.2f}",  size=24, weight="bold", color="white")
        self.txt_gastos   = ft.Text(f"${gastos_hoy:.2f}",  size=24, weight="bold", color="white")
        self.txt_ganancia = ft.Text(f"${ganancia:.2f}",    size=24, weight="bold", color="white")
        self.txt_ruta     = ft.Text(
            f"Se guardará en: data/cierres/{fecha_archivo}.json",
            size=12, color="#475569", italic=True
        )

        resumen = [
            {"titulo": "Ventas del Día",  "txt": self.txt_ventas,   "icono": Icons.TRENDING_UP,           "color": "#4ade80"},
            {"titulo": "Gastos del Día",  "txt": self.txt_gastos,   "icono": Icons.TRENDING_DOWN,          "color": "#f87171"},
            {"titulo": "Ganancia Neta",   "txt": self.txt_ganancia, "icono": Icons.ACCOUNT_BALANCE_WALLET, "color": "#38bdf8"},
        ]

        tarjetas = ft.Row([
            ft.Container(
                expand=1, bgcolor="#1e293b", border_radius=12, padding=20,
                content=ft.Row([
                    ft.Icon(r["icono"], size=38, color=r["color"]),
                    ft.Column([
                        ft.Text(r["titulo"], size=13, color="#64748b"),
                        r["txt"],
                    ], spacing=2)
                ], alignment="center")
            )
            for r in resumen
        ], alignment="spaceEvenly")

        # ── Boton ─────────────────────────────────────────────────────
        self.btn_cerrar = ft.ElevatedButton(
            "🌙  Cerrar Día",
            bgcolor="#f59e0b",
            color="#0f172a",
            height=55,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=self._confirmar_cierre,
        )

        zona_cierre = ft.Container(
            bgcolor="#1e293b", border_radius=12, padding=30,
            content=ft.Column([
                ft.Text(
                    "Se guardará el resumen del día en un archivo JSON y en la base de datos.",
                    size=14, color="#94a3b8",
                ),
                ft.Container(height=16),
                self.btn_cerrar,
                ft.Container(height=12),
                self.txt_ruta,
            ], horizontal_alignment="start")
        )

        self.content = ft.Column([
            ft.Row([
                ft.Icon(Icons.NIGHTLIGHT, color="#f59e0b", size=30),
                ft.Text("Cerrar Día", size=26, weight="bold", color="#f59e0b"),
            ], vertical_alignment="center"),
            ft.Text(fecha_str, size=14, color="#64748b"),
            ft.Container(height=20),
            tarjetas,
            ft.Container(height=30),
            zona_cierre,
        ], expand=True)

    # ── Dialogo ───────────────────────────────────────────────────────
    def _confirmar_cierre(self, e):
        self.dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Cerrar el día?"),
            content=ft.Text(
                "Se guardarán las ventas, gastos y ganancia del día.\n"
                "Esta acción no se puede deshacer.",
                color="#94a3b8"
            ),
            actions=[
                ft.TextButton("Cancelar",  on_click=self._cancelar),
                ft.ElevatedButton(
                    "Confirmar",
                    bgcolor="#f59e0b", color="#0f172a",
                    on_click=self._ejecutar_cierre,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if self.dlg not in self.pg.overlay:
            self.pg.overlay.append(self.dlg)
        self.dlg.open = True
        self.pg.update()

    def _cancelar(self, e):
        self.dlg.open = False
        self.pg.update()

    def _ejecutar_cierre(self, e):
        self.dlg.open = False
        self.pg.update()
        try:
            resumen, ruta = self.dm.cerrar_dia()

            self.txt_ventas.value   = f"${resumen['ventas']:.2f}"
            self.txt_gastos.value   = f"${resumen['gastos']:.2f}"
            self.txt_ganancia.value = f"${resumen['ganancia']:.2f}"
            self.txt_ruta.value     = f"Guardado en: {ruta}"
            self.txt_ruta.color     = "#4ade80"

            self.btn_cerrar.disabled = True
            self.btn_cerrar.text     = "✅  Día Cerrado"

            snack = ft.SnackBar(
                ft.Text(f"Día cerrado. Ganancia: ${resumen['ganancia']:.2f}"),
                bgcolor="#4ade80"
            )
            self.pg.overlay.append(snack)
            snack.open = True
            self.pg.update()

        except Exception as ex:
            snack = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="#f87171")
            self.pg.overlay.append(snack)
            snack.open = True
            self.pg.update()