import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QStatusBar, QLabel, QApplication,
    QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent
from PIL import Image

from .preview_canvas import PreviewCanvas
from .control_panel import ControlPanel
from ..core.watermark_engine import WatermarkEngine
from ..core.exporter import ImageExporter
from ..core.video_engine import VideoEngine

class VideoExportWorker(QThread):
    """
    Hilo en segundo plano para exportar el vídeo sin congelar la interfaz gráfica.
    """
    progress_changed = pyqtSignal(float)
    finished_signal = pyqtSignal(bool, str)

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
            def on_progress(p: float):
                self.progress_changed.emit(p)

            def is_cancel():
                return self._is_cancelled

            success = VideoEngine.apply_watermark_to_video(
                self.input_video,
                self.output_video,
                self.config,
                progress_callback=on_progress,
                cancel_check=is_cancel
            )

            if success:
                self.finished_signal.emit(True, self.output_video)
            else:
                self.finished_signal.emit(False, "Exportación cancelada.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class MainWindow(QMainWindow):
    """
    Ventana principal con soporte universal para Imágenes y Vídeos.
    """
    VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi', '.webm', '.flv', '.wmv', '.m4v')
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif')

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watermark Studio - Editor de Marcas de Agua (Foto & Vídeo)")
        self.setMinimumSize(850, 550)

        # Ajuste dinámico al tamaño de pantalla del usuario
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            w = min(1280, int(avail.width() * 0.9))
            h = min(800, int(avail.height() * 0.9))
            self.resize(w, h)
        else:
            self.resize(1100, 700)

        self.current_file_path: str = ""
        self.is_video_loaded: bool = False
        self.video_info: dict = {}
        self.loaded_pil_image: Image.Image = None
        self.export_worker: VideoExportWorker = None

        self.init_ui()
        self.apply_dark_theme()
        self.setup_menu_and_shortcuts()

        # Canvas inicial de bienvenida
        self.create_welcome_canvas()

    def init_ui(self):
        self.setAcceptDrops(True)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Splitter horizontal
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # 1. Canvas interactivo central
        self.canvas = PreviewCanvas()
        self.canvas.position_changed.connect(self.on_canvas_position_changed)
        self.canvas.time_seeked.connect(self.on_video_time_seeked)
        self.splitter.addWidget(self.canvas)

        # 2. Panel lateral de controles (fijo y ultra-compacto)
        self.control_panel = ControlPanel()
        self.control_panel.setFixedWidth(240)
        self.control_panel.config_changed.connect(self.on_config_changed)
        self.control_panel.open_image_requested.connect(self.open_media_dialog)
        self.control_panel.save_image_requested.connect(self.save_media_dialog)
        self.splitter.addWidget(self.control_panel)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        main_layout.addWidget(self.splitter)

        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.lbl_status_info = QLabel("Listo. Arrastra una foto o vídeo, o pulsa 'Cargar'.")
        self.lbl_resolution_info = QLabel("")
        self.status_bar.addWidget(self.lbl_status_info, 1)
        self.status_bar.addPermanentWidget(self.lbl_resolution_info)

    def setup_menu_and_shortcuts(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Archivo")

        open_action = QAction("Cargar Foto o Vídeo...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_media_dialog)
        file_menu.addAction(open_action)

        save_action = QAction("Guardar Resultado con Marca de Agua...", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_media_dialog)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("Ver")
        fit_action = QAction("Ajustar a la Ventana", self)
        fit_action.setShortcut(QKeySequence("Ctrl+0"))
        fit_action.triggered.connect(self.canvas.fit_in_view)
        view_menu.addAction(fit_action)

    def create_welcome_canvas(self):
        demo_img = Image.new("RGBA", (1920, 1080), (25, 27, 38, 255))
        self.loaded_pil_image = demo_img
        self.canvas.set_base_image(demo_img)
        self.canvas.set_video_mode(False)
        self.lbl_resolution_info.setText("1920 x 1080 px")
        self.canvas.update_watermark(self.control_panel.get_current_config())

    def open_media_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Foto o Vídeo", "",
            "Archivos Multimedia (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.mov *.mkv *.avi *.webm);;"
            "Vídeos (*.mp4 *.mov *.mkv *.avi *.webm);;"
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp);;"
            "Todos los archivos (*.*)"
        )
        if file_path:
            self.load_media(file_path)

    def load_media(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        if ext in self.VIDEO_EXTENSIONS:
            # 1. MODO VÍDEO
            try:
                info = VideoEngine.get_video_info(file_path)
                self.video_info = info
                self.current_file_path = file_path
                self.is_video_loaded = True

                # Extraer primer fotograma (0.0s)
                frame = VideoEngine.extract_frame_at_time(file_path, 0.0)
                if frame:
                    self.loaded_pil_image = frame
                    self.canvas.set_base_image(frame)
                    self.canvas.set_video_mode(True, info["duration"])
                    self.canvas.update_watermark(self.control_panel.get_current_config())

                mins, secs = divmod(int(info["duration"]), 60)
                self.lbl_status_info.setText(f"🎬 Vídeo: {filename}")
                self.lbl_resolution_info.setText(
                    f"{info['width']} x {info['height']} px | {info['fps']:.1f} FPS | ⏱ {mins:02d}:{secs:02d}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error al abrir vídeo", f"No se pudo cargar el vídeo:\n{str(e)}")

        elif ext in self.IMAGE_EXTENSIONS:
            # 2. MODO IMAGEN
            try:
                img = Image.open(file_path)
                self.loaded_pil_image = img.copy()
                self.current_file_path = file_path
                self.is_video_loaded = False
                self.video_info = {}

                self.canvas.set_base_image(self.loaded_pil_image)
                self.canvas.set_video_mode(False)
                self.canvas.update_watermark(self.control_panel.get_current_config())

                w, h = self.loaded_pil_image.size
                self.lbl_status_info.setText(f"🖼️ Imagen: {filename}")
                self.lbl_resolution_info.setText(f"{w} x {h} px | {img.format or 'RGBA'}")
            except Exception as e:
                QMessageBox.critical(self, "Error al abrir imagen", f"No se pudo cargar la imagen:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Formato no compatible", f"El formato {ext} no es compatible.")

    def on_video_time_seeked(self, time_sec: float):
        """Actualiza el fotograma de fondo cuando el usuario mueve la barra de tiempo."""
        if self.is_video_loaded and self.current_file_path:
            frame = VideoEngine.extract_frame_at_time(self.current_file_path, time_sec)
            if frame:
                self.loaded_pil_image = frame
                self.canvas.set_base_image(frame, keep_viewport=True)

    def save_media_dialog(self):
        if not self.current_file_path and not self.loaded_pil_image:
            QMessageBox.warning(self, "Aviso", "Por favor carga una foto o vídeo primero.")
            return

        config = self.control_panel.get_current_config()

        if self.is_video_loaded:
            # 1. EXPORTACIÓN DE VÍDEO
            base, ext = os.path.splitext(self.current_file_path)
            suggested_name = f"{base}_watermark{ext if ext else '.mp4'}"

            output_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Vídeo con Marca de Agua", suggested_name,
                "MP4 (*.mp4);;MKV (*.mkv);;MOV (*.mov);;WebM (*.webm);;AVI (*.avi)"
            )

            if output_path:
                # Mostrar barra de progreso modal
                self.progress_dlg = QProgressDialog("Procesando vídeo con marca de agua y audio...", "Cancelar", 0, 100, self)
                self.progress_dlg.setWindowTitle("Exportando Vídeo")
                self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress_dlg.setMinimumDuration(0)
                self.progress_dlg.setValue(0)

                # Iniciar hilo de exportación
                self.export_worker = VideoExportWorker(self.current_file_path, output_path, config)
                self.export_worker.progress_changed.connect(self.on_video_progress)
                self.export_worker.finished_signal.connect(self.on_video_export_finished)
                self.progress_dlg.canceled.connect(self.export_worker.cancel)

                self.export_worker.start()

        else:
            # 2. EXPORTACIÓN DE IMAGEN
            suggested_name = "imagen_watermarked.png"
            if self.current_file_path:
                base, ext = os.path.splitext(self.current_file_path)
                suggested_name = f"{base}_watermark{ext}"

            output_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Imagen con Marca de Agua", suggested_name,
                "PNG (*.png);;JPEG (*.jpg *.jpeg);;WebP (*.webp);;BMP (*.bmp)"
            )

            if output_path:
                try:
                    final_img = WatermarkEngine.apply_watermark(self.loaded_pil_image, config)
                    ImageExporter.save_image(final_img, output_path)
                    QMessageBox.information(
                        self, "Éxito", f"¡Imagen guardada correctamente con resolución completa!\n\n{output_path}"
                    )
                    self.lbl_status_info.setText(f"Guardado: {os.path.basename(output_path)}")
                except Exception as e:
                    QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar la imagen:\n{str(e)}")

    def on_video_progress(self, progress: float):
        pct = int(progress * 100)
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            self.progress_dlg.setValue(pct)
            self.progress_dlg.setLabelText(f"Procesando vídeo... {pct}%")

    def on_video_export_finished(self, success: bool, message: str):
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            self.progress_dlg.close()

        if success:
            QMessageBox.information(
                self, "Éxito", f"¡Vídeo exportado correctamente con su audio original!\n\n{message}"
            )
            self.lbl_status_info.setText(f"Vídeo guardado: {os.path.basename(message)}")
        else:
            QMessageBox.warning(self, "Exportación", f"Resultado:\n{message}")

    def on_config_changed(self, config: dict):
        if self.loaded_pil_image:
            self.canvas.update_watermark(config)

    def on_canvas_position_changed(self, pos_x: float, pos_y: float):
        self.control_panel.set_custom_drag_position(pos_x, pos_y)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.VIDEO_EXTENSIONS or ext in self.IMAGE_EXTENSIONS:
                self.load_media(file_path)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f1016;
            }
            QWidget {
                color: #e2e8f0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }
            QMenuBar {
                background-color: #161622;
                color: #e2e8f0;
                border-bottom: 1px solid #28283a;
                padding: 1px;
            }
            QMenuBar::item {
                padding: 2px 6px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background-color: #2b2d42;
            }
            QMenu {
                background-color: #1c1d2a;
                color: #e2e8f0;
                border: 1px solid #2e3048;
                padding: 2px;
            }
            QMenu::item {
                padding: 4px 14px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #2563eb;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #28283a;
                border-radius: 4px;
                background-color: #181824;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #12121c;
                color: #94a3b8;
                padding: 4px 10px;
                font-weight: 600;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #181824;
                color: #60a5fa;
                border-bottom: 2px solid #3b82f6;
            }
            QLineEdit, QComboBox {
                background-color: #20202e;
                color: #f8fafc;
                border: 1px solid #333346;
                border-radius: 3px;
                padding: 3px 5px;
                font-size: 11px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #3b82f6;
                background-color: #252536;
            }
            QSpinBox {
                background-color: #20202e;
                color: #f8fafc;
                border: 1px solid #333346;
                border-radius: 3px;
                padding: 2px 3px;
                font-size: 11px;
            }
            QSpinBox:focus {
                border: 1px solid #3b82f6;
            }
            QComboBox QAbstractItemView {
                background-color: #20202e;
                color: #f8fafc;
                selection-background-color: #2563eb;
                padding: 2px;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #28283a;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #2563eb;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #60a5fa;
                border: 1px solid #93c5fd;
                width: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #bfdbfe;
            }
            QScrollBar:horizontal, QScrollBar:vertical {
                height: 8px;
                width: 8px;
                background: #14141e;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 4px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }
            QStatusBar {
                background-color: #12121c;
                color: #94a3b8;
                border-top: 1px solid #222232;
                padding: 1px;
            }
            QProgressDialog {
                background-color: #1a1a26;
                color: #e2e8f0;
            }
            QProgressBar {
                background-color: #20202e;
                border: 1px solid #333346;
                border-radius: 4px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 3px;
            }
        """)
