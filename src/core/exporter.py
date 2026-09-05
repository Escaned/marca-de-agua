import os
from PIL import Image
from typing import Optional

class ImageExporter:
    """
    Gestiona el guardado y exportación de imágenes con marcas de agua.
    """

    @staticmethod
    def save_image(
        image: Image.Image,
        output_path: str,
        quality: int = 95,
        preserve_exif: bool = True
    ) -> bool:
        """
        Guarda la imagen procesada en el formato correspondiente según la extensión.
        """
        try:
            ext = os.path.splitext(output_path)[1].lower()

            if ext in ['.jpg', '.jpeg']:
                # JPG no soporta canal Alfa, convertir a RGB con fondo blanco
                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3]) # canal alfa
                    save_img = background
                else:
                    save_img = image.convert("RGB")

                save_img.save(output_path, "JPEG", quality=quality, optimize=True)

            elif ext == '.png':
                image.save(output_path, "PNG", optimize=True)

            elif ext == '.webp':
                image.save(output_path, "WEBP", quality=quality)

            elif ext in ['.bmp', '.tiff', '.tif']:
                image.save(output_path)

            else:
                # Por defecto PNG
                image.save(output_path, "PNG")

            return True
        except Exception as e:
            print(f"Error al guardar imagen: {e}")
            raise e
