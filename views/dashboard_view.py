import flet as ft
from flet.controls.material.icons import Icons
import threading
import time


BG_DARK  = "#0f172a"
BG_CARD  = "#1e293b"
BLUE     = "#38bdf8"
GREEN    = "#4ade80"
RED      = "#f87171"
GREY     = "#94a3b8"
DIVIDER  = "#334155"
SKELETON = "#263348"

# En lugar de mostrar pantalla vacia mientras cargan los datos, se muestran bloques grises (skeletons) de inmediato. El usuario siempre ve contenido desde el primer frame.
# Funcion auxiliar para crear bloques skeleton:

def _skeleton_box(width=None, height=16, radius=6):
    return ft.Container(width=width, height=height, bgcolor=SKELETON, border_radius=radius)


# Cache compartido entre navegaciones — persiste mientras la app esté abierta
_cache = {}


class DashboardView(ft.Container):
    def __init__(self, page, data_manager):
        super().__init__(expand=True, padding=30, bgcolor=BG_DARK)

        self.main_page     = page
        self.dm            = data_manager
        self._bar_controls = []

        self.txt_ventas   = ft.Text("—", size=26, weight="bold", color=GREY)
        self.txt_gastos   = ft.Text("—", size=26, weight="bold", color=GREY)
        self.txt_ganancia = ft.Text("—", size=26, weight="bold", color=GREY)

        self.tabla_top = ft.ListView(spacing=4, expand=True)
        self.historico_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.END,
            height=170, expand=True,
        )

        self.content = self._build_ui()
    
    # Carga con did_mount()
    # El dashboard usaba un thread con time.sleep(0.5) para esperar que el UI estuviera listo antes de cargar datos. 
    # Flet tiene un metodo nativo did_mount() que se ejecuta exactamente cuando el control ya esta montado en pantalla.
    # cache global para mostrar datos inmediatamente en próximas navegaciones sin esperar carga (si ya se cargaron una vez).
    # ── did_mount ─────────────────────────────────────────────────────────────
    def did_mount(self):
        if _cache:
            # Hay datos previos → mostrar INMEDIATAMENTE sin skeleton
            self._renderizar(_cache["data"], _cache["historico"], _cache["inventario"], animar=False)
            try:
                self.main_page.update()
            except Exception:
                pass
            # Refrescar en background silenciosamente
            threading.Thread(target=self._refrescar_silencioso, daemon=True).start()
        else:
            # Primera vez → skeleton + carga
            self._mostrar_skeleton_tabla()
            self._mostrar_skeleton_historico()
            try:
                self.main_page.update()
            except Exception:
                pass
            threading.Thread(target=self._cargar_datos_y_renderizar, daemon=True).start()

    # skeleton de la tabla top productos y del historico de ventas. 
    # Se muestran bloques grises en lugar de datos reales mientras se cargan los datos. 
    # El usuario ve contenido desde el primer frame, no una pantalla vacía.
    # ── Skeletons ─────────────────────────────────────────────────────────────
    def _mostrar_skeleton_tabla(self):
        self.tabla_top.controls.clear()
        for _ in range(6):
            self.tabla_top.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=11),
                    content=ft.Row([
                        ft.Container(expand=2, content=ft.Row([
                            _skeleton_box(22, 22, 11),
                            _skeleton_box(height=13),
                        ], spacing=8)),
                        _skeleton_box(40, 13),
                        _skeleton_box(55, 12),
                        _skeleton_box(70, 13),
                    ], spacing=12),
                )
            )
    # El skeleton del historico muestra barras grises de diferentes alturas, 
    # simulando el gráfico real que se renderizará una vez cargados los datos.
    def _mostrar_skeleton_historico(self):
        self.historico_row.controls.clear()
        for h in [40, 70, 55, 90, 35, 80, 60]:
            self.historico_row.controls.append(
                ft.Column([
                    _skeleton_box(26, 9),
                    ft.Container(height=4),
                    ft.Container(width=26, height=h, bgcolor=SKELETON,
                                 border_radius=ft.BorderRadius(4, 4, 0, 0)),
                    ft.Container(height=6),
                    _skeleton_box(26, 9),
                ], spacing=0, tight=True,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

    
    # ── Carga inicial (primera vez, con skeleton) ────────────────────────────
    def _cargar_datos_y_renderizar(self):
        data, historico, inventario = self._fetch_datos()
        # Guardar en cache para próximas navegaciones
        _cache["data"]       = data
        _cache["historico"]  = historico
        _cache["inventario"] = inventario
        self._renderizar(data, historico, inventario, animar=True)

    # ── Refresco silencioso (ya hay cache visible) ────────────────────────────
    def _refrescar_silencioso(self):
        data, historico, inventario = self._fetch_datos()
        _cache["data"]       = data
        _cache["historico"]  = historico
        _cache["inventario"] = inventario
        # Actualizar valores sin animación ni skeleton
        self._renderizar(data, historico, inventario, animar=False)
        try:
            self.main_page.update()
        except Exception:
            pass
    #Las 3 consultas a la base de datos se ejecutaban una tras otra.
    #Ahora corren en 2 threads simultaneos: 
    #el tiempo total es el de la consulta mas lenta, no la suma de todas.
    # ── Queries paralelas ─────────────────────────────────────────────────────
    def _fetch_datos(self):
        resultados = {}

        def fetch_kpis():
            resultados["data"]       = self.dm.get_kpis_y_graficos()
            resultados["inventario"] = self.dm.get_inventario()

        def fetch_historico():
            resultados["historico"] = self.dm.get_historico_7_dias()

        t1 = threading.Thread(target=fetch_kpis,      daemon=True)
        t2 = threading.Thread(target=fetch_historico, daemon=True)
        t1.start(); t2.start()
        t1.join();  t2.join()

        return resultados["data"], resultados["historico"], resultados["inventario"]

    # ── Render con o sin animación ────────────────────────────────────────────
    def _renderizar(self, data, historico, inventario, animar=True):
        ventas   = data["ventas_hoy"]
        gastos   = data["gastos_hoy"]
        ganancia = data.get("ganancia", ventas - gastos)

        self._construir_tabla_top(data, inventario)
        self._construir_historico(historico)
        # sirve para animar el conteo de los KPIs y la altura de las barras del histórico.
        # Si animar=False, se muestran los valores finales de inmediato sin animación (usado en refresco silencioso y cuando ya hay cache visible).
        # La animación suaviza la transición desde los skeletons a los datos reales, haciendo que los números cuenten hacia arriba y las barras crezcan progresivamente.
        if animar:
            pasos    = 25
            duracion = 0.55
            for i in range(pasos + 1):
                t = i / pasos
                t = 1 - pow(1 - t, 3)
                self.txt_ventas.value   = f"${ventas   * t:.2f}"
                self.txt_gastos.value   = f"${gastos   * t:.2f}"
                self.txt_ganancia.value = f"${ganancia * t:.2f}"
                if i == pasos:
                    self.txt_ventas.color   = GREEN
                    self.txt_gastos.color   = RED
                    self.txt_ganancia.color = BLUE
                for bc in self._bar_controls:
                    bc["barra"].height = int(6 + (bc["altura_final"] - 6) * t)
                try:
                    self.main_page.update()
                except Exception:
                    pass
                time.sleep(duracion / pasos)
        else:
            # Sin animación — valores finales directos
            self.txt_ventas.value   = f"${ventas:.2f}"
            self.txt_gastos.value   = f"${gastos:.2f}"
            self.txt_ganancia.value = f"${ganancia:.2f}"
            self.txt_ventas.color   = GREEN
            self.txt_gastos.color   = RED
            self.txt_ganancia.color = BLUE
            for bc in self._bar_controls:
                bc["barra"].height = bc["altura_final"]

    #La tabla de platillos construia cada fila con Container + Row + 4 Containers + Text anidados. 
    #Con 10 productos generaba mas de 100 controles que Flet serializaba uno a uno. 
    #Se reemplazo por ft.DataTable nativo que Flutter renderiza internamente de forma eficiente.
    # ── Tabla con DataTable nativo ───────────────────────────────────────────
    def _construir_tabla_top(self, data, inventario):
        self.tabla_top.controls.clear()
        top = data.get("top_productos", {})

        if not top:
            self.tabla_top.controls.append(
                ft.Container(
                    content=ft.Text("No hay ventas registradas hoy", color=GREY, size=14),
                    padding=20,
                )
            )
            try:
                self.tabla_top.update()
            except Exception:
                pass
            return

        filas = []
        for i, (prod, info) in enumerate(top.items(), 1):
            # info ahora es un dict con cantidad, precio, costo, ganancia_neta
            if isinstance(info, dict):
                cant         = info.get("cantidad", 0)
                precio       = info.get("precio", 0)
                costo        = info.get("costo", 0)
                ganancia_neta = info.get("ganancia_neta", 0)
            else:
                # compatibilidad si info viene como número (cant)
                cant          = info
                precio        = inventario.get(prod, {}).get("precio", 0)
                costo         = inventario.get(prod, {}).get("costo", 0)
                ganancia_neta = cant * (precio - costo)

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            filas.append(
                ft.DataRow(
                    color={"hovered": "#1a2744"},
                    cells=[
                        ft.DataCell(ft.Text(f"{medal}  {prod}", size=13, color="white")),
                        ft.DataCell(ft.Text(str(cant),              size=13, weight="bold", color=BLUE)),
                        ft.DataCell(ft.Text(f"${precio:.0f}",       size=12, color=GREY)),
                        ft.DataCell(ft.Text(f"${costo:.0f}",        size=12, color="#f59e0b")),
                        ft.DataCell(ft.Text(f"${ganancia_neta:.2f}", size=13, weight="bold", color=GREEN)),
                    ]
                )
            )

        self.tabla_top.controls.append(
            ft.DataTable(
                bgcolor="transparent",
                border_radius=8,
                column_spacing=20,
                heading_row_color=BG_DARK,
                heading_row_height=38,
                data_row_min_height=42,
                data_row_max_height=50,
                columns=[
                    ft.DataColumn(ft.Text("PLATILLO",        size=11, weight="bold", color="#64748b")),
                    ft.DataColumn(ft.Text("CANT.",           size=11, weight="bold", color="#64748b"), numeric=True),
                    ft.DataColumn(ft.Text("PRECIO",          size=11, weight="bold", color="#64748b"), numeric=True),
                    ft.DataColumn(ft.Text("COSTO",           size=11, weight="bold", color="#64748b"), numeric=True),
                    ft.DataColumn(ft.Text("GANANCIA NETA",   size=11, weight="bold", color="#64748b"), numeric=True),
                ],
                rows=filas,
            )
        )

        try:
            self.tabla_top.update()
        except Exception:
            pass

    # ── Histórico ─────────────────────────────────────────────────────────────
    def _construir_historico(self, historico):
        self.historico_row.controls.clear()
        self._bar_controls = []

        if not historico:
            self.historico_row.controls.append(
                ft.Container(expand=True, alignment=ft.Alignment(0, 0),
                             content=ft.Text("Sin datos históricos", color=GREY))
            )
            try:
                self.historico_row.update()
            except Exception:
                pass
            return

        max_v   = max(d["total"] for d in historico) or 1
        chart_h = 130

        for d in historico:
            altura_final = max(6, int((d["total"] / max_v) * chart_h))
            barra = ft.Container(
                width=26, height=6, bgcolor="#0ea5e9",
                border_radius=ft.BorderRadius(top_left=4, top_right=4,
                                              bottom_left=0, bottom_right=0),
            )
            self.historico_row.controls.append(
                ft.Column([
                    ft.Text(f"${d['total']:.0f}", size=9, color=BLUE,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=4),
                    barra,
                    ft.Container(height=6),
                    ft.Text(d["fecha"], size=9, color=GREY,
                            text_align=ft.TextAlign.CENTER),
                ], spacing=0, tight=True,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
            self._bar_controls.append({"barra": barra, "altura_final": altura_final})

        try:
            self.historico_row.update()
        except Exception:
            pass

    # ── UI estática ───────────────────────────────────────────────────────────
    def _build_ui(self):
    # La sección de KPIs se construye con tarjetas personalizadas que muestran un ícono, el título y el valor.
    # Se reemplazó el diseño original por un Row con tarjetas más compactas y visuales, usando colores e íconos para diferenciar cada KPI.
    # Cada tarjeta se construye con un método auxiliar _kpi_card() que recibe el título, el control de texto para el valor, el ícono y el color. 
    # Esto hace que el código sea más limpio y fácil de mantener.
        kpis = ft.Row([
            self._kpi_card("Ventas Hoy", self.txt_ventas,   Icons.TRENDING_UP,           GREEN),
            self._kpi_card("Gastos Hoy", self.txt_gastos,   Icons.TRENDING_DOWN,          RED),
            self._kpi_card("Ganancia",   self.txt_ganancia, Icons.ACCOUNT_BALANCE_WALLET, BLUE),
        ], alignment=ft.MainAxisAlignment.START, spacing=16)

        panel_tabla = ft.Container(
            expand=True, bgcolor=BG_CARD, padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("Top Productos - Estadísticas", size=18, weight="bold", color="white"),
                ft.Divider(color=DIVIDER),
                ft.Container(expand=True, content=self.tabla_top),
            ], spacing=6, expand=True),
        )

        panel_historico = ft.Container(
            expand=True, bgcolor=BG_CARD, padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("Ventas - Últimos 7 Días", size=18, weight="bold", color="white"),
                ft.Divider(color=DIVIDER),
                ft.Container(height=200, alignment=ft.Alignment(0, 0),
                             content=self.historico_row),
            ], spacing=6, expand=True),
        )

        return ft.Column([
            ft.Text("Dashboard & Analíticas", size=28, weight="bold", color=BLUE),
            ft.Container(height=20),
            kpis,
            ft.Container(height=25),
            ft.Row([panel_tabla, ft.Container(width=20), panel_historico],
                   expand=True, spacing=0),
        ], expand=True, spacing=0)

    def _kpi_card(self, titulo, valor_control, icono, color):
        return ft.Container(
            width=260, bgcolor=BG_CARD, padding=22, border_radius=12,
            content=ft.Row([
                ft.Icon(icono, size=42, color=color),
                ft.Column([
                    ft.Text(titulo, size=14, color=GREY),
                    valor_control,
                ], spacing=4, expand=True),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )