import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime
import threading
import time


class CierreDiaView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)
        self.main_page = page
        self.dm = data_manager

        fecha_str = datetime.now().strftime("%d/%m/%Y")

        # ── Textos animables ──
        self.txt_ventas   = ft.Text("$0.00", size=26, weight="bold", color="white")
        self.txt_gastos   = ft.Text("$0.00", size=26, weight="bold", color="white")
        self.txt_ganancia = ft.Text("$0.00", size=26, weight="bold", color="white")
        self.txt_ruta     = ft.Text(
            "El archivo se guardará en: data/cierres/YYYY-MM-DD.json",
            size=12, color="#475569", italic=True
        )

        resumen = [
            {"titulo": "Ventas del Día", "icono": Icons.TRENDING_UP,   "color": "#4ade80", "valor": self.txt_ventas},
            {"titulo": "Gastos del Día", "icono": Icons.TRENDING_DOWN,  "color": "#f87171", "valor": self.txt_gastos},
            {"titulo": "Ganancia Neta",  "icono": Icons.ACCOUNT_BALANCE_WALLET, "color": "#38bdf8", "valor": self.txt_ganancia},
        ]

        tarjetas = ft.Row([
            ft.Container(
                expand=1, bgcolor="#1e293b", border_radius=12, padding=22,
                content=ft.Row([
                    ft.Icon(r["icono"], size=40, color=r["color"]),
                    ft.Column([
                        ft.Text(r["titulo"], size=13, color="#64748b"),
                        r["valor"],
                    ], spacing=2)
                ], alignment="center")
            )
            for r in resumen
        ], alignment="spaceEvenly")

        zona_cierre = ft.Container(
            bgcolor="#1e293b",
            border_radius=12,
            padding=30,
            content=ft.Column([
                ft.Text(
                    "Al presionar el botón se calculará el resumen del día y se guardará como archivo JSON.",
                    size=14, color="#94a3b8",
                ),
                ft.Container(height=16),
                ft.ElevatedButton(
                    "🌙  Cerrar Día",
                    on_click=self._confirmar_cierre,
                    bgcolor="#f59e0b",
                    color="#0f172a",
                    height=55,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
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

    def did_mount(self):
        self._cargar_y_animar()

    def _cargar_y_animar(self):
        data = self.dm.get_kpis_y_graficos()
        threading.Thread(target=self._animar_contador,
                         args=(self.txt_ventas, data['ventas_hoy'], 0.8), daemon=True).start()
        threading.Thread(target=self._animar_contador,
                         args=(self.txt_gastos, data['gastos_hoy'], 0.8), daemon=True).start()
        threading.Thread(target=self._animar_contador,
                         args=(self.txt_ganancia, data['ganancia'], 1.0), daemon=True).start()

    def _animar_contador(self, control, valor_final, duracion=0.8):
        pasos = 30
        for i in range(pasos + 1):
            t = i / pasos
            t = 1 - pow(1 - t, 3)
            actual = valor_final * t
            control.value = f"${actual:.2f}"
            try:
                self.main_page.update()
            except Exception:
                pass
            time.sleep(duracion / pasos)

    def _confirmar_cierre(self, e):
        cierre = self.dm.get_cierre_hoy()
        if cierre:
            def on_dialog_click(e):
                if e.control.text == "Sí, sobreescribir":
                    self._ejecutar_cierre()
                dialog.open = False
                self.main_page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Cierre existente"),
                content=ft.Text("Hoy ya tiene un cierre registrado. ¿Deseas sobreescribirlo?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=on_dialog_click),
                    ft.ElevatedButton("Sí, sobreescribir", on_click=on_dialog_click,
                                      bgcolor="#f59e0b", color="#0f172a")
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.main_page.overlay.append(dialog)
            dialog.open = True
            self.main_page.update()
        else:
            self._ejecutar_cierre()

    def _ejecutar_cierre(self):
        resumen, ruta = self.dm.cerrar_dia()

        # Animar de nuevo hacia los nuevos valores (por si cambió entre entrada y cierre)
        threading.Thread(target=self._animar_contador,
                         args=(self.txt_ventas, resumen['ventas'], 0.6), daemon=True).start()
        threading.Thread(target=self._animar_contador,
                         args=(self.txt_gastos, resumen['gastos'], 0.6), daemon=True).start()
        threading.Thread(target=self._animar_contador,
                         args=(self.txt_ganancia, resumen['ganancia'], 0.8), daemon=True).start()

        self.txt_ruta.value = f"Respaldo guardado en: {ruta}"

        snack = ft.SnackBar(ft.Text("✅ Día cerrado y respaldado correctamente"), bgcolor="#166534")
        self.main_page.overlay.append(snack)
        snack.open = True
        self.update()
        self.main_page.update()