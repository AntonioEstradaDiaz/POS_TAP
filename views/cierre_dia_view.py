import flet as ft
from flet.controls.material.icons import Icons
from datetime import datetime
from core.data_manager import DataManager


class CierreDiaView(ft.Container):

    def __init__(self):
        super().__init__(expand=True, padding=30)

        self.data = DataManager()

        fecha_str = datetime.now().strftime("%d/%m/%Y")

        zona_cierre = ft.Container(

            bgcolor="#1e293b",
            border_radius=12,
            padding=30,

            content=ft.Column([

                ft.Text(
                    "Cerrar día y guardar resumen",
                    size=18,
                    color="white"
                ),

                ft.Container(height=20),

                ft.ElevatedButton(

                    "🌙 Cerrar Día",

                    on_click=self.ejecutar_cierre,

                    bgcolor="#f59e0b",
                    color="#0f172a",
                    height=55,

                ),

            ])

        )

        self.content = ft.Column([

            ft.Row([

                ft.Icon(
                    Icons.NIGHTLIGHT,
                    color="#f59e0b"
                ),

                ft.Text(
                    "Cerrar Día",
                    size=26,
                    weight="bold",
                    color="#f59e0b"
                ),

            ]),

            ft.Text(
                fecha_str,
                color="#64748b"
            ),

            ft.Container(height=30),

            zona_cierre,

        ])

    def ejecutar_cierre(self, e):

        try:

            print("ENTRO A LA FUNCION")

            resumen, ruta = self.data.cerrar_dia()

            print("CIERRE HECHO")

            snack = ft.SnackBar(

                content=ft.Text(
                    f"Cierre guardado correctamente\n{ruta}"
                ),

                bgcolor="#22c55e"

            )

            e.page.snack_bar = snack

            snack.open = True

            e.page.update()

        except Exception as error:

            print("ERROR EN CIERRE:")
            print(error)