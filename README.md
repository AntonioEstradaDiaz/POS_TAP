# POS_TAP 🛒

Sistema de Punto de Venta (POS) desarrollado con **Python + Flet** como parte del taller de Tópicos Avanzados.

## 📋 Descripción

Aplicación de escritorio para la gestión de ventas, gastos y cierre de caja diario, con un dashboard analítico e historial de operaciones.
Incluye controles de calidad de datos para evitar capturas inválidas, ventas sin stock suficiente y correcciones destructivas del catálogo.

## 🗂️ Estructura del Proyecto

```
POS_TAP/
├── main.py                  # Punto de entrada y navegación principal
├── core/                    # Acceso a datos, validaciones y persistencia SQLite
├── data/                    # Base de datos SQLite local
└── views/
    ├── ventas_view.py       # Módulo de ventas
    ├── gastos_view.py       # Módulo de gastos
    ├── dashboard_view.py    # Dashboard con métricas
    ├── historial_view.py    # Historial de transacciones
    └── cierre_dia_view.py   # Cierre de día
```

## 🚀 Características

- 🛒 **Ventas** – Gestión de productos y carrito de compras
- ✅ **Validaciones** – Bloqueo de campos vacíos, importes inválidos, valores en cero/negativos y productos duplicados sin distinguir mayúsculas/minúsculas
- 📦 **Control de stock** – Bloqueo al agregar, incrementar o cobrar productos sin existencias suficientes
- ✏️ **Edición de productos** – Actualización de nombre, precio y stock desde el catálogo sin eliminar platillos
- 💸 **Gastos** – Registro de gastos del negocio
- 📊 **Dashboard** – Métricas y estadísticas en tiempo real
- 📜 **Historial** – Registro completo de transacciones
- 🌙 **Cierre de día** – Resumen y corte de caja

## ⚙️ Requisitos

- Python 3.10+
- Flet

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/POS_TAP.git
cd POS_TAP

# Instalar dependencias
pip install flet

# Ejecutar la aplicación
python main.py
```

## 🎨 Tecnologías

| Tecnología | Uso |
|---|---|
| Python | Lenguaje principal |
| Flet | Framework de interfaz gráfica |

## 🧩 Documentación de mejoras

- `MEJORAS_PROPUESTAS.md`: listado de mejoras detectadas y priorizadas.
- `MEJORA_IMPLEMENTADA.md`: descripción del proceso que implementa validaciones, bloqueo por stock y edición de productos.
- `BD.md`: documentación de la base de datos SQLite y reglas operativas aplicadas desde la capa de datos.

---

> **Tópicos Avanzados** – Proyecto Educativo 2026
