import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSlider, QSpinBox,
    QTabWidget, QColorDialog, QFileDialog, QGridLayout,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from typing import Dict, Any, Tuple
from ..core.font_loader import get_system_fonts

class ColorButton(QPushButton):
    """Botón compacto con muestra de color y diálogo selector."""
    color_changed = pyqtSignal(tuple)

    def __init__(self, initial_color: Tuple[int, int, int] = (255, 255, 255), label: str = "Color", parent=None):
        super().__init__(parent)
        self.current_color = initial_color
        self.label_prefix = label
        self.clicked.connect(self.choose_color)
        self.setFixedHeight(26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()

    def update_style(self):
        r, g, b = self.current_color
        # Color del texto según luminancia para máxima legibilidad
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        text_color = "#0f172a" if luminance > 140 else "#f8fafc"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r}, {g}, {b});
                color: {text_color};
                border: 1px solid #64748b;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                border: 2px solid #60a5fa;
            }}
        """)
        self.setText(f"🎨 {self.label_prefix}")

    def choose_color(self):
        initial = QColor(*self.current_color)
        color = QColorDialog.getColor(initial, self, "Seleccionar Color de Letra")
        if color.isValid():
            self.current_color = (color.red(), color.green(), color.blue())
            self.update_style()
            self.color_changed.emit(self.current_color)

    def set_color(self, rgb: Tuple[int, int, int]):
        self.current_color = rgb
        self.update_style()


class ControlPanel(QWidget):
    """
    Panel de control ultra-compacto y todo-en-uno: 100% visible a simple vista sin scroll.
    """
    config_changed = pyqtSignal(dict)
    open_image_requested = pyqtSignal()
    save_image_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fonts_map = get_system_fonts()
        self.preset_position = "bottom_right"
        self.custom_pos_x = 20
        self.custom_pos_y = 20
        self.is_custom_position = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 1. BOTONES PRINCIPALES (CARGAR / GUARDAR)
        actions_box = QHBoxLayout()
        actions_box.setSpacing(4)

        self.btn_open = QPushButton("📂 Cargar")
        self.btn_open.setFixedHeight(28)
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.btn_open.clicked.connect(self.open_image_requested.emit)

        self.btn_save = QPushButton("💾 Guardar")
        self.btn_save.setFixedHeight(28)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_save.clicked.connect(self.save_image_requested.emit)

        actions_box.addWidget(self.btn_open)
        actions_box.addWidget(self.btn_save)
        layout.addLayout(actions_box)

        # 2. PESTAÑAS: TEXTO vs LOGO
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_text_tab(), "✍️ Texto")
        self.tabs.addTab(self.create_logo_tab(), "🖼️ Logo")
        self.tabs.currentChanged.connect(self.emit_config)
        layout.addWidget(self.tabs)

        # 3. SECCIÓN: ESTILO (OPACIDAD Y ROTACIÓN EN FILAS COMPACTAS)
        style_box = QFrame()
        style_box.setStyleSheet("background-color: #181824; border: 1px solid #28283a; border-radius: 5px; padding: 4px;")
        style_layout = QVBoxLayout(style_box)
        style_layout.setContentsMargins(4, 4, 4, 4)
        style_layout.setSpacing(4)

        # Opacidad
        op_row = QHBoxLayout()
        op_row.setSpacing(4)
        lbl_op = QLabel("Opacidad:")
        lbl_op.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: bold;")
        self.lbl_opacity_val = QLabel("80%")
        self.lbl_opacity_val.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: bold;")
        
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(80)
        self.slider_opacity.valueChanged.connect(self.on_opacity_slider_changed)

        op_row.addWidget(lbl_op)
        op_row.addWidget(self.slider_opacity)
        op_row.addWidget(self.lbl_opacity_val)
        style_layout.addLayout(op_row)

        # Rotación
        rot_row = QHBoxLayout()
        rot_row.setSpacing(4)
        lbl_rot = QLabel("Rotación:")
        lbl_rot.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: bold;")
        self.lbl_rotation_val = QLabel("0°")
        self.lbl_rotation_val.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: bold;")

        self.slider_rotation = QSlider(Qt.Orientation.Horizontal)
        self.slider_rotation.setRange(-180, 180)
        self.slider_rotation.setValue(0)
        self.slider_rotation.valueChanged.connect(self.on_rotation_slider_changed)

        btn_reset_rot = QPushButton("0°")
        btn_reset_rot.setFixedSize(22, 20)
        btn_reset_rot.setStyleSheet("background: #334155; color: white; border-radius: 2px; font-size: 9px;")
        btn_reset_rot.clicked.connect(lambda: self.slider_rotation.setValue(0))

        rot_row.addWidget(lbl_rot)
        rot_row.addWidget(self.slider_rotation)
        rot_row.addWidget(self.lbl_rotation_val)
        rot_row.addWidget(btn_reset_rot)
        style_layout.addLayout(rot_row)

        layout.addWidget(style_box)

        # 4. SECCIÓN: POSICIÓN (3x3 + MÁRGENES)
        pos_box = QFrame()
        pos_box.setStyleSheet("background-color: #181824; border: 1px solid #28283a; border-radius: 5px; padding: 4px;")
        pos_layout = QVBoxLayout(pos_box)
        pos_layout.setContentsMargins(4, 4, 4, 4)
        pos_layout.setSpacing(4)

        pos_header = QHBoxLayout()
        lbl_pos_title = QLabel("Posición:")
        lbl_pos_title.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: bold;")
        self.lbl_pos_status = QLabel("Abajo Der")
        self.lbl_pos_status.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: bold;")
        pos_header.addWidget(lbl_pos_title)
        pos_header.addWidget(self.lbl_pos_status, alignment=Qt.AlignmentFlag.AlignRight)
        pos_layout.addLayout(pos_header)

        # Matriz 3x3
        grid = QGridLayout()
        grid.setSpacing(2)
        presets = [
            ("top_left", "↖", "Arriba Izq", 0, 0), ("top_center", "↑", "Arriba Centro", 0, 1), ("top_right", "↗", "Arriba Der", 0, 2),
            ("center_left", "←", "Centro Izq", 1, 0), ("center", "•", "Centro", 1, 1), ("center_right", "→", "Centro Der", 1, 2),
            ("bottom_left", "↙", "Abajo Izq", 2, 0), ("bottom_center", "↓", "Abajo Centro", 2, 1), ("bottom_right", "↘", "Abajo Der", 2, 2)
        ]

        self.preset_buttons = {}
        for key, text, tooltip, row, col in presets:
            btn = QPushButton(text)
            btn.setFixedHeight(22)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #242436;
                    color: #cbd5e1;
                    border: 1px solid #3b3b52;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #313148; border-color: #60a5fa; }
                QPushButton:checked { background-color: #2563eb; color: white; border-color: #60a5fa; }
            """)
            btn.clicked.connect(lambda checked, k=key: self.set_preset(k))
            grid.addWidget(btn, row, col)
            self.preset_buttons[key] = btn

        self.preset_buttons["bottom_right"].setChecked(True)
        pos_layout.addLayout(grid)

        # Márgenes X / Y
        margins_row = QHBoxLayout()
        margins_row.setSpacing(2)
        
        lbl_mx = QLabel("X:")
        lbl_mx.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.spin_margin_x = QSpinBox()
        self.spin_margin_x.setRange(0, 800)
        self.spin_margin_x.setValue(30)
        self.spin_margin_x.setSuffix("px")
        self.spin_margin_x.setFixedHeight(22)
        self.spin_margin_x.valueChanged.connect(self.emit_config)

        lbl_my = QLabel(" Y:")
        lbl_my.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.spin_margin_y = QSpinBox()
        self.spin_margin_y.setRange(0, 800)
        self.spin_margin_y.setValue(30)
        self.spin_margin_y.setSuffix("px")
        self.spin_margin_y.setFixedHeight(22)
        self.spin_margin_y.valueChanged.connect(self.emit_config)

        margins_row.addWidget(lbl_mx)
        margins_row.addWidget(self.spin_margin_x)
        margins_row.addWidget(lbl_my)
        margins_row.addWidget(self.spin_margin_y)
        pos_layout.addLayout(margins_row)

        layout.addWidget(pos_box)
        layout.addStretch()

    def create_text_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 4, 2, 2)
        layout.setSpacing(5)

        # 1. Campo de texto
        self.txt_watermark = QLineEdit("© Mi Marca de Agua")
        self.txt_watermark.setFixedHeight(26)
        self.txt_watermark.setPlaceholderText("Escribe el texto...")
        self.txt_watermark.textChanged.connect(self.emit_config)
        layout.addWidget(self.txt_watermark)

        # 2. Selección de Fuente
        self.combo_font = QComboBox()
        self.combo_font.setEditable(True)
        self.combo_font.setFixedHeight(26)
        self.combo_font.setMaxVisibleItems(15)

        default_index = 0
        for i, (name, path) in enumerate(self.fonts_map.items()):
            self.combo_font.addItem(name, path)
            if name.lower() in ['arial', 'segoe ui', 'calibri', 'helvetica', 'verdana']:
                default_index = i

        if self.combo_font.count() > 0:
            self.combo_font.setCurrentIndex(default_index)

        self.combo_font.currentIndexChanged.connect(self.emit_config)
        layout.addWidget(self.combo_font)

        # 3. Fila de Color y Formato (Color, Negrita, Cursiva, Subrayado)
        format_row = QHBoxLayout()
        format_row.setSpacing(4)

        # Botón de selección de color
        self.btn_text_color = ColorButton((255, 255, 255), label="Color")
        self.btn_text_color.setFixedHeight(26)
        self.btn_text_color.setToolTip("Elegir color de la letra")
        self.btn_text_color.color_changed.connect(lambda _: self.emit_config())

        # Botón Negrita (Bold)
        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(28, 26)
        self.btn_bold.setToolTip("Negrita (Bold)")
        self.btn_bold.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bold.setStyleSheet("""
            QPushButton {
                background-color: #242436;
                color: #cbd5e1;
                border: 1px solid #3b3b52;
                border-radius: 3px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #313148; border-color: #60a5fa; }
            QPushButton:checked { background-color: #2563eb; color: white; border-color: #60a5fa; }
        """)
        self.btn_bold.clicked.connect(self.emit_config)

        # Botón Cursiva (Italic)
        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(28, 26)
        self.btn_italic.setToolTip("Cursiva (Italic)")
        self.btn_italic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_italic.setStyleSheet("""
            QPushButton {
                background-color: #242436;
                color: #cbd5e1;
                border: 1px solid #3b3b52;
                border-radius: 3px;
                font-style: italic;
                font-weight: bold;
                font-family: 'Times New Roman', serif;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #313148; border-color: #60a5fa; }
            QPushButton:checked { background-color: #2563eb; color: white; border-color: #60a5fa; }
        """)
        self.btn_italic.clicked.connect(self.emit_config)

        # Botón Subrayado (Underline)
        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(28, 26)
        self.btn_underline.setToolTip("Subrayado (Underline)")
        self.btn_underline.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_underline.setStyleSheet("""
            QPushButton {
                background-color: #242436;
                color: #cbd5e1;
                border: 1px solid #3b3b52;
                border-radius: 3px;
                text-decoration: underline;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #313148; border-color: #60a5fa; }
            QPushButton:checked { background-color: #2563eb; color: white; border-color: #60a5fa; }
        """)
        self.btn_underline.clicked.connect(self.emit_config)

        format_row.addWidget(self.btn_text_color, 1)
        format_row.addWidget(self.btn_bold)
        format_row.addWidget(self.btn_italic)
        format_row.addWidget(self.btn_underline)
        layout.addLayout(format_row)

        # Tamaño con Slider y +/-
        size_row = QHBoxLayout()
        size_row.setSpacing(3)
        lbl_sz = QLabel("Tam:")
        lbl_sz.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: bold;")
        
        btn_dec = QPushButton("➖")
        btn_dec.setFixedSize(20, 20)
        btn_dec.setStyleSheet("background: #334155; color: white; border-radius: 2px; font-size: 8px;")
        btn_dec.clicked.connect(self.decrease_font_size)

        self.slider_font_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_font_size.setRange(8, 300)
        self.slider_font_size.setValue(52)
        self.slider_font_size.valueChanged.connect(self.on_font_size_changed)

        btn_inc = QPushButton("➕")
        btn_inc.setFixedSize(20, 20)
        btn_inc.setStyleSheet("background: #334155; color: white; border-radius: 2px; font-size: 8px;")
        btn_inc.clicked.connect(self.increase_font_size)

        self.lbl_font_size_val = QLabel("52")
        self.lbl_font_size_val.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: bold; min-width: 22px;")

        size_row.addWidget(lbl_sz)
        size_row.addWidget(btn_dec)
        size_row.addWidget(self.slider_font_size)
        size_row.addWidget(btn_inc)
        size_row.addWidget(self.lbl_font_size_val)
        layout.addLayout(size_row)

        return widget

    def decrease_font_size(self):
        new_val = max(8, self.slider_font_size.value() - 2)
        self.slider_font_size.setValue(new_val)

    def increase_font_size(self):
        new_val = min(300, self.slider_font_size.value() + 2)
        self.slider_font_size.setValue(new_val)

    def on_font_size_changed(self, value: int):
        self.lbl_font_size_val.setText(str(value))
        self.emit_config()

    def create_logo_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 4, 2, 2)
        layout.setSpacing(5)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(3)
        self.txt_logo_path = QLineEdit()
        self.txt_logo_path.setFixedHeight(26)
        self.txt_logo_path.setPlaceholderText("Logo PNG/JPG...")
        self.txt_logo_path.setReadOnly(True)

        btn_browse_logo = QPushButton("...")
        btn_browse_logo.setFixedSize(26, 26)
        btn_browse_logo.setStyleSheet("background: #334155; color: white; border-radius: 3px; font-weight: bold;")
        btn_browse_logo.clicked.connect(self.browse_logo_file)

        logo_row.addWidget(self.txt_logo_path)
        logo_row.addWidget(btn_browse_logo)
        layout.addLayout(logo_row)

        scale_row = QHBoxLayout()
        scale_row.setSpacing(3)
        lbl_sc = QLabel("Escala:")
        lbl_sc.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: bold;")

        self.slider_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_scale.setRange(1, 100)
        self.slider_scale.setValue(20)
        self.slider_scale.valueChanged.connect(self.on_scale_changed)

        self.lbl_scale_val = QLabel("20%")
        self.lbl_scale_val.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: bold; min-width: 28px;")

        scale_row.addWidget(lbl_sc)
        scale_row.addWidget(self.slider_scale)
        scale_row.addWidget(self.lbl_scale_val)
        layout.addLayout(scale_row)

        return widget

    def on_scale_changed(self, value: int):
        self.lbl_scale_val.setText(f"{value}%")
        self.emit_config()

    def browse_logo_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Logo", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp *.tif);;Todos los archivos (*.*)"
        )
        if file_path:
            self.txt_logo_path.setText(file_path)
            self.emit_config()

    def set_preset(self, key: str):
        self.preset_position = key
        self.is_custom_position = False
        readable_name = key.replace('_', ' ').title()
        self.lbl_pos_status.setText(readable_name)
        for k, btn in self.preset_buttons.items():
            btn.setChecked(k == key)
        self.emit_config()

    def set_custom_drag_position(self, pos_x: float, pos_y: float):
        self.preset_position = "custom"
        self.is_custom_position = True
        self.custom_pos_x = int(pos_x)
        self.custom_pos_y = int(pos_y)
        self.lbl_pos_status.setText(f"Libre ({self.custom_pos_x},{self.custom_pos_y})")
        for btn in self.preset_buttons.values():
            btn.setChecked(False)

    def on_opacity_slider_changed(self, value: int):
        self.lbl_opacity_val.setText(f"{value}%")
        self.emit_config()

    def on_rotation_slider_changed(self, value: int):
        self.lbl_rotation_val.setText(f"{value}°")
        self.emit_config()

    def get_current_config(self) -> Dict[str, Any]:
        mode = "text" if self.tabs.currentIndex() == 0 else "logo"
        font_path = self.combo_font.currentData() or ""

        return {
            "mode": mode,
            "text": self.txt_watermark.text(),
            "font_path": font_path,
            "font_size": self.slider_font_size.value(),
            "color": self.btn_text_color.current_color,
            "is_bold": getattr(self, "btn_bold", None).isChecked() if hasattr(self, "btn_bold") else False,
            "is_italic": getattr(self, "btn_italic", None).isChecked() if hasattr(self, "btn_italic") else False,
            "is_underline": getattr(self, "btn_underline", None).isChecked() if hasattr(self, "btn_underline") else False,
            "shadow": False,
            "outline": False,
            "logo_path": self.txt_logo_path.text(),
            "scale": float(self.slider_scale.value()),
            "opacity": self.slider_opacity.value() / 100.0,
            "rotation": float(self.slider_rotation.value()),
            "preset": self.preset_position,
            "margin_x": self.spin_margin_x.value(),
            "margin_y": self.spin_margin_y.value(),
            "pos_x": self.custom_pos_x,
            "pos_y": self.custom_pos_y,
            "relative_pos": False
        }

    def emit_config(self):
        self.config_changed.emit(self.get_current_config())
