"""
src/gui/main_window.py
WatermarkStudio — Ventana Principal de Aplicación PyQt6 (Dark Slate / Obsidian)
Ensamblado con QMenuBar, QSplitter horizontal, atajos de teclado y barra de estado técnica.
Integración completa con OpenCV, FFmpeg y WatermarkEngine para imágenes y vídeos.
"""

import sys
import os
from typing import Optional
import cv2
from PIL import Image, ImageDraw, ImageFont

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QApplication, QLabel, QProgressDialog
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QIcon

# Importaciones locales del módulo GUI y Core
from .theme import DARK_THEME_QSS
from .control_panel import ControlPanel
from .preview_canvas import PreviewCanvas
from ..core.video_engine import VideoEngine
from ..core.watermark_engine import WatermarkEngine
from ..core.exporter import ImageExporter
from ..core.font_loader import get_system_fonts


class VideoExportWorker(QThread):
    """Hilo secundario para renderizar el vídeo con FFmpeg sin congelar la interfaz de usuario."""
    progress_changed = pyqtSignal(float)
    finished_export = pyqtSignal(bool, str)

    def __init__(self, input_video: str, output_video: str, config: dict):
        super().__init__()
        self.input_video = input_video
        self.output_video = output_video
        self.config = config
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            success = VideoEngine.apply_watermark_to_video(
                input_video=self.input_video,
                output_video=self.output_video,
                config=self.config,
                progress_callback=lambda p: self.progress_changed.emit(p),
                cancel_check=lambda: self._is_cancelled
            )
            if success:
                self.finished_export.emit(True, "Exportación completada con éxito.")
            else:
                self.finished_export.emit(False, "La exportación fue cancelada por el usuario.")
        except Exception as e:
            self.finished_export.emit(False, f"Error durante la exportación:\n{str(e)}")


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
        self._current_base_image: Optional[Image.Image] = None
        self._is_video = False
        self._video_cap: Optional[cv2.VideoCapture] = None
        self._video_info = None
        self._system_fonts = get_system_fonts()
        self._active_worker = None

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

        # Sincronización de rango de recorte entre Lienzo y Panel
        self.canvas.trim_range_changed.connect(self.control_panel.set_trim_range)
        self.control_panel.trim_range_changed.connect(self.canvas.set_trim_range)

        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(self.control_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([950, 350])

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
    # EXTRACCIÓN DE FOTOGRAMAS DE VÍDEO
    # -----------------------------------------------------------------
    def _extract_video_frame(self, time_sec: float) -> Optional[Image.Image]:
        """Extrae un fotograma del vídeo activo en milisegundos de forma ultra rápida."""
        if not self._video_cap or not self._video_cap.isOpened():
            return None

        self._video_cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, time_sec) * 1000.0)
        ret, frame = self._video_cap.read()
        if ret and frame is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_frame)
        return None

    # -----------------------------------------------------------------
    # SINCRONIZACIÓN DE SEÑALES
    # -----------------------------------------------------------------
    def on_canvas_position_changed(self, x: float, y: float):
        """Notifica al panel que la marca ha sido arrastrada a una posición personalizada."""
        self.control_panel.set_custom_drag_position(x, y)

    def on_video_time_seeked(self, seconds: float):
        """Callback cuando el usuario desplaza la línea de tiempo del vídeo o durante la reproducción."""
        if self._is_video and self._video_cap:
            frame = self._extract_video_frame(seconds)
            if frame is not None:
                self._current_base_image = frame
                self.canvas.update_base_frame(frame)

        total_dur = self._video_info.get("duration", 0.0) if self._video_info else 0.0
        self.lbl_status_engine.setText(f"▶ Tiempo de Vídeo: {seconds:.2f}s / {total_dur:.2f}s | Fotograma Sincronizado")

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
        """Crea el bitmap PIL con el texto o logo utilizando WatermarkEngine."""
        mode = config.get("mode", "text")
        opacity = config.get("opacity", 0.75)
        rotation = config.get("rotation", 0.0)
        base_w = self._current_base_image.width if self._current_base_image else 1920
        base_h = self._current_base_image.height if self._current_base_image else 1080

        if mode == "text":
            font_family = config.get("font_family", "Segoe UI")
            font_path = self._system_fonts.get(font_family, "")
            return WatermarkEngine.create_text_element(
                text=config.get("text", "Watermark"),
                font_path=font_path,
                font_size=config.get("font_size", 48),
                color_rgb=config.get("color", (248, 250, 252)),
                opacity=opacity,
                rotation=rotation,
                is_bold=config.get("is_bold", False),
                is_italic=config.get("is_italic", False),
                is_underline=config.get("is_underline", False)
            )
        else:
            return WatermarkEngine.create_logo_element(
                logo_path=config.get("logo_path", ""),
                scale_percent=config.get("scale", 0.25),
                base_w=base_w,
                base_h=base_h,
                opacity=opacity,
                rotation=rotation
            )

    # -----------------------------------------------------------------
    # DIÁLOGOS DE ARCHIVO (CARGAR Y GUARDAR)
    # -----------------------------------------------------------------
    def open_media_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar Archivo de Foto o Vídeo",
            "",
            "Archivos Multimedia (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.mov *.mkv *.avi *.webm *.m4v *.wmv);;Todos los archivos (*.*)"
        )
        if file_path:
            self._current_media_path = file_path
            ext = os.path.splitext(file_path)[1].lower()
            is_video = ext in [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv", ".flv"]

            if is_video:
                self._is_video = True
                if self._video_cap is not None:
                    self._video_cap.release()
                    self._video_cap = None

                self._video_cap = cv2.VideoCapture(file_path)
                try:
                    self._video_info = VideoEngine.get_video_info(file_path)
                    duration = self._video_info.get("duration", 0.0)
                    w = self._video_info.get("width", 1920)
                    h = self._video_info.get("height", 1080)
                    fps = self._video_info.get("fps", 30.0)
                except Exception:
                    self._video_info = {"duration": 0.0, "width": 1920, "height": 1080, "fps": 30.0}
                    duration = 0.0
                    w, h, fps = 1920, 1080, 30.0

                frame = self._extract_video_frame(0.0)
                if frame is None:
                    ret, raw_frame = self._video_cap.read()
                    if ret and raw_frame is not None:
                        rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
                        frame = Image.fromarray(rgb)
                    else:
                        frame = Image.new("RGBA", (w, h), (30, 30, 40, 255))

                self._current_base_image = frame
                self.canvas.set_base_image(frame, is_video=True, duration=duration)
                self.control_panel.set_video_mode(True, duration=duration)
                self.lbl_status_resolution.setText(f"Vídeo: {w} × {h} px | {fps:.1f} FPS | {duration:.1f}s")
                self.lbl_status_engine.setText(f"● Vídeo cargado: {os.path.basename(file_path)}")
            else:
                self._is_video = False
                if self._video_cap is not None:
                    self._video_cap.release()
                    self._video_cap = None
                self._video_info = None

                try:
                    img = Image.open(file_path).convert("RGBA")
                    self._current_base_image = img
                    self.canvas.set_base_image(img, is_video=False)
                    self.control_panel.set_video_mode(False)
                    self.lbl_status_resolution.setText(f"Imagen: {img.width} × {img.height} px")
                    self.lbl_status_engine.setText(f"● Imagen cargada: {os.path.basename(file_path)}")
                except Exception as e:
                    QMessageBox.warning(self, "Error al abrir imagen", f"No se pudo cargar la imagen:\n{e}")
                    return

            self.on_config_changed(self.control_panel.get_current_config())

    def save_media_dialog(self):
        if not self._current_media_path and not self._current_base_image:
            QMessageBox.information(self, "Aviso", "Primero carga una imagen o vídeo para exportar.")
            return

        config = self.control_panel.get_current_config()
        font_family = config.get("font_family", "Segoe UI")
        config["font_path"] = self._system_fonts.get(font_family, "")

        if self._is_video and self._current_media_path:
            orig_name = os.path.splitext(os.path.basename(self._current_media_path))[0]
            st = config.get("start_time", 0.0)
            et = config.get("end_time", 0.0)
            is_trimmed = config.get("is_trimmed", False)

            suffix = f"_{st:.1f}s-{et:.1f}s" if is_trimmed else ""
            default_out = f"{orig_name}{suffix}_watermarked.mp4"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Vídeo con Marca de Agua",
                default_out,
                "Vídeo MP4 (*.mp4);;Vídeo MKV (*.mkv);;Vídeo MOV (*.mov)"
            )
            if not file_path:
                return

            msg_progress = (
                f"Procesando y recortando fragmento [{st:.2f}s ➔ {et:.2f}s] con FFmpeg..."
                if is_trimmed
                else "Procesando y codificando vídeo completo con FFmpeg..."
            )

            # Diálogo de progreso para vídeo con FFmpeg
            progress_dialog = QProgressDialog(msg_progress, "Cancelar", 0, 100, self)
            progress_dialog.setWindowTitle("Exportando Vídeo")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)

            worker = VideoExportWorker(self._current_media_path, file_path, config)

            def on_progress(p: float):
                progress_dialog.setValue(int(p * 100))

            def on_finished(success: bool, msg: str):
                progress_dialog.close()
                if success:
                    if is_trimmed:
                        dur = et - st
                        info_txt = f"El fragmento recortado [{st:.2f}s ➔ {et:.2f}s] ({dur:.1f}s) con la marca de agua se exportó exitosamente en:\n{file_path}"
                    else:
                        info_txt = f"El vídeo completo con la marca de agua se exportó exitosamente en:\n{file_path}"
                    QMessageBox.information(self, "Exportación Completada", info_txt)
                else:
                    QMessageBox.warning(self, "Exportación Interrumpida", msg)

            worker.progress_changed.connect(on_progress)
            worker.finished_export.connect(on_finished)
            progress_dialog.canceled.connect(worker.cancel)

            worker.start()
            self._active_worker = worker

        else:
            orig_name = "imagen_watermarked.png"
            if self._current_media_path:
                orig_name = f"{os.path.splitext(os.path.basename(self._current_media_path))[0]}_watermarked.png"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Imagen con Marca de Agua",
                orig_name,
                "Imágenes (*.png *.jpg *.webp *.bmp)"
            )
            if not file_path:
                return

            try:
                final_img = WatermarkEngine.apply_watermark(self._current_base_image, config)
                ImageExporter.save_image(final_img, file_path)
                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"La imagen procesada se ha guardado correctamente en:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"No se pudo guardar la imagen:\n{e}")

    def closeEvent(self, event):
        if self._video_cap is not None:
            self._video_cap.release()
            self._video_cap = None
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
