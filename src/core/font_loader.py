import os
import winreg
from typing import Dict, List, Tuple

def get_system_fonts() -> Dict[str, str]:
    """
    Recupera todas las fuentes TrueType y OpenType instaladas en Windows.
    Retorna un diccionario: {nombre_mostrado: ruta_del_archivo}
    """
    fonts: Dict[str, str] = {}
    
    # 1. Rutas estándar de fuentes en Windows
    system_fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    user_fonts_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
    
    # 2. Consultar el registro de Windows para nombres exactos de fuentes
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", system_fonts_dir),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", user_fonts_dir)
    ]
    
    for hkey, subkey, base_dir in registry_paths:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    try:
                        font_name, font_file, _ = winreg.EnumValue(key, i)
                        
                        # Limpiar nombre (quitar sufijos como (TrueType), (OpenType), etc.)
                        clean_name = font_name
                        for suffix in [" (TrueType)", " (OpenType)", " (All type)", " (TrueType & OpenType)"]:
                            if clean_name.endswith(suffix):
                                clean_name = clean_name[:-len(suffix)].strip()
                        
                        # Determinar ruta absoluta del archivo
                        if os.path.isabs(font_file):
                            full_path = font_file
                        else:
                            full_path = os.path.join(base_dir, font_file)
                        
                        # Solo incluir si el archivo existe y es compatible
                        if os.path.isfile(full_path) and full_path.lower().endswith(('.ttf', '.otf', '.ttc')):
                            if clean_name not in fonts:
                                fonts[clean_name] = full_path
                    except Exception:
                        continue
        except Exception:
            continue
            
    # 3. Escaneo directo de la carpeta C:\Windows\Fonts como respaldo
    if os.path.isdir(system_fonts_dir):
        for file in os.listdir(system_fonts_dir):
            if file.lower().endswith(('.ttf', '.otf')):
                name = os.path.splitext(file)[0].replace('_', ' ').title()
                full_path = os.path.join(system_fonts_dir, file)
                if name not in fonts:
                    fonts[name] = full_path
                    
    # Si por alguna razón no se encuentran fuentes, asegurar fuentes esenciales
    if not fonts:
        for standard in ["arial.ttf", "segoeui.ttf", "calibri.ttf", "tahoma.ttf", "times.ttf"]:
            p = os.path.join(system_fonts_dir, standard)
            if os.path.exists(p):
                fonts[os.path.splitext(standard)[0].capitalize()] = p
                
    return dict(sorted(fonts.items(), key=lambda item: item[0].lower()))
