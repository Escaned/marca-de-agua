"""
src/gui/preview_canvas.py
WatermarkStudio — Lienzo Gráfico Interactivo de Previsualización (Dark Slate / Obsidian)
Soporte completo para arrastre libre de marca de agua, barra flotante de zoom y timeline de vídeo.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QSlider, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QPixmap, QImage, QCursor, QPen, QBrush
)
from PIL import Image


class DraggableWatermarkItem(QGraphicsPixmapItem):
    """
    Elemento gráfico de marca de agua arrastrable libremente con caja
    delimitadora interactiva, guías sutiles y emisión de posición en tiempo real.
    """
    def __init__(self, parent_canvas, parent=None):
        super().__init__(parent)
        self.parent_canvas = parent_canvas
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setZValue(10)  # Siempre por encima de la imagen o vídeo base
        self._is_selected = True

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.parent_canvas:
                pos = self.pos()
                self.parent_canvas.on_watermark_moved(pos.x(), pos.y())
        return super().itemChange(change, value)

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        # Dibujar caja delimitadora y líneas guía sutiles en cyan eléctrico
        if self.isSelected() or self._is_selected:
            painter.save()
            rect = self.boundingRect()
            pen = QPen(QColor("#38bdf8"), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

            # Tiradores de esquina sutiles
            handle_size = 6
            painter.setBrush(QBrush(QColor("#38bdf8")))
            painter.setPen(QPen(QColor("#0f1016"), 1))
            corners = [
                rect.topLeft(), rect.topRight(),
                rect.bottomLeft(), rect.bottomRight()
            ]
            for pt in corners:
                painter.drawRect(QRectF(pt.x() - handle_size/2, pt.y() - handle_size/2, handle_size, handle_size))
            painter.restore()


class FloatingZoomBar(QFrame):
    """Barra flotante translúcida superior izquierda para control rápido de escala y visualización."""
    def __init__(self, parent_canvas):
        super().__init__(parent_canvas)
        self.parent_canvas = parent_canvas
        self.setObjectName("floating_zoom_bar")
        self.setStyleSheet("""
            QFrame#floating_zoom_bar {
                background-color: rgba(20, 20, 32, 0.94);
                border: 1px solid #33334d;
                border-radius: 8px;
            }
            QFrame#floating_zoom_bar QPushButton {
                background-color: #242438;
                border: 1px solid #383852;
                color: #f1f5f9;
                font-weight: 600;
                font-size: 12px;
                padding: 4px 10px;
                border-radius: 5px;
                min-height: 22px;
            }
            QFrame#floating_zoom_bar QPushButton:hover {
                background-color: #31314e;
                border-color: #60a5fa;
                color: #60a5fa;
            }
            QFrame#floating_zoom_bar QPushButton:pressed {
                background-color: #2563eb;
                color: #ffffff;
            }
            QFrame#floating_zoom_bar QLabel {
                color: #94a3b8;
                font-size: 12px;
                font-weight: 600;
                padding: 0 4px;
                min-width: 42px;
                background: transparent;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        self.btn_fit = QPushButton("⤢ Ajustar")
        self.btn_fit.setToolTip("Ajustar imagen o vídeo a la ventana (Ctrl+0)")
        self.btn_fit.setMinimumWidth(80)
        self.btn_fit.clicked.connect(self.parent_canvas.fit_in_view)

        self.btn_1x = QPushButton("1:1")
        self.btn_1x.setToolTip("Escala original al 100% (Ctrl+1)")
        self.btn_1x.setMinimumWidth(38)
        self.btn_1x.clicked.connect(self.parent_canvas.reset_zoom)

        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setToolTip("Reducir zoom")
        self.btn_zoom_out.setFixedWidth(28)
        self.btn_zoom_out.clicked.connect(self.parent_canvas.zoom_out)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setToolTip("Aumentar zoom")
        self.btn_zoom_in.setFixedWidth(28)
        self.btn_zoom_in.clicked.connect(self.parent_canvas.zoom_in)

        layout.addWidget(self.btn_fit)
        layout.addWidget(self.btn_1x)
        layout.addWidget(self.btn_zoom_out)
        layout.addWidget(self.lbl_zoom)
        layout.addWidget(self.btn_zoom_in)
        self.adjustSize()

    def update_zoom_text(self, factor_percent: int):
        self.lbl_zoom.setText(f"{factor_percent}%")


class PreviewCanvas(QWidget):
    """
    Lienzo interactivo central basado en QGraphicsView.
    Admite zoom con rueda de ratón, paneo fluido, arrastre de marca de agua
    y controles de reproducción para medios de vídeo.
    """
    position_changed = pyqtSignal(float, float)
    time_seeked = pyqtSignal(float)
    trim_range_changed = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_zoom = 1.0
        self._media_duration = 0.0
        self._is_video = False
        self._is_playing = False
        self._trim_start = 0.0
        self._trim_end = 0.0

        # Timer para simulación fluida de reproducción de vídeo
        self._play_timer = QTimer(self)
        self._play_timer.setInterval(100)  # 10 fps de preview interactivo
        self._play_timer.timeout.connect(self._on_play_tick)

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. ESCENA Y VISTA GRÁFICA
        # -------------------------------------------------------------
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setObjectName("canvas_view")
        self.view.setStyleSheet("""
            QGraphicsView#canvas_view {
                background-color: #14141c;
                border: 1px solid #28283a;
                border-radius: 6px;
            }
        """)
        self.view.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

        # Eventos de ratón para Paneado y Zoom
        self.view.wheelEvent = self._handle_wheel_zoom
        self.view.mousePressEvent = self._handle_mouse_press
        self.view.mouseMoveEvent = self._handle_mouse_move
        self.view.mouseReleaseEvent = self._handle_mouse_release

        # Capas de la escena
        self.base_pixmap_item = QGraphicsPixmapItem()
        self.base_pixmap_item.setZValue(0)
        self.scene.addItem(self.base_pixmap_item)

        self.watermark_item = DraggableWatermarkItem(self)
        self.scene.addItem(self.watermark_item)

        main_layout.addWidget(self.view, 1)

        # -------------------------------------------------------------
        # 2. BARRA FLOTANTE DE ZOOM
        # -------------------------------------------------------------
        self.floating_zoom = FloatingZoomBar(self)
        self.floating_zoom.move(14, 14)
        self.floating_zoom.raise_()

        # -------------------------------------------------------------
        # 3. BARRA INFERIOR DE VÍDEO (Timeline & Transporte & Recorte IN/OUT)
        # -------------------------------------------------------------
        self.frame_video = QFrame()
        self.frame_video.setFixedHeight(46)
        self.frame_video.setStyleSheet("""
            QFrame {
                background-color: #141420;
                border-top: 1px solid #28283a;
                padding: 2px 8px;
            }
            QPushButton.trim_btn {
                background-color: #202032;
                color: #e2e8f0;
                border: 1px solid #383852;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
                min-height: 22px;
            }
            QPushButton.trim_btn:hover {
                background-color: #2d2d48;
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        video_layout = QHBoxLayout(self.frame_video)
        video_layout.setContentsMargins(6, 4, 6, 4)
        video_layout.setSpacing(8)

        self.btn_play_pause = QPushButton("▶")
        self.btn_play_pause.setFixedSize(36, 28)
        self.btn_play_pause.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)

        self.slider_video = QSlider(Qt.Orientation.Horizontal)
        self.slider_video.setRange(0, 1000)
        self.slider_video.setValue(0)
        self.slider_video.valueChanged.connect(self._on_seek_moved)

        self.lbl_time = QLabel("00:00.00 / 00:00.00")
        self.lbl_time.setStyleSheet("color: #93c5fd; font-family: 'Consolas', monospace; font-size: 11px; font-weight: 600; min-width: 125px;")

        # Botones de recorte de vídeo (Punto IN y Punto OUT)
        self.btn_set_in = QPushButton("⭢[ Inicio")
        self.btn_set_in.setProperty("class", "trim_btn")
        self.btn_set_in.setToolTip("Fijar el segundo actual como INICIO del vídeo con marca")
        self.btn_set_in.clicked.connect(self._on_set_in_clicked)

        self.btn_set_out = QPushButton("]⭠ Fin")
        self.btn_set_out.setProperty("class", "trim_btn")
        self.btn_set_out.setToolTip("Fijar el segundo actual como FIN del vídeo con marca")
        self.btn_set_out.clicked.connect(self._on_set_out_clicked)

        self.btn_reset_trim = QPushButton("↺ Todo")
        self.btn_reset_trim.setProperty("class", "trim_btn")
        self.btn_reset_trim.setToolTip("Restablecer al 100% del vídeo completo")
        self.btn_reset_trim.clicked.connect(self._on_reset_trim_clicked)

        self.lbl_trim_info = QLabel("✂ Recorte: Todo")
        self.lbl_trim_info.setStyleSheet("color: #38bdf8; font-family: 'Consolas', monospace; font-size: 11px; font-weight: 600; padding: 0 4px;")

        video_layout.addWidget(self.btn_play_pause)
        video_layout.addWidget(self.slider_video, 1)
        video_layout.addWidget(self.lbl_time)
        video_layout.addWidget(self.btn_set_in)
        video_layout.addWidget(self.btn_set_out)
        video_layout.addWidget(self.btn_reset_trim)
        video_layout.addWidget(self.lbl_trim_info)

        main_layout.addWidget(self.frame_video)
        self.frame_video.hide()  # Oculto por defecto hasta cargar un vídeo

    # -----------------------------------------------------------------
    # CONTROL DE ZOOM Y NAVEGACIÓN
    # -----------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.floating_zoom.adjustSize()
        self.floating_zoom.move(14, 14)

    def _handle_wheel_zoom(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.view.scale(factor, factor)
        self._current_zoom *= factor
        self.floating_zoom.update_zoom_text(int(round(self._current_zoom * 100)))

    def zoom_in(self):
        self.view.scale(1.2, 1.2)
        self._current_zoom *= 1.2
        self.floating_zoom.update_zoom_text(int(round(self._current_zoom * 100)))

    def zoom_out(self):
        self.view.scale(1 / 1.2, 1 / 1.2)
        self._current_zoom /= 1.2
        self.floating_zoom.update_zoom_text(int(round(self._current_zoom * 100)))

    def reset_zoom(self):
        self.view.resetTransform()
        self._current_zoom = 1.0
        self.floating_zoom.update_zoom_text(100)

    def fit_in_view(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isEmpty():
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            # Calcular zoom efectivo
            self._current_zoom = self.view.transform().m11()
            self.floating_zoom.update_zoom_text(int(round(self._current_zoom * 100)))

    # -----------------------------------------------------------------
    # PANEO (CLIC DERECHO O RUEDA CENTRAL)
    # -----------------------------------------------------------------
    def _handle_mouse_press(self, event):
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._pan_active = True
            self._pan_start = event.pos()
            self.view.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            QGraphicsView.mousePressEvent(self.view, event)

    def _handle_mouse_move(self, event):
        if getattr(self, "_pan_active", False):
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().value() - delta.x())
            self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            QGraphicsView.mouseMoveEvent(self.view, event)

    def _handle_mouse_release(self, event):
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._pan_active = False
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            QGraphicsView.mouseReleaseEvent(self.view, event)

    # -----------------------------------------------------------------
    # MARCA DE AGUA: ACTUALIZACIÓN Y ARRASTRE
    # -----------------------------------------------------------------
    def on_watermark_moved(self, x: float, y: float):
        """Notifica hacia MainWindow para sincronizar el panel lateral."""
        self.position_changed.emit(x, y)

    def set_base_image(self, pil_image: Image.Image, is_video: bool = False, duration: float = 0.0):
        """Establece la imagen de fondo base desde un PIL.Image."""
        self._is_video = is_video
        self._media_duration = duration
        self._trim_start = 0.0
        self._trim_end = duration
        self._is_playing = False
        self._play_timer.stop()
        self.btn_play_pause.setText("▶")

        qimg = self.pil_to_qimage(pil_image)
        pixmap = QPixmap.fromImage(qimg)
        self.base_pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))

        if is_video:
            self.frame_video.show()
            self.slider_video.blockSignals(True)
            self.slider_video.setValue(0)
            self.slider_video.blockSignals(False)
            self.update_video_time_display(0.0)
            self._update_trim_display()
        else:
            self.frame_video.hide()

        self.fit_in_view()

    def set_trim_range(self, start_sec: float, end_sec: float):
        """Establece el rango de recorte externamente."""
        if self._media_duration <= 0:
            return
        self._trim_start = max(0.0, min(start_sec, self._media_duration))
        self._trim_end = max(self._trim_start, min(end_sec, self._media_duration))
        self._update_trim_display()

    def get_trim_range(self) -> tuple[float, float]:
        """Devuelve (start_sec, end_sec)."""
        return self._trim_start, self._trim_end

    def _on_set_in_clicked(self):
        """Fija la posición actual del slider como punto de Inicio (IN)."""
        if self._media_duration <= 0:
            return
        current_sec = (self.slider_video.value() / 1000.0) * self._media_duration
        if current_sec >= self._trim_end:
            self._trim_end = self._media_duration
        self._trim_start = current_sec
        self._update_trim_display()
        self.trim_range_changed.emit(self._trim_start, self._trim_end)

    def _on_set_out_clicked(self):
        """Fija la posición actual del slider como punto de Fin (OUT)."""
        if self._media_duration <= 0:
            return
        current_sec = (self.slider_video.value() / 1000.0) * self._media_duration
        if current_sec <= self._trim_start:
            self._trim_start = 0.0
        self._trim_end = current_sec
        self._update_trim_display()
        self.trim_range_changed.emit(self._trim_start, self._trim_end)

    def _on_reset_trim_clicked(self):
        """Restablece el recorte a la duración completa del vídeo."""
        self._trim_start = 0.0
        self._trim_end = self._media_duration
        self._update_trim_display()
        self.trim_range_changed.emit(self._trim_start, self._trim_end)

    def _update_trim_display(self):
        """Actualiza la etiqueta con el intervalo recortado actual."""
        if self._media_duration <= 0:
            self.lbl_trim_info.setText("✂ Recorte: Todo")
            return

        is_trimmed = (self._trim_start > 0.05) or (self._trim_end < self._media_duration - 0.05)
        if not is_trimmed:
            self.lbl_trim_info.setText("✂ Todo el vídeo")
            self.lbl_trim_info.setStyleSheet("color: #94a3b8; font-family: 'Consolas', monospace; font-size: 11px; font-weight: 600;")
        else:
            in_m, in_s = divmod(int(self._trim_start), 60)
            in_ms = int((self._trim_start - int(self._trim_start)) * 100)
            out_m, out_s = divmod(int(self._trim_end), 60)
            out_ms = int((self._trim_end - int(self._trim_end)) * 100)
            dur = self._trim_end - self._trim_start
            self.lbl_trim_info.setText(f"✂ [{in_m:02d}:{in_s:02d}.{in_ms:02d} ➔ {out_m:02d}:{out_s:02d}.{out_ms:02d}] ({dur:.1f}s)")
            self.lbl_trim_info.setStyleSheet("color: #38bdf8; font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700;")

    def update_base_frame(self, pil_image: Image.Image):
        """Actualiza el fotograma de vídeo actual en tiempo real sin reiniciar zoom ni vista."""
        qimg = self.pil_to_qimage(pil_image)
        pixmap = QPixmap.fromImage(qimg)
        self.base_pixmap_item.setPixmap(pixmap)

    def set_watermark_pixmap(self, pil_image: Image.Image, x: float = None, y: float = None):
        """Actualiza el gráfico y opcionalmente la posición de la marca."""
        qimg = self.pil_to_qimage(pil_image)
        pixmap = QPixmap.fromImage(qimg)
        self.watermark_item.setPixmap(pixmap)
        if x is not None and y is not None:
            self.watermark_item.setPos(QPointF(x, y))

    @staticmethod
    def pil_to_qimage(pil_image: Image.Image) -> QImage:
        """Conversión segura de PIL.Image a QImage con formato RGBA8888."""
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGBA8888)
        return qimage.copy()

    # -----------------------------------------------------------------
    # CONTROL DE LÍNEA DE TIEMPO DE VÍDEO
    # -----------------------------------------------------------------
    def toggle_play_pause(self):
        if not self._is_video or self._media_duration <= 0:
            return

        if self._is_playing:
            self._play_timer.stop()
            self.btn_play_pause.setText("▶")
            self._is_playing = False
        else:
            if self.slider_video.value() >= 1000:
                self.slider_video.setValue(0)
            self._play_timer.start()
            self.btn_play_pause.setText("⏸")
            self._is_playing = True

    def _on_play_tick(self):
        if not self._is_video or self._media_duration <= 0:
            self._play_timer.stop()
            return

        current_val = self.slider_video.value()
        # Avanzar en función de la duración real (tick cada 100ms = 0.1s)
        step = int(max(1, (0.1 / self._media_duration) * 1000))
        next_val = current_val + step
        if next_val >= 1000:
            self.slider_video.setValue(1000)
            self.toggle_play_pause()
        else:
            self.slider_video.setValue(next_val)

    def _on_seek_moved(self, value: int):
        current_sec = (value / 1000.0) * self._media_duration
        self.update_video_time_display(current_sec)
        self.time_seeked.emit(current_sec)

    def update_video_time_display(self, current_sec: float):
        cur_min, cur_s = divmod(int(current_sec), 60)
        cur_ms = int((current_sec - int(current_sec)) * 100)
        dur_min, dur_s = divmod(int(self._media_duration), 60)
        dur_ms = int((self._media_duration - int(self._media_duration)) * 100)
        self.lbl_time.setText(f"{cur_min:02d}:{cur_s:02d}.{cur_ms:02d} / {dur_min:02d}:{dur_s:02d}.{dur_ms:02d}")
