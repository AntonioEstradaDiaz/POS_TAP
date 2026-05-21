import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime


class CierreDiaView(ft.Container):
    """
    Vista de Cierre de Dia - SOLO ESTRUCTURA DE INTERFAZ
    Sin datos ni logica funcional. Valores en cero.
    """
    def __init__(self):
        super().__init__(expand=True, padding=30)

        fecha_str = datetime.now().strftime("%d/%m/%Y")

        resumen = [
            {"titulo": "Ventas del Día",  "valor": "$0.00", "icono": Icons.TRENDING_UP,           "color": "#4ade80"},
            {"titulo": "Gastos del Día",  "valor": "$0.00", "icono": Icons.TRENDING_DOWN,          "color": "#f87171"},
            {"titulo": "Ganancia Neta",   "valor": "$0.00", "icono": Icons.ACCOUNT_BALANCE_WALLET, "color": "#38bdf8"},
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
                    "Al presionar el botón se guardaría el resumen del día como archivo JSON.",
                    size=14, color="#94a3b8",
                ),
                ft.Container(height=16),
                ft.ElevatedButton(
                    "🌙  Cerrar Día",
                    bgcolor="#f59e0b",
                    color="#0f172a",
                    height=55,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.Container(height=12),
                ft.Text(
                    "El archivo se guardaría en: data/cierres/YYYY-MM-DD.json",
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
