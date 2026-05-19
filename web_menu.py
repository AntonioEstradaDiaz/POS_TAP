import flet as ft
import threading
import time
from core.data_manager import DataManager

def main(page: ft.Page):
    page.title = "Menú Digital & Reseñas - POS TAP"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # Inicializamos el gestor de datos de la base de datos
    dm = DataManager()
    
    # Contenedor dinámico para las tarjetas de los platillos
    grid_productos = ft.ResponsiveRow(spacing=20, run_spacing=20)

    def cargar_menu_web(e=None):
        """Consulta el inventario actual de la BD y dibuja las tarjetas frescas."""
        # Si venimos del clic de un botón, mostramos un feedback visual rápido opcional
        grid_productos.controls.clear()
        
        inventario = dm.get_inventario()

        if not inventario:
            grid_productos.controls.append(
                ft.Container(
                    content=ft.Text("No hay platillos disponibles en el menú por el momento.", size=18, italic=True, color="#64748b"),
                    alignment=ft.alignment.center,
                    col=12
                )
            )
            page.update()
            return

        for nombre, info in inventario.items():
            precio = info["precio"]
            
            # Buscamos si tiene reseñas para calcular el promedio de estrellas
            promedio_estrellas = dm.get_promedio_calificacion(nombre)
            estrellas_texto = f"⭐ {promedio_estrellas}" if promedio_estrellas > 0 else "Sin reseñas"

            # Creamos la tarjeta visual para cada platillo
            tarjeta = ft.Container(
                content=ft.Column([
                    ft.Text(nombre, size=20, weight="bold", color="white"),
                    ft.Text(f"${precio:.2f}", size=18, color="#4ade80", weight="bold"),
                    ft.Row([
                        ft.Text(estrellas_texto, size=14, color="#fbbf24", weight="bold"),
                        ft.TextButton(
                            "Ver u opinar", 
                            icon="rate_review",
                            icon_color="#38bdf8",
                            on_click=lambda e, n=nombre: abrir_modal_resenas(n)
                        )
                    ], alignment="spaceBetween")
                ], spacing=10),
                padding=20,
                bgcolor="#1e293b",
                border_radius=12,
                border=ft.border.all(1, "#334155"),
                col={"sm": 12, "md": 6, "lg": 4}
            )
            grid_productos.controls.append(tarjeta)
        
        page.update()

    # ─────────────────────────────────────────────
    # LÓGICA DE RESEÑAS Y COMENTARIOS (MODAL)
    # ─────────────────────────────────────────────
    
    def abrir_modal_resenas(nombre_producto):
        lista_comentarios = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, height=200)
        
        dropdown_calif = ft.Dropdown(
            label="Calificación",
            width=120,
            options=[
                ft.dropdown.Option("5", "⭐⭐⭐⭐⭐"),
                ft.dropdown.Option("4", "⭐⭐⭐⭐"),
                ft.dropdown.Option("3", "⭐⭐⭐"),
                ft.dropdown.Option("2", "⭐⭐"),
                ft.dropdown.Option("1", "⭐"),
            ],
            value="5"
        )
        txt_comentario = ft.TextField(label="Deja tu opinión aquí...", expand=True, multiline=True)

        def cargar_comentarios_locales():
            lista_comentarios.controls.clear()
            resenas = dm.get_resenas_producto(nombre_producto)
            for r in resenas:
                estrellitas = "⭐" * r["calificacion"]
                lista_comentarios.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([ft.Text(estrellitas, color="#fbbf24", weight="bold"), ft.Text(r["fecha"], size=11, color="#64748b")]),
                            ft.Text(r["comentario"] if r["comentario"] else "(Sin comentario)", size=13, color="#e2e8f0")
                        ], spacing=3),
                        padding=10, bgcolor="#0f172a", border_radius=8
                    )
                )

        def guardar_comentario_evento(e):
            if not dropdown_calif.value:
                return
            
            dm.registrar_resena(
                producto=nombre_producto,
                calificacion=int(dropdown_calif.value),
                comentario=txt_comentario.value.strip()
            )
            txt_comentario.value = ""
            cargar_comentarios_locales()
            cargar_menu_web()

        cargar_comentarios_locales()

        dialogo = ft.AlertDialog(
            title=ft.Text(f"Reseñas de {nombre_producto}", size=18, weight="bold"),
            content=ft.Column([
                ft.Text("Comentarios de clientes:", size=14, weight="bold", color="#38bdf8"),
                lista_comentarios,
                ft.Divider(color="#334155"),
                ft.Text("Añadir tu reseña:", size=14, weight="bold", color="#38bdf8"),
                ft.Row([dropdown_calif, txt_comentario], alignment="top"),
                ft.ElevatedButton(
                    "Enviar Reseña", 
                    icon="send",  # <--- Cambiado a string plano en minúsculas
                    bgcolor="#38bdf8", 
                    color="#0f172a",
                    on_click=guardar_comentario_evento
                )
            ], tight=True, width=450),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: cerrar_modal(dialogo))]
        )
        
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    def cerrar_modal(modal):
        modal.open = False
        page.update()

    # ─────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA INTERFAZ WEB
    # ─────────────────────────────────────────────
    
    header = ft.Container(
        content=ft.Column([
            ft.Text("NUESTRO MENÚ DIGITAL", size=28, weight="bold", color="#38bdf8", text_align="center"),
            ft.Text("Consulta nuestros platillos en tiempo real y déjanos tu opinión", size=14, color="#94a3b8", text_align="center")
        ], horizontal_alignment="center"),
        margin=ft.margin.only(bottom=10, top=10)
    )

    # Botón flotante estilizado de refresco manual justo arriba de los productos
    btn_refrescar = ft.Row([
        ft.ElevatedButton(
            "Actualizar Menú",
            icon=ft.Icons.REFRESH,
            bgcolor="#1e293b",
            color="#38bdf8",
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, "#334155"),
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=cargar_menu_web # Al darle clic vuelve a consultar la Base de Datos
        )
    ], alignment="end")

    page.add(
        ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=10),
                grid_productos
            ]),
            width=1000,
            padding=10
        )
    )

    # Carga inicial al abrir el navegador por primera vez
    cargar_menu_web()
    def auto_refresh():
        while True:
            time.sleep(5)

            try:
                cargar_menu_web()
            except:
                pass


    page.run_thread(auto_refresh)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8050)