import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime


class GastosView(ft.Container):
    """
    Vista de Gastos - Gestión y análisis financiero.
    """

    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30)

        self.main_page = page
        self.dm = data_manager

        # ─────────────────────────────────────
        # INPUTS
        # ─────────────────────────────────────

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

        self.content = self._build_ui()

    # ─────────────────────────────────────
    # GUARDAR GASTO
    # ─────────────────────────────────────

    def _guardar_gasto(self, e):

        if not self.input_concepto.value or not self.input_monto.value:

            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ Por favor, llena ambos campos"),
                bgcolor=ft.Colors.ORANGE_800
            )

            self.main_page.snack_bar.open = True
            self.main_page.update()

            return

        try:

            monto = float(self.input_monto.value)

        except ValueError:

            self.main_page.snack_bar = ft.SnackBar(
                ft.Text("⚠ El monto debe ser un número válido"),
                bgcolor=ft.Colors.RED_700
            )

            self.main_page.snack_bar.open = True
            self.main_page.update()

            return

        # Guardar en SQLite

        concepto = self.input_concepto.value.strip().lower()

        self.dm.registrar_gasto(
            concepto,
            monto
        )

        # Limpiar inputs
        self.input_concepto.value = ""
        self.input_monto.value = ""

        # Refrescar interfaz
        self.content = self._build_ui()

        self.main_page.snack_bar = ft.SnackBar(
            ft.Text("✅ Gasto registrado exitosamente"),
            bgcolor=ft.Colors.GREEN_700
        )

        self.main_page.snack_bar.open = True

        self.update()

    # ─────────────────────────────────────
    # INTERFAZ
    # ─────────────────────────────────────

    def _build_ui(self):

        # ====================================
        # DATOS FINANCIEROS
        # ====================================

        data = self.dm.get_kpis_y_graficos()

        ventas = data["ventas_hoy"]
        gastos = data["gastos_hoy"]

        porcentaje = 0
        # Se implemento un calculo automatico para determinar que porcentuaje de las ventas corresponde alos gastos del dia.
        if ventas > 0:
            porcentaje = (gastos / ventas) * 100

        # ====================================
        # SEMÁFORO FINANCIERO : se implemento un sistema de alertas utilizando colores para representar el estado  financiero del negocio
        # ====================================

        if porcentaje >= 70:

            color_estado = "#ef4444"

            mensaje_estado = (
                "🔴 Advertencia:\n"
                "Los gastos del día superan el 70% de las ventas."
            )

            analisis = (
                "Los gastos son elevados y podrían "
                "generar pérdidas financieras."
            )

        elif porcentaje >= 50:

            color_estado = "#facc15"

            mensaje_estado = (
                "🟡 Precaución:\n"
                "Los gastos representan más del 50% de las ventas."
            )

            analisis = (
                "Se recomienda monitorear los gastos "
                "para evitar reducción de ganancias."
            )

        else:

            color_estado = "#22c55e"

            mensaje_estado = (
                "🟢 Gastos bajo control."
            )

            analisis = (
                "Las finanzas del día son estables y "
                "los gastos se mantienen controlados."
            )
            
        # ====================================
        # GRÁFICA DE GASTOS: se obtuvo informacion de los gastos agrupados por concepto para generar graficas dinamicas.
        # ====================================

        gastos_concepto = self.dm.get_gastos_por_concepto()

        max_gasto = max(
            [g["total"] for g in gastos_concepto],
            default=1
        )
        
        #se creo una graica visual utilizando componentes de let para representar los gastos de forma dinamica.
        grafica = ft.Column(

            spacing=10,

            controls=[

                ft.Row([

                    ft.Container(

                        content=ft.Text(
                            gasto["concepto"],
                            color="white",
                            size=14
                        ),

                        width=120

                    ),

                    ft.Container(
                        # Escalado automatico de barras: se calculo el tamaño proporcional de cara segun el monto del gasto registrado.
                        width=max(
                            20,
                            int((gasto["total"] / max_gasto) * 220)
                        ),

                        height=24,

                        bgcolor="#ef4444",

                        border_radius=6

                    ),

                    ft.Text(
                        f" ${gasto['total']:.2f}",
                        color="#f87171"
                    )

                ])

                for gasto in gastos_concepto

            ] if gastos_concepto else [

                ft.Text(
                    "No hay gastos registrados hoy.",
                    color="grey"
                )

            ]

        )

        # ====================================
        # FORMULARIO dinamico para registro de gastos conectado a SQLite mediante DataManager.
        # ====================================

        formulario = ft.Container(

            bgcolor="#1e293b",

            padding=40,

            border_radius=15,

            content=ft.Column([

                ft.Text(
                    "Registrar Nuevo Gasto",
                    size=22,
                    weight="bold",
                    color="#38bdf8"
                ),

                ft.Divider(
                    color="#334155",
                    height=25
                ),

                self.input_concepto,

                ft.Container(height=12),
                # Campo para ingresar el monto del gasto 
                self.input_monto,

                ft.Container(height=24),
                # Boton para guardar gastos y actualizar analisis financiero.
                ft.ElevatedButton(

                    "GUARDAR GASTO",

                    icon=Icons.SAVE,

                    bgcolor="#38bdf8",

                    color="#0f172a",

                    height=50,

                    width=400,

                    on_click=self._guardar_gasto,

                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )

                ),

            ],

            horizontal_alignment="center")

        )

        # ====================================
        # PANEL FINANCIERO : muestra el analisis visual y estado financiero del negocio en tiempo real
        # ====================================

        panel_financiero = ft.Container(

            bgcolor="#1e293b",

            padding=25,

            border_radius=15,

            width=500,

            content=ft.Column([

                ft.Text(
                    "📊 Análisis Financiero",
                    size=22,
                    weight="bold",
                    color="white"
                ),

                ft.Container(height=10),
                # Muestra el total de gastos del dia 
                ft.Text(
                    f"Gastos del día: ${gastos:.2f}",
                    size=18,
                    color="#f87171"
                ),
                # Muestra el total de ventas del dia 
                ft.Text(
                    f"Ventas del día: ${ventas:.2f}",
                    size=18,
                    color="#4ade80"
                ),

                ft.Container(height=15),

                ft.Text(
                    f"Los gastos representan el {porcentaje:.1f}% de las ventas del día.",
                    size=16,
                    color="white"
                ),

                ft.Container(height=10),
                # Grafica dinamica de gastos por concepto
                grafica,

                ft.Container(height=15),
                # Muestra el estado del semaforo financiero 
                ft.Text(
                    mensaje_estado,
                    size=16,
                    color=color_estado,
                    weight="bold"
                ),

                ft.Container(height=10),
                # Muestra interpretacion financiera automatica
                ft.Text(
                    analisis,
                    size=14,
                    color="#cbd5e1",
                    italic=True
                ),

            ])

        )

        # ====================================
        # VISTA COMPLETA : integra el formulario y el panel financiero dentro de la interaz 
        # ====================================

        return ft.Column([

            ft.Text(
                "Gestión de Gastos",
                size=28,
                weight="bold",
                color="white"
            ),

            ft.Container(height=30),
            # Organizacion horizontal de componentes 
            ft.Row(

                [
                    # Formulario de registro de gastos 
                    formulario,

                    ft.Container(width=30),
                    # Panel de analisis financiero y graficas
                    panel_financiero,

                ],

                alignment="center"

            ),

        ],

        expand=True)