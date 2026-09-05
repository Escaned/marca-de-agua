import io
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsItem, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame,
    QSlider, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QPoint, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QWheelEvent, QMouseEvent, QCursor
from PIL import Image
from typing import Optional, Dict, Any
from ..core.watermark_engine import WatermarkEngine

class DraggableWatermarkItem(QGraphicsPixmapItem):
    """
    Elemento gráfico de la marca de agua que permite arrastre con el ratón
    directamente sobre el lienzo interactivo.
    """
    def __init__(self, parent_canvas):
        super().__init__()
        self.canvas = parent_canvas
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            self.canvas.on_watermark_drag_start()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            super().mouseMoveEvent(event)
            self.canvas.on_watermark_dragged(self.pos())
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)
            self.canvas.on_watermark_drag_end(self.pos())
        else:
            event.ignore()


class PreviewCanvas(QWidget):
    """
    Contenedor principal del lienzo visual que incluye:
    - Lienzo gráfico interactivo con arrastre de marca de agua y pan.
    - Barra flotante de zoom (Ajustar, 1:1, +, -).
    - Barra de reproducción / scrubber de vídeo (aparece solo cuando hay un vídeo cargado).
    """
    position_changed = pyqtSignal(float, float)
    time_seeked = pyqtSignal(float) # segundo actual seleccionado

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.init_ui()

        self.bg_item: Optional[QGraphicsPixmapItem] = None
        self.watermark_item: Optional[DraggableWatermarkItem] = None

        self.pil_base_image: Optional[Image.Image] = None
        self.pil_watermark_element: Optional[Image.Image] = None
        self.current_config: Dict[str, Any] = {}

        self.is_video_mode = False
        self.video_duration = 0.0
        self.current_video_time = 0.0
        self.is_playing = False

        # Timer para reproducción continua del vídeo
        self.play_timer = QTimer(self)
        self.play_timer.setInterval(100) # 10 fps en preview para fluidez ligera
        self.play_timer.timeout.connect(self.advance_playback)

        self.is_panning = False
        self.pan_start_pos = QPoint()
        self.is_custom_pos = False

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # 1. Vista gráfica principal
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self.view.setStyleSheet("""
            QGraphicsView {
                background-color: #14141c;
                border: 1px solid #28283a;
                border-radius: 6px;
            }
        """)

        # Eventos del view
        self.view.wheelEvent = self.on_view_wheel
        self.view.mousePressEvent = self.on_view_mouse_press
        self.view.mouseMoveEvent = self.on_view_mouse_move
        self.view.mouseReleaseEvent = self.on_view_mouse_release
        self.view.resizeEvent = self.on_view_resize

        main_layout.addWidget(self.view, 1)

        # 2. Barra flotante de zoom
        self.create_floating_toolbar()

        # 3. Barra inferior de control de vídeo (inicialmente oculta)
        self.create_video_timeline(main_layout)

    def create_floating_toolbar(self):
        self.toolbar_frame = QFrame(self.view)
        self.toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 26, 38, 0.85);
                border: 1px solid #3b3b52;
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton {
                background-color: #242436;
                color: #f1f5f9;
                border: 1px solid #3b3b50;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
                color: white;
            }
        """)
        tb_layout = QHBoxLayout(self.toolbar_frame)
        tb_layout.setContentsMargins(4, 4, 4, 4)
        tb_layout.setSpacing(4)

        btn_fit = QPushButton("⛶ Ajustar")
        btn_fit.setToolTip("Ajustar imagen completa a la ventana")
        btn_fit.clicked.connect(self.fit_in_view)
        tb_layout.addWidget(btn_fit)

        btn_orig = QPushButton("1:1")
        btn_orig.setToolTip("Tamaño real 100%")
        btn_orig.clicked.connect(self.reset_zoom)
        tb_layout.addWidget(btn_orig)

        btn_zin = QPushButton("➕")
        btn_zin.setToolTip("Acercar Zoom")
        btn_zin.clicked.connect(self.zoom_in)
        tb_layout.addWidget(btn_zin)

        btn_zout = QPushButton("➖")
        btn_zout.setToolTip("Alejar Zoom")
        btn_zout.clicked.connect(self.zoom_out)
        tb_layout.addWidget(btn_zout)

        self.toolbar_frame.adjustSize()
        self.toolbar_frame.move(12, 12)

    def create_video_timeline(self, parent_layout: QVBoxLayout):
        """Crea la barra inferior interactiva para reproducción de vídeo."""
        self.timeline_frame = QFrame(self)
        self.timeline_frame.setFixedHeight(38)
        self.timeline_frame.setStyleSheet("""
            QFrame {
                background-color: #181824;
                border: 1px solid #28283a;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                font-size: 11px;
                padding: 2px 8px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        tl_layout = QHBoxLayout(self.timeline_frame)
        tl_layout.setContentsMargins(6, 2, 6, 2)
        tl_layout.setSpacing(8)

        self.btn_play_pause = QPushButton("▶ Play")
        self.btn_play_pause.setFixedWidth(60)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        tl_layout.addWidget(self.btn_play_pause)

        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, 1000)
        self.slider_timeline.setValue(0)
        self.slider_timeline.sliderMoved.connect(self.on_slider_seek)
        self.slider_timeline.sliderPressed.connect(self.on_slider_pressed)
        tl_layout.addWidget(self.slider_timeline, 1)

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("color: #93c5fd; font-weight: bold; font-size: 11px;")
        tl_layout.addWidget(self.lbl_time)

        parent_layout.addWidget(self.timeline_frame)
        self.timeline_frame.hide()

    def set_video_mode(self, is_video: bool, duration: float = 0.0):
        """Activa o desactiva la barra de tiempo según sea vídeo o imagen."""
        self.is_video_mode = is_video
        self.video_duration = duration
        self.current_video_time = 0.0
        self.is_playing = False
        self.play_timer.stop()
        self.btn_play_pause.setText("▶ Play")

        if is_video:
            self.timeline_frame.show()
            self.update_time_label()
        else:
            self.timeline_frame.hide()

    def update_time_label(self):
        cur_min, cur_sec = divmod(int(self.current_video_time), 60)
        tot_min, tot_sec = divmod(int(self.video_duration), 60)
        self.lbl_time.setText(f"{cur_min:02d}:{cur_sec:02d} / {tot_min:02d}:{tot_sec:02d}")

    def toggle_play_pause(self):
        if not self.is_video_mode or self.video_duration <= 0:
            return

        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play_pause.setText("⏸ Pausa")
            self.play_timer.start()
        else:
            self.btn_play_pause.setText("▶ Play")
            self.play_timer.stop()

    def advance_playback(self):
        if not self.is_video_mode or self.video_duration <= 0:
            return

        self.current_video_time += 0.2
        if self.current_video_time > self.video_duration:
            self.current_video_time = 0.0

        # Actualizar slider y solicitar nuevo fotograma
        slider_val = int((self.current_video_time / self.video_duration) * 1000)
        self.slider_timeline.blockSignals(True)
        self.slider_timeline.setValue(slider_val)
        self.slider_timeline.blockSignals(False)

        self.update_time_label()
        self.time_seeked.emit(self.current_video_time)

    def on_slider_pressed(self):
        if self.is_playing:
            self.toggle_play_pause()

    def on_slider_seek(self, value: int):
        if self.video_duration > 0:
            self.current_video_time = (value / 1000.0) * self.video_duration
            self.update_time_label()
            self.time_seeked.emit(self.current_video_time)

    def set_base_image(self, pil_image: Image.Image, keep_viewport: bool = False):
        """Carga o actualiza el fotograma/imagen base en el lienzo."""
        self.pil_base_image = pil_image

        qimg = self.pil_to_qimage(pil_image)
        pixmap = QPixmap.fromImage(qimg)

        if not self.bg_item:
            self.scene.clear()
            self.bg_item = QGraphicsPixmapItem(pixmap)
            self.bg_item.setZValue(0)
            self.scene.addItem(self.bg_item)
            self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

            self.watermark_item = DraggableWatermarkItem(self)
            self.watermark_item.setZValue(10)
            self.scene.addItem(self.watermark_item)

            self.fit_in_view()
        else:
            self.bg_item.setPixmap(pixmap)
            if not keep_viewport:
                self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

    def update_watermark(self, config: Dict[str, Any]):
        """Actualiza la apariencia y posición de la marca de agua."""
        if not self.pil_base_image or not self.watermark_item:
            return

        self.current_config = config
        mode = config.get("mode", "text")
        preset = config.get("preset", "bottom_right")

        if mode == "text":
            self.pil_watermark_element = WatermarkEngine.create_text_element(
                text=config.get("text", "Marca de Agua"),
                font_path=config.get("font_path", ""),
                font_size=config.get("font_size", 40),
                color_rgb=config.get("color", (255, 255, 255)),
                opacity=config.get("opacity", 0.8),
                rotation=config.get("rotation", 0.0),
                has_shadow=config.get("shadow", False),
                has_outline=config.get("outline", False),
                is_bold=config.get("is_bold", False),
                is_italic=config.get("is_italic", False),
                is_underline=config.get("is_underline", False)
            )
        else:
            self.pil_watermark_element = WatermarkEngine.create_logo_element(
                logo_path=config.get("logo_path", ""),
                scale_percent=config.get("scale", 20.0),
                base_w=self.pil_base_image.width,
                base_h=self.pil_base_image.height,
                opacity=config.get("opacity", 0.8),
                rotation=config.get("rotation", 0.0)
            )

        wm_qimg = self.pil_to_qimage(self.pil_watermark_element)
        wm_pixmap = QPixmap.fromImage(wm_qimg)
        self.watermark_item.setPixmap(wm_pixmap)

        elem_w = self.pil_watermark_element.width
        elem_h = self.pil_watermark_element.height
        base_w = self.pil_base_image.width
        base_h = self.pil_base_image.height

        if preset != "custom":
            margin_x = int(config.get("margin_x", 30))
            margin_y = int(config.get("margin_y", 30))
            x, y = WatermarkEngine.calculate_preset_position(
                base_w, base_h, elem_w, elem_h, preset, margin_x, margin_y
            )
            self.watermark_item.setPos(x, y)
        else:
            pos_x = config.get("pos_x", 20)
            pos_y = config.get("pos_y", 20)
            self.watermark_item.setPos(pos_x, pos_y)

    def on_watermark_drag_start(self):
        self.is_custom_pos = True

    def on_watermark_dragged(self, pos: QPointF):
        if self.pil_base_image:
            self.position_changed.emit(pos.x(), pos.y())

    def on_watermark_drag_end(self, pos: QPointF):
        if self.pil_base_image:
            self.position_changed.emit(pos.x(), pos.y())

    def fit_in_view(self):
        if self.scene.items():
            self.view.resetTransform()
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def reset_zoom(self):
        self.view.resetTransform()

    def zoom_in(self):
        self.view.scale(1.2, 1.2)

    def zoom_out(self):
        self.view.scale(1 / 1.2, 1 / 1.2)

    def on_view_resize(self, event):
        if hasattr(self, 'toolbar_frame'):
            self.toolbar_frame.move(12, 12)

    def on_view_wheel(self, event: QWheelEvent):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.view.scale(factor, factor)

    def on_view_mouse_press(self, event: QMouseEvent):
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self.is_panning = True
            self.pan_start_pos = event.pos()
            self.view.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            QGraphicsView.mousePressEvent(self.view, event)

    def on_view_mouse_move(self, event: QMouseEvent):
        if self.is_panning:
            delta = event.pos() - self.pan_start_pos
            self.pan_start_pos = event.pos()
            self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().value() - delta.x())
            self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            QGraphicsView.mouseMoveEvent(self.view, event)

    def on_view_mouse_release(self, event: QMouseEvent):
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self.is_panning = False
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            QGraphicsView.mouseReleaseEvent(self.view, event)

    @staticmethod
    def pil_to_qimage(pil_img: Image.Image) -> QImage:
        if pil_img.mode != "RGBA":
            pil_img = pil_img.convert("RGBA")
        data = pil_img.tobytes("raw", "RGBA")
        qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        return qimage.copy()
