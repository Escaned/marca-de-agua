"""
src/gui/theme.py
WatermarkStudio — Sistema de Temas y Estilos QSS (Obsidian / Dark Slate)
Basado en PyQt6 y sincronizado con el Sistema de Diseño oficial.
"""

# -----------------------------------------------------------------------------
# PALETA DE COLORES & TOKENS DE DISEÑO
# -----------------------------------------------------------------------------
COLORS = {
    # Fondos y superficies
    "bg_main": "#0f1016",
    "bg_canvas": "#14141c",
    "bg_panel": "#181824",
    "bg_surface_alt": "#161622",
    "bg_input": "#20202e",
    "bg_input_focus": "#242436",
    "bg_tab_inactive": "#12121c",
    "bg_button_tool": "#242436",
    "bg_button_hover": "#313148",

    # Bordes y separadores
    "border_subtle": "#28283a",
    "border_focus": "#3b82f6",
    "border_hover": "#60a5fa",

    # Colores semánticos de acción
    "primary_blue": "#2563eb",
    "primary_blue_hover": "#1d4ed8",
    "save_green": "#059669",
    "save_green_hover": "#047857",
    "accent_cyan": "#38bdf8",
    "accent_light_blue": "#60a5fa",
    "accent_pale_blue": "#93c5fd",
    "error_red": "#ef4444",

    # Tipografía
    "text_primary": "#e2e8f0",
    "text_heading": "#f8fafc",
    "text_muted": "#94a3b8",
    "text_dim": "#64748b",
}

# -----------------------------------------------------------------------------
# HOJA DE ESTILOS QSS COMPLETA (DARK THEME)
# -----------------------------------------------------------------------------
DARK_THEME_QSS = f"""
/* ==========================================================================
   Configuración Global de Ventana y Tipografía
   ========================================================================== */
QMainWindow, QDialog {{
    background-color: {COLORS["bg_main"]};
    color: {COLORS["text_primary"]};
}}

QWidget {{
    font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    font-size: 13px;
    color: {COLORS["text_primary"]};
    outline: none;
}}

/* ==========================================================================
   Barra de Menús y Menús Desplegables
   ========================================================================== */
QMenuBar {{
    background-color: {COLORS["bg_surface_alt"]};
    border-bottom: 1px solid {COLORS["border_subtle"]};
    padding: 2px 6px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    color: {COLORS["text_muted"]};
}}

QMenuBar::item:selected {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["accent_light_blue"]};
}}

QMenu {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["border_subtle"]};
    padding: 4px;
    border-radius: 6px;
}}

QMenu::item {{
    padding: 6px 24px 6px 16px;
    border-radius: 4px;
    color: {COLORS["text_primary"]};
}}

QMenu::item:selected {{
    background-color: {COLORS["primary_blue"]};
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS["border_subtle"]};
    margin: 4px 6px;
}}

/* ==========================================================================
   Paneles, Tarjetas (GroupBox), ScrollAreas y Splitters
   ========================================================================== */
QWidget#control_panel, QFrame#control_panel {{
    background-color: {COLORS["bg_panel"]};
    border-left: 1px solid {COLORS["border_subtle"]};
}}

QScrollArea {{
    background-color: {COLORS["bg_panel"]};
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background-color: {COLORS["bg_panel"]};
}}

QSplitter::handle {{
    background-color: {COLORS["border_subtle"]};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QGroupBox {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["border_subtle"]};
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 600;
    color: {COLORS["text_muted"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: {COLORS["accent_pale_blue"]};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ==========================================================================
   Campos de Texto, SpinBoxes y Selectores
   ========================================================================== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border_subtle"]};
    border-radius: 6px;
    padding: 6px 10px;
    color: {COLORS["text_heading"]};
    font-size: 12px;
    min-height: 20px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {COLORS["border_focus"]};
    background-color: {COLORS["bg_input_focus"]};
}}

QLineEdit:read-only {{
    background-color: {COLORS["bg_main"]};
    color: {COLORS["text_dim"]};
    border-style: dashed;
}}

/* Flechas y controles de SpinBox */
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS["bg_button_tool"]};
    border: none;
    width: 16px;
    border-radius: 2px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {COLORS["primary_blue"]};
}}

/* ComboBox Desplegable */
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["border_subtle"]};
    border-radius: 6px;
    selection-background-color: {COLORS["primary_blue"]};
    color: {COLORS["text_primary"]};
    padding: 4px;
}}

/* ==========================================================================
   Pestañas (Tabs de Texto y Logo)
   ========================================================================== */
QTabWidget::pane {{
    border: none;
    background: transparent;
    padding: 0;
}}

QTabBar {{
    background: transparent;
    qproperty-drawBase: 0;
}}

QTabBar::tab {{
    background: {COLORS["bg_tab_inactive"]};
    border: 1px solid {COLORS["border_subtle"]};
    color: {COLORS["text_muted"]};
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
    font-weight: 500;
}}

QTabBar::tab:hover {{
    color: {COLORS["text_primary"]};
    background: {COLORS["bg_panel"]};
}}

QTabBar::tab:selected {{
    background: {COLORS["bg_panel"]};
    color: {COLORS["accent_light_blue"]};
    border-bottom: 2px solid {COLORS["primary_blue"]};
    font-weight: 600;
}}

/* ==========================================================================
   Botones (Primarios, Secundarios y de Herramientas)
   ========================================================================== */
QPushButton {{
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}}

/* Botón Cargar */
QPushButton#btn_load {{
    background-color: {COLORS["primary_blue"]};
    color: #ffffff;
    border: none;
    font-weight: 600;
    min-height: 24px;
}}

QPushButton#btn_load:hover {{
    background-color: {COLORS["primary_blue_hover"]};
}}

/* Botón Guardar / Exportar */
QPushButton#btn_save, QPushButton#btn_export {{
    background-color: {COLORS["save_green"]};
    color: #ffffff;
    border: none;
    font-weight: 600;
    min-height: 24px;
}}

QPushButton#btn_save:hover, QPushButton#btn_export:hover {{
    background-color: {COLORS["save_green_hover"]};
}}

/* Botones de Estilo y Matriz (B, I, U, Grid 3x3) */
QPushButton.tool_btn {{
    background-color: {COLORS["bg_button_tool"]};
    border: 1px solid {COLORS["border_subtle"]};
    border-radius: 6px;
    color: {COLORS["text_primary"]};
    font-weight: 600;
    min-width: 28px;
    min-height: 28px;
}}

QPushButton.tool_btn:hover {{
    background-color: {COLORS["bg_button_hover"]};
    border-color: {COLORS["border_hover"]};
}}

QPushButton.tool_btn:checked {{
    background-color: {COLORS["primary_blue"]};
    border-color: {COLORS["accent_cyan"]};
    color: #ffffff;
}}

/* ==========================================================================
   Sliders Estilizados (Opacidad, Rotación, Escala)
   ========================================================================== */
QSlider::groove:horizontal {{
    height: 4px;
    background: {COLORS["border_subtle"]};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS["primary_blue"]};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLORS["accent_light_blue"]};
    border: 2px solid {COLORS["bg_main"]};
    width: 14px;
    height: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS["accent_pale_blue"]};
}}

/* ==========================================================================
   Barras de Desplazamiento (ScrollBars)
   ========================================================================== */
QScrollBar:vertical {{
    background: {COLORS["bg_panel"]};
    width: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border_subtle"]};
    min-height: 20px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["text_dim"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    height: 0;
}}

/* ==========================================================================
   Barra de Estado
   ========================================================================== */
QStatusBar {{
    background-color: {COLORS["bg_tab_inactive"]};
    border-top: 1px solid {COLORS["border_subtle"]};
    color: {COLORS["text_muted"]};
    font-size: 11px;
    padding: 3px 8px;
}}
"""
