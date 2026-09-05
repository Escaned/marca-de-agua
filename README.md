# Watermark Studio 🎨

Aplicación de escritorio profesional desarrollada en Python para añadir marcas de agua totalmente personalizables a imágenes y videos.

---

## ✨ Características Principales

- **✍️ Marcas de Agua de Texto:**
  - Selector dinámico de **todas las fuentes instaladas en Windows** (`C:\Windows\Fonts`).
  - **Estilos tipográficos:** Botones para **Negrita (Bold)**, **Cursiva (Italic)** y **Subrayado (Underline)**.
  - **Selector de color:** Botón con muestra en vivo y paleta de colores.
  - Control de tamaño de tipografía con ajuste rápido y slider.
- **🖼️ Marcas de Agua de Logo / Imagen:**
  - Admite logotipos transparentes (PNG, WEBP, etc.).
  - Escalado proporcional relativo (1% al 100%).
- **🎛️ Control Total de Estilo:**
  - Slider de **Opacidad / Transparencia** (0% a 100%).
  - Slider de **Rotación libre** (-180° a 180°).
- **🎯 Posicionamiento Interactivo:**
  - **Arrastre libre con el ratón (Drag & Drop)** directamente sobre la imagen en tiempo real.
  - Matriz rápida de 9 posiciones predefinidas (Arriba-Izq, Centro, Abajo-Der, etc.) con ajuste de márgenes X/Y.
- **👁️ Previsualización en Vivo (Live Preview):**
  - Actualización instantánea a 60 FPS con zoom interactivo (rueda del ratón) y ajuste de ventana (`Ctrl+0`).
- **💾 Exportación de Alta Calidad:**
  - Exporta en resolución nativa original en formatos **PNG, JPEG, WebP y BMP**.

---

## 🚀 Requisitos e Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

---

## 📁 Estructura del Código

```
video_nombre/
├── src/
│   ├── core/
│   │   ├── font_loader.py       # Detección de fuentes del registro y sistema Windows
│   │   ├── watermark_engine.py  # Motor de renderizado con Pillow (capas RGBA y composición)
│   │   └── exporter.py          # Guardado y compresión de imágenes
│   └── gui/
│       ├── control_panel.py     # Panel lateral de controles y selectores
│       ├── preview_canvas.py    # Lienzo gráfico interactivo con arrastre de ratón
│       └── main_window.py       # Ventana principal y tema oscuro
├── main.py                      # Punto de entrada de la aplicación
├── requirements.txt             # Dependencias
└── README.md
```
