import os
import re
import subprocess
import tempfile
import cv2
from PIL import Image
import imageio_ffmpeg
from typing import Dict, Any, Optional, Callable, Tuple
from .watermark_engine import WatermarkEngine

class VideoEngine:
    """
    Motor de procesamiento de vídeo para extracción de fotogramas
    y renderizado de marcas de agua mediante FFmpeg y OpenCV.
    """

    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """
        Obtiene información técnica del vídeo: resolución, duración, FPS y frames.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el vídeo: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0.0

        cap.release()

        return {
            "width": width,
            "height": height,
            "fps": fps,
            "total_frames": total_frames,
            "duration": duration
        }

    @staticmethod
    def extract_frame_at_time(video_path: str, time_sec: float) -> Optional[Image.Image]:
        """
        Extrae un fotograma específico en el segundo indicado y lo devuelve como PIL Image (RGB).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        # Posicionar en milisegundos
        cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000.0)
        ret, frame = cap.read()
        cap.release()

        if ret and frame is not None:
            # OpenCV usa BGR, convertir a RGB para Pillow
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_frame)

        return None

    @classmethod
    def apply_watermark_to_video(
        cls,
        input_video: str,
        output_video: str,
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> bool:
        """
        Aplica la marca de agua al vídeo completo utilizando FFmpeg por hardware/multi-hilo
        y preservando la pista de audio original.
        """
        info = cls.get_video_info(input_video)
        base_w = info["width"]
        base_h = info["height"]
        duration = info["duration"]

        mode = config.get("mode", "text")
        preset = config.get("preset", "bottom_right")

        # 1. Generar elemento de marca de agua individual
        if mode == "text":
            element = WatermarkEngine.create_text_element(
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
            element = WatermarkEngine.create_logo_element(
                logo_path=config.get("logo_path", ""),
                scale_percent=config.get("scale", 20.0),
                base_w=base_w,
                base_h=base_h,
                opacity=config.get("opacity", 0.8),
                rotation=config.get("rotation", 0.0)
            )

        elem_w, elem_h = element.size

        # Calcular coordenadas (x, y)
        if preset == "custom":
            pos_x = int(config.get("pos_x", 20))
            pos_y = int(config.get("pos_y", 20))
        else:
            margin_x = int(config.get("margin_x", 30))
            margin_y = int(config.get("margin_y", 30))
            pos_x, pos_y = WatermarkEngine.calculate_preset_position(
                base_w, base_h, elem_w, elem_h, preset, margin_x, margin_y
            )

        # 2. Guardar la marca de agua temporalmente como PNG transparente
        temp_wm_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_wm_path = temp_wm_file.name
        temp_wm_file.close()

        try:
            element.save(temp_wm_path, "PNG")

            # 3. Construir comando FFmpeg optimizado
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

            # Asegurar coordenadas dentro de límites
            pos_x = max(0, min(pos_x, base_w - 1))
            pos_y = max(0, min(pos_y, base_h - 1))

            # Filtro overlay para superponer la marca de agua
            overlay_filter = f"[0:v][1:v]overlay=x={pos_x}:y={pos_y}[outv]"

            cmd = [
                ffmpeg_exe,
                "-y",                       # Sobrescribir archivo de salida
                "-i", input_video,          # Entrada 0: Vídeo original
                "-i", temp_wm_path,         # Entrada 1: Marca de agua PNG
                "-filter_complex", overlay_filter,
                "-map", "[outv]",           # Usar vídeo con overlay
                "-map", "0:a?",             # Copiar audio si existe, o ignorar si no hay
                "-c:a", "copy",             # Copia directa de audio sin pérdida ni recodificación
                "-c:v", "libx264",          # Códec de vídeo H.264
                "-pix_fmt", "yuv420p",      # Máxima compatibilidad de reproducción
                "-crf", "18",               # Calidad visual prácticamente sin pérdida (CRF 18)
                "-preset", "fast",          # Velocidad de codificación óptima
                output_video
            ]

            # Iniciar proceso con lectura de stderr para la barra de progreso
            # Ocultar ventana de consola en Windows con CREATE_NO_WINDOW
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=creationflags,
                encoding='utf-8',
                errors='replace'
            )

            # Patrón para extraer el tiempo actual procesado (time=00:01:23.45)
            time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")

            while True:
                if cancel_check and cancel_check():
                    proc.terminate()
                    proc.kill()
                    return False

                line = proc.stderr.readline()
                if not line and proc.poll() is not None:
                    break

                if line and duration > 0:
                    match = time_pattern.search(line)
                    if match:
                        hours = float(match.group(1))
                        minutes = float(match.group(2))
                        seconds = float(match.group(3))
                        current_sec = hours * 3600 + minutes * 60 + seconds
                        progress = min(1.0, current_sec / duration)
                        if progress_callback:
                            progress_callback(progress)

            retcode = proc.wait()
            if retcode != 0:
                raise RuntimeError(f"FFmpeg terminó con código de error {retcode}")

            if progress_callback:
                progress_callback(1.0)

            return True

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_wm_path):
                try:
                    os.remove(temp_wm_path)
                except Exception:
                    pass
