from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import math
from typing import Tuple, Optional, Dict, Any

class WatermarkEngine:
    """
    Motor de renderizado de marcas de agua para imágenes utilizando Pillow.
    Soporta marcas de agua de texto e imagen/logo con soporte completo de:
    - Tipografía personalizada
    - Opacidad / Transparencia alfa
    - Color RGBA
    - Sombras y contornos
    - Rotación sin recorte
    - Posicionamiento predefinido y libre (coordenadas relativas o absolutas)
    """

    PRESET_POSITIONS = {
        "top_left": "Arriba Izquierda",
        "top_center": "Arriba Centro",
        "top_right": "Arriba Derecha",
        "center_left": "Centro Izquierda",
        "center": "Centro",
        "center_right": "Centro Derecha",
        "bottom_left": "Abajo Izquierda",
        "bottom_center": "Abajo Centro",
        "bottom_right": "Abajo Derecha",
        "custom": "Libre / Personalizado"
    }

    @staticmethod
    def calculate_preset_position(
        base_w: int, base_h: int, item_w: int, item_h: int,
        preset: str, margin_x: int = 20, margin_y: int = 20
    ) -> Tuple[int, int]:
        """Calcula la posición (x, y) basada en un preajuste de 9 cuadrantes."""
        if preset == "top_left":
            return margin_x, margin_y
        elif preset == "top_center":
            return (base_w - item_w) // 2, margin_y
        elif preset == "top_right":
            return base_w - item_w - margin_x, margin_y
        elif preset == "center_left":
            return margin_x, (base_h - item_h) // 2
        elif preset == "center":
            return (base_w - item_w) // 2, (base_h - item_h) // 2
        elif preset == "center_right":
            return base_w - item_w - margin_x, (base_h - item_h) // 2
        elif preset == "bottom_left":
            return margin_x, base_h - item_h - margin_y
        elif preset == "bottom_center":
            return (base_w - item_w) // 2, base_h - item_h - margin_y
        elif preset == "bottom_right":
            return base_w - item_w - margin_x, base_h - item_h - margin_y
        return margin_x, margin_y

    @classmethod
    def create_text_element(
        cls,
        text: str,
        font_path: str,
        font_size: int,
        color_rgb: Tuple[int, int, int],
        opacity: float,
        rotation: float = 0.0,
        has_shadow: bool = False,
        shadow_color: Tuple[int, int, int] = (0, 0, 0),
        shadow_offset: Tuple[int, int] = (3, 3),
        has_outline: bool = False,
        outline_color: Tuple[int, int, int] = (0, 0, 0),
        outline_width: int = 2,
        is_bold: bool = False,
        is_italic: bool = False,
        is_underline: bool = False
    ) -> Image.Image:
        """
        Crea una imagen RGBA individual con el texto estilizado (color, negrita, cursiva, subrayado), sombreado y rotado.
        """
        if not text.strip():
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()

        # Medir tamaño del texto
        dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Grosor de negrita simulado
        bold_stroke = max(1, round(font_size * 0.04)) if is_bold else 0

        # Margen para padding, contorno, subrayado y sombra
        underline_extra = max(4, int(font_size * 0.12)) if is_underline else 0
        padding = max(12, outline_width * 2, bold_stroke * 2, abs(shadow_offset[0]) + 10, abs(shadow_offset[1]) + 10)
        layer_w = text_w + padding * 2 + bold_stroke * 2
        layer_h = text_h + padding * 2 + underline_extra + bold_stroke * 2

        layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        # Coordenadas base dentro del layer
        text_x = padding - bbox[0]
        text_y = padding - bbox[1]

        alpha_int = int(max(0.0, min(1.0, opacity)) * 255)
        text_rgba = (*color_rgb, alpha_int)

        # 1. Dibujar sombra si está activa
        if has_shadow:
            shadow_alpha = int(alpha_int * 0.6)
            s_rgba = (*shadow_color, shadow_alpha)
            sx = text_x + shadow_offset[0]
            sy = text_y + shadow_offset[1]
            if bold_stroke > 0:
                draw.text(
                    (sx, sy),
                    text,
                    font=font,
                    fill=s_rgba,
                    stroke_width=bold_stroke,
                    stroke_fill=s_rgba
                )
            else:
                draw.text(
                    (sx, sy),
                    text,
                    font=font,
                    fill=s_rgba
                )
            if is_underline:
                u_thick = max(2, int(font_size * 0.05))
                u_y = sy + text_h + max(2, int(font_size * 0.04))
                draw.line([(sx, u_y), (sx + text_w, u_y)], fill=s_rgba, width=u_thick)

        # 2. Dibujar contorno o texto normal (con soporte para negrita)
        if has_outline and outline_width > 0:
            outline_alpha = int(alpha_int * 0.8)
            o_rgba = (*outline_color, outline_alpha)
            total_stroke = outline_width + bold_stroke
            draw.text(
                (text_x, text_y),
                text,
                font=font,
                fill=text_rgba,
                stroke_width=total_stroke,
                stroke_fill=o_rgba
            )
        elif bold_stroke > 0:
            draw.text(
                (text_x, text_y),
                text,
                font=font,
                fill=text_rgba,
                stroke_width=bold_stroke,
                stroke_fill=text_rgba
            )
        else:
            draw.text((text_x, text_y), text, font=font, fill=text_rgba)

        # 3. Dibujar subrayado
        if is_underline:
            u_thick = max(2, int(font_size * 0.05))
            u_y = text_y + text_h + max(2, int(font_size * 0.04))
            draw.line([(text_x, u_y), (text_x + text_w, u_y)], fill=text_rgba, width=u_thick)

        # 4. Cursiva (Inclinación por transformación afín)
        if is_italic:
            shear = 0.24
            extra_w = int(layer.height * shear) + 6
            expanded = Image.new("RGBA", (layer.width + extra_w, layer.height), (0, 0, 0, 0))
            expanded.paste(layer, (0, 0))
            matrix = (1, shear, -shear * layer.height, 0, 1, 0)
            layer = expanded.transform(
                (layer.width + extra_w, layer.height),
                Image.Transform.AFFINE,
                matrix,
                resample=Image.Resampling.BICUBIC
            )

        # 5. Rotación (con expansión para evitar cortes)
        if rotation != 0:
            layer = layer.rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=True)

        return layer

    @classmethod
    def create_logo_element(
        cls,
        logo_path: str,
        scale_percent: float, # ej: 10% a 100% relativo o tamaño directo
        base_w: int,
        base_h: int,
        opacity: float,
        rotation: float = 0.0
    ) -> Image.Image:
        """
        Carga, escala, ajusta la opacidad y rota un logo/imagen.
        """
        try:
            logo = Image.open(logo_path).convert("RGBA")
        except Exception:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        # Calcular nuevo tamaño según el porcentaje respecto a la imagen base
        target_w = max(10, int(base_w * (scale_percent / 100.0)))
        aspect_ratio = logo.height / logo.width
        target_h = max(10, int(target_w * aspect_ratio))

        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Ajustar opacidad
        if opacity < 1.0:
            alpha = logo.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            logo.putalpha(alpha)

        # Rotar
        if rotation != 0:
            logo = logo.rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=True)

        return logo

    @classmethod
    def apply_watermark(
        cls,
        base_image: Image.Image,
        config: Dict[str, Any]
    ) -> Image.Image:
        """
        Aplica la configuración completa de marca de agua sobre una imagen base.
        Retorna una nueva imagen compuesta.
        """
        # Trabajar en modo RGBA para composición alfa perfecta
        composed = base_image.convert("RGBA")
        overlay = Image.new("RGBA", composed.size, (0, 0, 0, 0))

        mode = config.get("mode", "text") # "text" o "logo"
        preset = config.get("preset", "bottom_right")
        
        if mode == "text":
            element = cls.create_text_element(
                text=config.get("text", "Marca de Agua"),
                font_path=config.get("font_path", ""),
                font_size=config.get("font_size", 40),
                color_rgb=config.get("color", (255, 255, 255)),
                opacity=config.get("opacity", 0.8),
                rotation=config.get("rotation", 0.0),
                has_shadow=config.get("shadow", False),
                shadow_color=config.get("shadow_color", (0, 0, 0)),
                shadow_offset=config.get("shadow_offset", (3, 3)),
                has_outline=config.get("outline", False),
                outline_color=config.get("outline_color", (0, 0, 0)),
                outline_width=config.get("outline_width", 2),
                is_bold=config.get("is_bold", False),
                is_italic=config.get("is_italic", False),
                is_underline=config.get("is_underline", False)
            )
        else:
            element = cls.create_logo_element(
                logo_path=config.get("logo_path", ""),
                scale_percent=config.get("scale", 20.0),
                base_w=composed.width,
                base_h=composed.height,
                opacity=config.get("opacity", 0.8),
                rotation=config.get("rotation", 0.0)
            )

        elem_w, elem_h = element.size

        # Calcular coordenadas finales (x, y)
        if preset == "custom":
            # Coordenadas directas (pueden ser relativas 0-1 o absolutas)
            if config.get("relative_pos", False):
                pos_x = int(config.get("pos_x_ratio", 0.5) * composed.width - elem_w / 2)
                pos_y = int(config.get("pos_y_ratio", 0.5) * composed.height - elem_h / 2)
            else:
                pos_x = int(config.get("pos_x", 20))
                pos_y = int(config.get("pos_y", 20))
        else:
            margin_x = int(config.get("margin_x", 30))
            margin_y = int(config.get("margin_y", 30))
            pos_x, pos_y = cls.calculate_preset_position(
                composed.width, composed.height, elem_w, elem_h, preset, margin_x, margin_y
            )

        # Pegar elemento en el overlay usando su canal alfa como máscara
        overlay.paste(element, (pos_x, pos_y), element)

        # Componer imagen base con overlay
        final_image = Image.alpha_composite(composed, overlay)
        return final_image
