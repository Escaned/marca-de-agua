"""
src/gui/control_panel.py
WatermarkStudio — Panel Lateral de Control Ergonómico (Dark Slate / Obsidian)
Implementación completa para PyQt6 compatible con WatermarkEngine y MainWindow.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QSlider, QSpinBox, QDoubleSpinBox,
    QColorDialog, QFileDialog, QTabWidget, QFrame, QButtonGroup,
    QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontDatabase


class ColorButton(QPushButton):
    """Botón con selector de color y previsualización dinámica en tiempo real."""
    color_changed = pyqtSignal(tuple)

    def __init__(self, default_color=(248, 250, 252), parent=None):
        super().__init__(parent)
        self._color = default_color
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Hacer clic para cambiar el color de la marca de agua")
        self.clicked.connect(self._choose_color)
        self._update_appearance()

    @property
    def color(self) -> tuple:
        return self._color

    @color.setter
    def color(self, rgb: tuple):
        self._color = rgb
        self._update_appearance()
        self.color_changed.emit(rgb)

    def _update_appearance(self):
        r, g, b = self._color
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        text_color = "#0f172a" if luminance > 140 else "#f8fafc"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                color: {text_color};
                border: 1px solid #383852;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                border-color: #60a5fa;
            }}
        """)
        self.setText(f"🎨 {hex_color}")

    def _choose_color(self):
        current_qcolor = QColor(*self._color)
        dialog = QColorDialog(current_qcolor, self)
        dialog.setWindowTitle("Seleccionar Color de Marca")
        if dialog.exec():
            selected = dialog.selectedColor()
            if selected.isValid():
                self.color = (selected.red(), selected.green(), selected.blue())


class ControlPanel(QWidget):
    """
    Panel lateral de configuración con pestañas de Texto/Logo,
    transformaciones (opacidad/rotación), matriz de anclaje 3x3 y márgenes.
    """
    config_changed = pyqtSignal(dict)
    open_image_requested = pyqtSignal()
    save_image_requested = pyqtSignal()
    trim_range_changed = pyqtSignal(float, float)

    PRESET_NAMES = {
        (0, 0): "top_left",
        (0, 1): "top_center",
        (0, 2): "top_right",
        (1, 0): "center_left",
        (1, 1): "center",
        (1, 2): "center_right",
        (2, 0): "bottom_left",
        (2, 1): "bottom_center",
        (2, 2): "bottom_right",
    }

    PRESET_LABELS = {
        "top_left": "Arriba Izquierda",
        "top_center": "Arriba Centro",
        "top_right": "Arriba Derecha",
        "center_left": "Centro Izquierda",
        "center": "Centro",
        "center_right": "Centro Derecha",
        "bottom_left": "Abajo Izquierda",
        "bottom_center": "Abajo Centro",
        "bottom_right": "Abajo Derecha",
        "custom": "Libre (Arrastre manual)",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("control_panel")
        self.setFixedWidth(350)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._active_mode = "text"  # 'text' o 'logo'
        self._custom_pos_x = None
        self._custom_pos_y = None
        self._active_preset = "bottom_right"
        self._is_video = False
        self._video_duration = 0.0
        self._trim_start = 0.0
        self._trim_end = 0.0

        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ScrollArea ergonómico que evita que los controles queden cortados
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #12121c;
                width: 6px;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background-color: #28283e;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #38bdf8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content_widget = QWidget()
        content_widget.setObjectName("panel_content_widget")
        content_widget.setStyleSheet("""
            QWidget#panel_content_widget {
                background-color: #181824;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # -------------------------------------------------------------
        # 1. BOTONES SUPERIORES DE ACCIÓN PRINCIPAL (Cargar / Guardar)
        # -------------------------------------------------------------
        top_actions_layout = QHBoxLayout()
        top_actions_layout.setSpacing(8)

        self.btn_load = QPushButton("📂 Cargar")
        self.btn_load.setObjectName("btn_load")
        self.btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load.clicked.connect(self.open_image_requested.emit)

        self.btn_save = QPushButton("💾 Guardar")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_image_requested.emit)

        top_actions_layout.addWidget(self.btn_load)
        top_actions_layout.addWidget(self.btn_save)
        content_layout.addLayout(top_actions_layout)

        # -------------------------------------------------------------
        # 2. PESTAÑAS MODO MARCA: TEXTO O LOGO
        # -------------------------------------------------------------
        self.tabs = QTabWidget()
        self.tab_text = self._create_text_tab()
        self.tab_logo = self._create_logo_tab()

        self.tabs.addTab(self.tab_text, "✍️ Texto")
        self.tabs.addTab(self.tab_logo, "🖼️ Logo")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        content_layout.addWidget(self.tabs)

        # -------------------------------------------------------------
        # 3. SECCIÓN: ESTILO & TRANSFORMACIÓN (Opacidad, Rotación)
        # -------------------------------------------------------------
        frame_style = QFrame()
        frame_style.setStyleSheet("background-color: #181824; border: 1px solid #28283a; border-radius: 8px; padding: 6px;")
        style_layout = QVBoxLayout(frame_style)
        style_layout.setContentsMargins(8, 8, 8, 8)
        style_layout.setSpacing(8)

        lbl_section_style = QLabel("ESTILO & TRANSFORMACIÓN")
        lbl_section_style.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none;")
        style_layout.addWidget(lbl_section_style)

        # Fila Opacidad
        row_opacity = QHBoxLayout()
        lbl_opacity_title = QLabel("Opacidad")
        lbl_opacity_title.setStyleSheet("color: #94a3b8; font-size: 12px; border: none;")
        self.lbl_opacity_val = QLabel("75%")
        self.lbl_opacity_val.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 600; border: none;")
        row_opacity.addWidget(lbl_opacity_title)
        row_opacity.addStretch()
        row_opacity.addWidget(self.lbl_opacity_val)
        style_layout.addLayout(row_opacity)

        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(75)
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        style_layout.addWidget(self.slider_opacity)

        # Fila Rotación
        row_rot = QHBoxLayout()
        lbl_rot_title = QLabel("Rotación")
        lbl_rot_title.setStyleSheet("color: #94a3b8; font-size: 12px; border: none;")
        self.lbl_rot_val = QLabel("0°")
        self.lbl_rot_val.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 600; border: none;")
        self.btn_reset_rot = QPushButton("0°")
        self.btn_reset_rot.setFixedSize(28, 20)
        self.btn_reset_rot.setStyleSheet("background: #20202e; color: #94a3b8; border: 1px solid #28283a; border-radius: 4px; font-size: 10px;")
        self.btn_reset_rot.clicked.connect(lambda: self.slider_rot.setValue(0))

        row_rot.addWidget(lbl_rot_title)
        row_rot.addStretch()
        row_rot.addWidget(self.btn_reset_rot)
        row_rot.addWidget(self.lbl_rot_val)
        style_layout.addLayout(row_rot)

        self.slider_rot = QSlider(Qt.Orientation.Horizontal)
        self.slider_rot.setRange(-180, 180)
        self.slider_rot.setValue(0)
        self.slider_rot.valueChanged.connect(self._on_rotation_changed)
        style_layout.addWidget(self.slider_rot)

        content_layout.addWidget(frame_style)

        # -------------------------------------------------------------
        # 4. SECCIÓN: POSICIÓN & ANCLAJE ESPACIAL (Matriz 3x3 + Márgenes)
        # -------------------------------------------------------------
        frame_pos = QFrame()
        frame_pos.setStyleSheet("background-color: #181824; border: 1px solid #28283a; border-radius: 8px; padding: 6px;")
        pos_layout = QVBoxLayout(frame_pos)
        pos_layout.setContentsMargins(8, 8, 8, 8)
        pos_layout.setSpacing(8)

        # Cabecera Posición con estado activo
        row_pos_header = QHBoxLayout()
        lbl_pos_title = QLabel("ANCLAJE ESPACIAL")
        lbl_pos_title.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none;")
        self.lbl_pos_status = QLabel("Abajo Derecha")
        self.lbl_pos_status.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600; border: none;")
        row_pos_header.addWidget(lbl_pos_title)
        row_pos_header.addStretch()
        row_pos_header.addWidget(self.lbl_pos_status)
        pos_layout.addLayout(row_pos_header)

        # Grid 3x3 de anclaje
        grid_widget = QWidget()
        grid_widget.setStyleSheet("border: none;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(0, 4, 0, 4)
        grid_layout.setSpacing(4)

        self.pos_button_group = QButtonGroup(self)
        self.pos_button_group.setExclusive(True)
        self.grid_buttons = {}

        symbols = [
            ("↖", 0, 0), ("↑", 0, 1), ("↗", 0, 2),
            ("←", 1, 0), ("•", 1, 1), ("→", 1, 2),
            ("↙", 2, 0), ("↓", 2, 1), ("↘", 2, 2)
        ]

        for symbol, r, c in symbols:
            btn = QPushButton(symbol)
            btn.setCheckable(True)
            btn.setProperty("class", "tool_btn")
            btn.setFixedSize(36, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            preset_name = self.PRESET_NAMES[(r, c)]
            btn.clicked.connect(lambda checked, name=preset_name: self._on_preset_clicked(name))
            if preset_name == "bottom_right":
                btn.setChecked(True)

            self.pos_button_group.addButton(btn)
            self.grid_buttons[preset_name] = btn
            grid_layout.addWidget(btn, r, c, alignment=Qt.AlignmentFlag.AlignCenter)

        pos_layout.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Fila Márgenes X e Y
        row_margins = QHBoxLayout()
        row_margins.setSpacing(8)

        # Margen X
        col_mx = QVBoxLayout()
        lbl_mx = QLabel("Margen X (px)")
        lbl_mx.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        self.spin_margin_x = QSpinBox()
        self.spin_margin_x.setRange(0, 1000)
        self.spin_margin_x.setValue(24)
        self.spin_margin_x.valueChanged.connect(self.emit_config)
        col_mx.addWidget(lbl_mx)
        col_mx.addWidget(self.spin_margin_x)

        # Margen Y
        col_my = QVBoxLayout()
        lbl_my = QLabel("Margen Y (px)")
        lbl_my.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        self.spin_margin_y = QSpinBox()
        self.spin_margin_y.setRange(0, 1000)
        self.spin_margin_y.setValue(24)
        self.spin_margin_y.valueChanged.connect(self.emit_config)
        col_my.addWidget(lbl_my)
        col_my.addWidget(self.spin_margin_y)

        row_margins.addLayout(col_mx)
        row_margins.addLayout(col_my)
        pos_layout.addLayout(row_margins)

        content_layout.addWidget(frame_pos)

        # -------------------------------------------------------------
        # 5. SECCIÓN: RECORTE DE VÍDEO (PUNTO IN / OUT)
        # -------------------------------------------------------------
        self.frame_trim = QFrame()
        self.frame_trim.setStyleSheet("background-color: #181824; border: 1px solid #28283a; border-radius: 8px; padding: 6px;")
        trim_layout = QVBoxLayout(self.frame_trim)
        trim_layout.setContentsMargins(8, 8, 8, 8)
        trim_layout.setSpacing(6)

        lbl_trim_title = QLabel("✂ RECORTE DE VÍDEO (IN / OUT)")
        lbl_trim_title.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none;")
        trim_layout.addWidget(lbl_trim_title)

        # Fila Inicio y Fin
        row_in_out = QHBoxLayout()
        row_in_out.setSpacing(6)

        # Punto Inicio
        col_in = QVBoxLayout()
        lbl_in = QLabel("Inicio (seg)")
        lbl_in.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        self.spin_start_time = QDoubleSpinBox()
        self.spin_start_time.setRange(0.0, 99999.0)
        self.spin_start_time.setSingleStep(0.5)
        self.spin_start_time.setDecimals(2)
        self.spin_start_time.setSuffix(" s")
        self.spin_start_time.valueChanged.connect(self._on_trim_spin_changed)
        col_in.addWidget(lbl_in)
        col_in.addWidget(self.spin_start_time)

        # Punto Fin
        col_out = QVBoxLayout()
        lbl_out = QLabel("Fin (seg)")
        lbl_out.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        self.spin_end_time = QDoubleSpinBox()
        self.spin_end_time.setRange(0.0, 99999.0)
        self.spin_end_time.setSingleStep(0.5)
        self.spin_end_time.setDecimals(2)
        self.spin_end_time.setSuffix(" s")
        self.spin_end_time.valueChanged.connect(self._on_trim_spin_changed)
        col_out.addWidget(lbl_out)
        col_out.addWidget(self.spin_end_time)

        row_in_out.addLayout(col_in)
        row_in_out.addLayout(col_out)
        trim_layout.addLayout(row_in_out)

        self.lbl_trim_summary = QLabel("Corte: 0.00s a 0.00s (0.0s)")
        self.lbl_trim_summary.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; font-family: 'Consolas', monospace;")
        trim_layout.addWidget(self.lbl_trim_summary)

        content_layout.addWidget(self.frame_trim)
        self.frame_trim.hide()  # Oculto hasta que se cargue un vídeo

        # Espaciador elástico inferior
        content_layout.addStretch()

        self.scroll_area.setWidget(content_widget)
        root_layout.addWidget(self.scroll_area)

    # -----------------------------------------------------------------
    # SUB-PESTAÑA 1: CONTROLES DE TEXTO
    # -----------------------------------------------------------------
    def _create_text_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(8)

        # Input Texto
        lbl_text = QLabel("Contenido del Texto")
        lbl_text.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
        self.input_text = QLineEdit("© WatermarkStudio • Preview")
        self.input_text.setPlaceholderText("Ingresa el texto de la marca...")
        self.input_text.textChanged.connect(self.emit_config)
        layout.addWidget(lbl_text)
        layout.addWidget(self.input_text)

        # Tipografía y Tamaño
        lbl_font = QLabel("Tipografía y Tamaño")
        lbl_font.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
        layout.addWidget(lbl_font)

        row_font = QHBoxLayout()
        row_font.setSpacing(6)

        self.combo_font = QComboBox()
        self.combo_font.setEditable(False)
        fonts = QFontDatabase.families()
        common_fonts = ["Inter", "Segoe UI", "Arial", "Roboto", "Calibri", "Montserrat", "Helvetica"]
        for cf in reversed(common_fonts):
            if cf in fonts:
                fonts.remove(cf)
                fonts.insert(0, cf)
        self.combo_font.addItems(fonts[:30])
        self.combo_font.currentTextChanged.connect(self.emit_config)

        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 300)
        self.spin_font_size.setValue(48)
        self.spin_font_size.setFixedWidth(64)
        self.spin_font_size.valueChanged.connect(self.emit_config)

        row_font.addWidget(self.combo_font, 1)
        row_font.addWidget(self.spin_font_size)
        layout.addLayout(row_font)

        # Formato (Negrita, Cursiva, Subrayado) y Color
        lbl_format = QLabel("Formato y Color")
        lbl_format.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
        layout.addWidget(lbl_format)

        row_style_buttons = QHBoxLayout()
        row_style_buttons.setSpacing(6)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setChecked(True)
        self.btn_bold.setProperty("class", "tool_btn")
        self.btn_bold.setFixedSize(36, 32)
        self.btn_bold.setToolTip("Negrita (Bold)")
        self.btn_bold.setStyleSheet("font-weight: 700; font-size: 13px;")
        self.btn_bold.clicked.connect(self.emit_config)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setProperty("class", "tool_btn")
        self.btn_italic.setFixedSize(36, 32)
        self.btn_italic.setToolTip("Cursiva (Italic)")
        self.btn_italic.setStyleSheet("font-style: italic; font-size: 13px;")
        self.btn_italic.clicked.connect(self.emit_config)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setProperty("class", "tool_btn")
        self.btn_underline.setFixedSize(36, 32)
        self.btn_underline.setToolTip("Subrayado (Underline)")
        self.btn_underline.setStyleSheet("text-decoration: underline; font-size: 13px;")
        self.btn_underline.clicked.connect(self.emit_config)

        self.btn_color = ColorButton(default_color=(248, 250, 252))
        self.btn_color.color_changed.connect(lambda _: self.emit_config())

        row_style_buttons.addWidget(self.btn_bold)
        row_style_buttons.addWidget(self.btn_italic)
        row_style_buttons.addWidget(self.btn_underline)
        row_style_buttons.addWidget(self.btn_color, 1)

        layout.addLayout(row_style_buttons)
        return widget

    # -----------------------------------------------------------------
    # SUB-PESTAÑA 2: CONTROLES DE LOGO
    # -----------------------------------------------------------------
    def _create_logo_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(8)

        lbl_logo_path = QLabel("Archivo de Imagen / Logo")
        lbl_logo_path.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
        layout.addWidget(lbl_logo_path)

        row_file = QHBoxLayout()
        row_file.setSpacing(6)

        self.input_logo_path = QLineEdit()
        self.input_logo_path.setReadOnly(True)
        self.input_logo_path.setPlaceholderText("Seleccionar PNG, JPG o WebP...")

        self.btn_browse_logo = QPushButton("Examinar...")
        self.btn_browse_logo.setFixedSize(80, 28)
        self.btn_browse_logo.setStyleSheet("background: #242436; color: #e2e8f0; border: 1px solid #28283a; border-radius: 6px;")
        self.btn_browse_logo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_logo.clicked.connect(self._browse_logo_file)

        row_file.addWidget(self.input_logo_path, 1)
        row_file.addWidget(self.btn_browse_logo)
        layout.addLayout(row_file)

        # Escala del Logo
        row_scale = QHBoxLayout()
        lbl_scale_title = QLabel("Escala")
        lbl_scale_title.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.lbl_scale_val = QLabel("25%")
        self.lbl_scale_val.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 600;")
        row_scale.addWidget(lbl_scale_title)
        row_scale.addStretch()
        row_scale.addWidget(self.lbl_scale_val)
        layout.addLayout(row_scale)

        self.slider_logo_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_logo_scale.setRange(1, 100)
        self.slider_logo_scale.setValue(25)
        self.slider_logo_scale.valueChanged.connect(self._on_logo_scale_changed)
        layout.addWidget(self.slider_logo_scale)

        return widget

    # -----------------------------------------------------------------
    # MANEJADORES DE EVENTOS
    # -----------------------------------------------------------------
    def _on_tab_changed(self, index: int):
        self._active_mode = "text" if index == 0 else "logo"
        self.emit_config()

    def _on_opacity_changed(self, val: int):
        self.lbl_opacity_val.setText(f"{val}%")
        self.emit_config()

    def _on_rotation_changed(self, val: int):
        self.lbl_rot_val.setText(f"{val}°")
        self.emit_config()

    def _on_logo_scale_changed(self, val: int):
        self.lbl_scale_val.setText(f"{val}%")
        self.emit_config()

    def _on_preset_clicked(self, preset_name: str):
        self._active_preset = preset_name
        self._custom_pos_x = None
        self._custom_pos_y = None
        self.lbl_pos_status.setText(self.PRESET_LABELS.get(preset_name, preset_name))
        self.lbl_pos_status.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600; border: none;")
        self.emit_config()

    def set_custom_drag_position(self, x: float, y: float):
        """Llamado desde el lienzo interactivo cuando el usuario arrastra libremente la marca."""
        self._active_preset = "custom"
        self._custom_pos_x = int(x)
        self._custom_pos_y = int(y)

        # Desmarcar todos los botones de la matriz
        for btn in self.grid_buttons.values():
            btn.setChecked(False)

        self.lbl_pos_status.setText(f"Libre ({self._custom_pos_x}, {self._custom_pos_y})")
        self.lbl_pos_status.setStyleSheet("color: #60a5fa; font-size: 11px; font-weight: 600; border: none;")

    def _browse_logo_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Logotipo o Imagen",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;Todos los archivos (*.*)"
        )
        if file_path:
            self.input_logo_path.setText(file_path)
            self.emit_config()

    def set_video_mode(self, is_video: bool, duration: float = 0.0):
        """Habilita o deshabilita la sección de recorte de vídeo según el tipo de medio."""
        self._is_video = is_video
        self._video_duration = duration
        if is_video and duration > 0:
            self.spin_start_time.blockSignals(True)
            self.spin_end_time.blockSignals(True)
            self.spin_start_time.setRange(0.0, duration)
            self.spin_end_time.setRange(0.0, duration)
            self.spin_start_time.setValue(0.0)
            self.spin_end_time.setValue(duration)
            self.spin_start_time.blockSignals(False)
            self.spin_end_time.blockSignals(False)
            self._trim_start = 0.0
            self._trim_end = duration
            self._update_trim_summary_label()
            self.frame_trim.show()
        else:
            self.frame_trim.hide()

    def set_trim_range(self, start_sec: float, end_sec: float):
        """Sincroniza los valores numéricos desde el lienzo de previsualización."""
        self._trim_start = max(0.0, min(start_sec, self._video_duration))
        self._trim_end = max(self._trim_start, min(end_sec, self._video_duration))

        self.spin_start_time.blockSignals(True)
        self.spin_end_time.blockSignals(True)
        self.spin_start_time.setValue(self._trim_start)
        self.spin_end_time.setValue(self._trim_end)
        self.spin_start_time.blockSignals(False)
        self.spin_end_time.blockSignals(False)
        self._update_trim_summary_label()

    def _on_trim_spin_changed(self):
        """Manejador cuando el usuario modifica los spinboxes de tiempo."""
        st = self.spin_start_time.value()
        et = self.spin_end_time.value()
        if st > et:
            et = st
            self.spin_end_time.blockSignals(True)
            self.spin_end_time.setValue(et)
            self.spin_end_time.blockSignals(False)

        self._trim_start = st
        self._trim_end = et
        self._update_trim_summary_label()
        self.trim_range_changed.emit(self._trim_start, self._trim_end)
        self.emit_config()

    def _update_trim_summary_label(self):
        """Actualiza el texto descriptivo del fragmento."""
        dur = max(0.0, self._trim_end - self._trim_start)
        is_trimmed = (self._trim_start > 0.05) or (self._trim_end < self._video_duration - 0.05)
        if is_trimmed:
            self.lbl_trim_summary.setText(f"Corte: {self._trim_start:.2f}s ➔ {self._trim_end:.2f}s ({dur:.1f}s)")
            self.lbl_trim_summary.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600; border: none; font-family: 'Consolas', monospace;")
        else:
            self.lbl_trim_summary.setText(f"Vídeo Completo ({self._video_duration:.1f}s)")
            self.lbl_trim_summary.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; font-family: 'Consolas', monospace;")

    # -----------------------------------------------------------------
    # EXPORTACIÓN DE CONFIGURACIÓN
    # -----------------------------------------------------------------
    def get_current_config(self) -> dict:
        """Devuelve el diccionario con el estado actual del panel sincronizado."""
        return {
            "mode": self._active_mode,
            "text": self.input_text.text(),
            "font_family": self.combo_font.currentText(),
            "font_size": self.spin_font_size.value(),
            "color": self.btn_color.color,
            "is_bold": self.btn_bold.isChecked(),
            "is_italic": self.btn_italic.isChecked(),
            "is_underline": self.btn_underline.isChecked(),
            "logo_path": self.input_logo_path.text(),
            "scale": self.slider_logo_scale.value() / 100.0,
            "opacity": self.slider_opacity.value() / 100.0,
            "rotation": float(self.slider_rot.value()),
            "preset": self._active_preset,
            "margin_x": self.spin_margin_x.value(),
            "margin_y": self.spin_margin_y.value(),
            "pos_x": self._custom_pos_x,
            "pos_y": self._custom_pos_y,
            "start_time": self._trim_start if self._is_video else 0.0,
            "end_time": self._trim_end if self._is_video else 0.0,
            "is_trimmed": ((self._trim_start > 0.05) or (self._trim_end < self._video_duration - 0.05)) if self._is_video else False,
        }

    def emit_config(self):
        """Emite la señal config_changed con la configuración actualizada."""
        self.config_changed.emit(self.get_current_config())
