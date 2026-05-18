import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime


class CierreDiaView(ft.Container):
    """
    Vista de Cierre de Dia - FUNCIONAL
    Muestra resumen del día y permite guardar el cierre en la BD.
    """
    def __init__(self, dm):
        super().__init__(expand=True, padding=30)
        self.dm = dm

        # Obtener datos reales
        kpis = self.dm.get_kpis_y_graficos()
        v_hoy = kpis.get("ventas_hoy", 0.0)
        g_hoy = kpis.get("gastos_hoy", 0.0)
        ganancia = kpis.get("ganancia", 0.0)

        fecha_str = datetime.now().strftime("%d/%m/%Y")

        resumen = [
            {"titulo": "Ventas del Día",  "valor": f"${v_hoy:,.2f}", "icono": Icons.TRENDING_UP,           "color": "#4ade80"},
            {"titulo": "Gastos del Día",  "valor": f"${g_hoy:,.2f}", "icono": Icons.TRENDING_DOWN,          "color": "#f87171"},
            {"titulo": "Ganancia Neta",   "valor": f"${ganancia:,.2f}", "icono": Icons.ACCOUNT_BALANCE_WALLET, "color": "#38bdf8"},
        ]

        tarjetas = ft.Row([
            ft.Container(
                expand=1, bgcolor="#1e293b", border_radius=12, padding=20,
                content=ft.Row([
                    ft.Icon(r["icono"], size=38, color=r["color"]),
                    ft.Column([
                        ft.Text(r["titulo"], size=13, color="#64748b"),
                        ft.Text(r["valor"],  size=24, weight="bold", color="white"),
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
                    "Al presionar el botón se guardará el resumen del día en la Base de Datos.",
                    size=14, color="#94a3b8",
                ),
                ft.Container(height=16),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(Icons.NIGHTLIGHT, size=20),
                        ft.Text("Cerrar Día", weight="bold", size=16),
                    ], alignment="center", spacing=10),
                    bgcolor="#f59e0b",
                    color="#0f172a",
                    height=55,
                    width=220,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    on_click=self.handle_cerrar_dia
                ),
                ft.Container(height=12),
                ft.Text(
                    "Los datos se consolidan en la tabla 'cierres' para reportes históricos.",
                    size=12, color="#475569", italic=True
                ),
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

    def handle_cerrar_dia(self, e):
        # 1. Feedback visual inmediato
        btn = e.control
        btn.disabled = True
        btn.content = ft.Row([
            ft.ProgressRing(width=20, height=20, color="#0f172a", stroke_width=2),
            ft.Text(" Procesando...", weight="bold"),
        ], alignment="center", spacing=10)
        self.page.update()

        # 2. Ejecutar cierre
        resumen, destino = self.dm.cerrar_dia()

        # 3. Actualizar UI con éxito
        btn.content = ft.Row([
            ft.Icon(Icons.CHECK_CIRCLE_OUTLINE, size=20),
            ft.Text("Día Cerrado", weight="bold"),
        ], alignment="center", spacing=10)
        btn.bgcolor = "#4ade80" # Cambiar a verde
        
        # 4. Mostrar SnackBar robusto
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(Icons.CHECK, color="#1e293b"),
                ft.Text(f"¡Cierre guardado! Ventas: ${resumen['ventas']:,.2f}", color="#1e293b", weight="bold"),
            ]),
            bgcolor="#4ade80",
            duration=4000
        )
        self.page.snack_bar.open = True
        self.page.update()
