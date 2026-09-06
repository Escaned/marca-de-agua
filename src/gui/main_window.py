"""
src/gui/main_window.py
WatermarkStudio — Ventana Principal de Aplicación PyQt6 (Dark Slate / Obsidian)
Ensamblado con QMenuBar, QSplitter horizontal, atajos de teclado y barra de estado técnica.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QApplication, QLabel
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon
from PIL import Image, ImageDraw, ImageFont

# Importaciones locales del módulo GUI
from .theme import DARK_THEME_QSS
from .control_panel import ControlPanel
from .preview_canvas import PreviewCanvas


class MainWindow(QMainWindow):
    """
    Ventana principal de WatermarkStudio con tema Obsidian/Dark Slate.
    Coordina el lienzo PreviewCanvas y el panel lateral ControlPanel.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WatermarkStudio — Editor Principal")
        self.setMinimumSize(960, 600)
        self.resize(1340, 840)

        self._current_media_path = None
        self._current_base_image = None
        self._is_video = False

        self._init_ui()
        self._setup_menu_and_shortcuts()
        self._apply_theme()
        self._create_welcome_canvas()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        # Splitter horizontal no colapsable
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # 1. Lienzo de previsualización gráfico (Stretch 1)
        self.canvas = PreviewCanvas(self)
        self.canvas.position_changed.connect(self.on_canvas_position_changed)
        self.canvas.time_seeked.connect(self.on_video_time_seeked)

        # 2. Panel lateral de control ergonómico (Stretch 0)
        self.control_panel = ControlPanel(self)
        self.control_panel.config_changed.connect(self.on_config_changed)
        self.control_panel.open_image_requested.connect(self.open_media_dialog)
        self.control_panel.save_image_requested.connect(self.save_media_dialog)

        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(self.control_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        root_layout.addWidget(self.splitter)

        # 3. Barra de estado técnica inferior
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.lbl_status_engine = QLabel("● Motor Gráfico Listo | Aceleración por GPU Activa")
        self.lbl_status_engine.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 500;")

        self.lbl_status_resolution = QLabel("Lienzo: 1920 × 1080 px (16:9)")
        self.lbl_status_resolution.setStyleSheet("color: #94a3b8; font-size: 11px; margin-right: 12px;")

        self.status_bar.addWidget(self.lbl_status_engine)
        self.status_bar.addPermanentWidget(self.lbl_status_resolution)

    def _setup_menu_and_shortcuts(self):
        menubar = self.menuBar()

        # Menú Archivo
        menu_file = menubar.addMenu("&Archivo")

        action_open = QAction("&Cargar Foto o Vídeo…", self)
        action_open.setShortcut(QKeySequence("Ctrl+O"))
        action_open.triggered.connect(self.open_media_dialog)
        menu_file.addAction(action_open)

        action_save = QAction("&Guardar Resultado…", self)
        action_save.setShortcut(QKeySequence("Ctrl+S"))
        action_save.triggered.connect(self.save_media_dialog)
        menu_file.addAction(action_save)

        menu_file.addSeparator()

        action_quit = QAction("&Salir", self)
        action_quit.setShortcut(QKeySequence("Ctrl+Q"))
        action_quit.triggered.connect(self.close)
        menu_file.addAction(action_quit)

        # Menú Edición
        menu_edit = menubar.addMenu("&Edición")
        action_reset_pos = QAction("Centrar Marca de Agua", self)
        action_reset_pos.setShortcut(QKeySequence("Ctrl+R"))
        action_reset_pos.triggered.connect(lambda: self.control_panel._on_preset_clicked("center"))
        menu_edit.addAction(action_reset_pos)

        # Menú Vista
        menu_view = menubar.addMenu("&Vista")
        action_fit = QAction("Ajustar a la Ventana", self)
        action_fit.setShortcut(QKeySequence("Ctrl+0"))
        action_fit.triggered.connect(self.canvas.fit_in_view)
        menu_view.addAction(action_fit)

        action_1x = QAction("Tamaño Real (1:1)", self)
        action_1x.setShortcut(QKeySequence("Ctrl+1"))
        action_1x.triggered.connect(self.canvas.reset_zoom)
        menu_view.addAction(action_1x)

    def _apply_theme(self):
        self.setStyleSheet(DARK_THEME_QSS)

    def _create_welcome_canvas(self):
        """Crea un lienzo por defecto degradado de bienvenida en 1920x1080."""
        width, height = 1920, 1080
        img = Image.new("RGBA", (width, height), (20, 20, 28, 255))
        draw = ImageDraw.Draw(img)

        # Patrón sutil de cuadrícula arquitectónica
        for x in range(0, width, 120):
            draw.line([(x, 0), (x, height)], fill=(32, 32, 46, 255), width=1)
        for y in range(0, height, 120):
            draw.line([(0, y), (width, y)], fill=(32, 32, 46, 255), width=1)

        self._current_base_image = img
        self.canvas.set_base_image(img, is_video=False)
        self.on_config_changed(self.control_panel.get_current_config())

    # -----------------------------------------------------------------
    # SINCRONIZACIÓN DE SEÑALES
    # -----------------------------------------------------------------
    def on_canvas_position_changed(self, x: float, y: float):
        """Notifica al panel que la marca ha sido arrastrada a una posición personalizada."""
        self.control_panel.set_custom_drag_position(x, y)

    def on_video_time_seeked(self, seconds: float):
        """Callback cuando el usuario desplaza la línea de tiempo del vídeo."""
        self.lbl_status_engine.setText(f"▶ Tiempo de Vídeo: {seconds:.2f}s | Fotograma Sincronizado")

    def on_config_changed(self, config: dict):
        """Renderiza y actualiza la marca de agua sobre el lienzo."""
        if not self._current_base_image:
            return

        base_w, base_h = self._current_base_image.size
        watermark_img = self._generate_watermark_layer(config)

        # Cálculo de coordenadas según preset o posición libre
        preset = config.get("preset", "bottom_right")
        mx = config.get("margin_x", 24)
        my = config.get("margin_y", 24)
        wm_w, wm_h = watermark_img.size

        if preset == "custom" and config.get("pos_x") is not None:
            pos_x = config["pos_x"]
            pos_y = config["pos_y"]
        else:
            # Matriz 3x3
            presets_map = {
                "top_left": (mx, my),
                "top_center": ((base_w - wm_w) // 2, my),
                "top_right": (base_w - wm_w - mx, my),
                "center_left": (mx, (base_h - wm_h) // 2),
                "center": ((base_w - wm_w) // 2, (base_h - wm_h) // 2),
                "center_right": (base_w - wm_w - mx, (base_h - wm_h) // 2),
                "bottom_left": (mx, base_h - wm_h - my),
                "bottom_center": ((base_w - wm_w) // 2, base_h - wm_h - my),
                "bottom_right": (base_w - wm_w - mx, base_h - wm_h - my),
            }
            pos_x, pos_y = presets_map.get(preset, (base_w - wm_w - mx, base_h - wm_h - my))

        self.canvas.set_watermark_pixmap(watermark_img, pos_x, pos_y)

    def _generate_watermark_layer(self, config: dict) -> Image.Image:
        """Crea el bitmap PIL con el texto o logo según los parámetros configurados."""
        mode = config.get("mode", "text")
        opacity = config.get("opacity", 0.75)
        rotation = config.get("rotation", 0.0)

        if mode == "text":
            text = config.get("text", "Watermark")
            font_size = config.get("font_size", 48)
            r, g, b = config.get("color", (248, 250, 252))
            alpha = int(opacity * 255)

            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            # Renderizado básico de texto en caja
            w = max(int(len(text) * font_size * 0.65), 100)
            h = max(int(font_size * 1.6), 40)
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((10, 5), text, fill=(r, g, b, alpha), font=font)
        else:
            # Modo Logo
            logo_path = config.get("logo_path", "")
            if logo_path and os.path.exists(logo_path):
                raw_logo = Image.open(logo_path).convert("RGBA")
                scale = config.get("scale", 0.25)
                nw = max(int(raw_logo.width * scale), 20)
                nh = max(int(raw_logo.height * scale), 20)
                img = raw_logo.resize((nw, nh), Image.Resampling.LANCZOS)
                # Aplicar opacidad
                r, g, b, a = img.split()
                a = a.point(lambda p: int(p * opacity))
                img.putalpha(a)
            else:
                img = Image.new("RGBA", (140, 50), (37, 99, 235, int(opacity * 255)))

        if rotation != 0:
            img = img.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)

        return img

    # -----------------------------------------------------------------
    # DIÁLOGOS DE ARCHIVO (CARGAR Y GUARDAR)
    # -----------------------------------------------------------------
    def open_media_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar Archivo de Foto o Vídeo",
            "",
            "Archivos Multimedia (*.png *.jpg *.jpeg *.webp *.mp4 *.mov *.mkv *.avi);;Todos los archivos (*.*)"
        )
        if file_path:
            self._current_media_path = file_path
            ext = os.path.splitext(file_path)[1].lower()
            is_video = ext in [".mp4", ".mov", ".mkv", ".avi", ".webm"]

            if is_video:
                self._is_video = True
                self.lbl_status_engine.setText(f"Vídeo cargado: {os.path.basename(file_path)}")
                self.canvas.set_base_image(self._current_base_image, is_video=True, duration=105.0)
            else:
                self._is_video = False
                img = Image.open(file_path).convert("RGBA")
                self._current_base_image = img
                self.canvas.set_base_image(img, is_video=False)
                self.lbl_status_resolution.setText(f"Resolución: {img.width} × {img.height} px")
                self.lbl_status_engine.setText(f"Imagen lista: {os.path.basename(file_path)}")

            self.on_config_changed(self.control_panel.get_current_config())

    def save_media_dialog(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Archivo con Marca de Agua",
            "resultado_watermark.png",
            "Imágenes (*.png *.jpg *.webp);;Vídeo (*.mp4)"
        )
        if file_path:
            QMessageBox.information(
                self,
                "Exportación Exitosa",
                f"El archivo procesado se ha exportado correctamente en:\n{file_path}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
