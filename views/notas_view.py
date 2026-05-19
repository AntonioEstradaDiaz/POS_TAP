import flet as ft
import json
import os


class NotasView(ft.Container):
    def __init__(self, page):
        super().__init__(expand=True, padding=30)

        self.main_page = page
        self.archivo = "notas.json"
        self.notas = []

        self.input_nota = ft.TextField(
            hint_text="Escribe una nota...",
            expand=True,
            border_color="#38bdf8"
        )

        self.lista_notas = ft.Column(spacing=10, scroll="auto", expand=True)

        self._cargar_notas()

        self.content = ft.Column(
            [
                ft.Text(
                    "Notas Rápidas",
                    size=28,
                    weight="bold",
                    color="#38bdf8"
                ),

                ft.Container(height=20),

                ft.Row(
                    [
                        self.input_nota,

                        ft.ElevatedButton(
                            "Agregar",
                            icon=ft.Icons.ADD,
                            bgcolor="#38bdf8",
                            color="#0f172a",
                            on_click=self._agregar_nota
                        )
                    ]
                ),

                ft.Container(height=20),

                self.lista_notas
            ],
            expand=True
        )

        self._renderizar_notas()

    # -----------------------------------------
    # Guardar / cargar archivo JSON
    # -----------------------------------------
    def _guardar_archivo(self):
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(self.notas, f, ensure_ascii=False, indent=4)

    def _cargar_notas(self):
        if os.path.exists(self.archivo):
            with open(self.archivo, "r", encoding="utf-8") as f:
                self.notas = json.load(f)

    # -----------------------------------------
    # Agregar nota
    # -----------------------------------------
    def _agregar_nota(self, e):
        texto = self.input_nota.value.strip()

        if texto == "":
            return

        self.notas.append(texto)
        self.input_nota.value = ""

        self._guardar_archivo()
        self._renderizar_notas()
        self.update()

    # -----------------------------------------
    # Eliminar nota
    # -----------------------------------------
    def _eliminar_nota(self, index):
        del self.notas[index]
        self._guardar_archivo()
        self._renderizar_notas()
        self.update()

    # -----------------------------------------
    # Editar nota
    # -----------------------------------------
    def _editar_nota(self, index):
        self.input_nota.value = self.notas[index]
        del self.notas[index]

        self._guardar_archivo()
        self._renderizar_notas()
        self.update()

    # -----------------------------------------
    # Mostrar notas en pantalla
    # -----------------------------------------
    def _renderizar_notas(self):
        self.lista_notas.controls.clear()

        if not self.notas:
            self.lista_notas.controls.append(
                ft.Text(
                    "No hay notas guardadas.",
                    color="gray"
                )
            )
            return

        for i, nota in enumerate(self.notas):
            tarjeta = ft.Container(
                bgcolor="#1e293b",
                padding=15,
                border_radius=10,
                content=ft.Row(
                    [
                        ft.Text(
                            nota,
                            expand=True,
                            color="white"
                        ),

                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color="#38bdf8",
                            tooltip="Editar",
                            on_click=lambda e, x=i: self._editar_nota(x)
                        ),

                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color="#f87171",
                            tooltip="Eliminar",
                            on_click=lambda e, x=i: self._eliminar_nota(x)
                        )
                    ]
                )
            )

            self.lista_notas.controls.append(tarjeta)
