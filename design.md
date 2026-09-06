# WatermarkStudio — Diseño Frontend

> **Framework UI:** PyQt6  
> **Tema global:** Dark mode con paleta azul-slate  
> **Carpeta:** `src/gui/`

---

## Estructura general de la interfaz

```
QMainWindow (MainWindow)
├── QMenuBar  →  Archivo | Ver
├── QSplitter (horizontal)
│   ├── PreviewCanvas  →  lienzo gráfico interactivo (expansible)
│   └── ControlPanel   →  panel lateral fijo 240 px
└── QStatusBar  →  info de archivo + resolución
```

---

## Paleta de colores

| Token | Color | Uso |
|---|---|---|
| Fondo principal | `#0f1016` | `QMainWindow` |
| Fondo panel | `#181824` | Secciones del `ControlPanel` |
| Fondo input | `#20202e` | `QLineEdit`, `QComboBox`, `QSpinBox` |
| Fondo canvas | `#14141c` | `QGraphicsView` |
| Fondo tabs | `#12121c` | `QTabBar` inactivo |
| Borde sutil | `#28283a` | Separadores y frames |
| Azul primario | `#2563eb` | Botones de acción, sliders activos |
| Azul hover | `#1d4ed8` | Estado hover del botón Cargar |
| Verde guardar | `#059669` | Botón Guardar |
| Verde hover | `#047857` | Estado hover del botón Guardar |
| Azul claro | `#60a5fa` | Handle del slider, tab activo |
| Azul pálido | `#93c5fd` | Labels de valores numéricos |
| Texto principal | `#e2e8f0` | `QWidget` global |
| Texto sutil | `#94a3b8` | `QStatusBar`, labels secundarios |
| Status posición | `#38bdf8` | Indicador de posición activa |

---

## 1. `main_window.py` — Ventana Principal

**Clase:** `MainWindow(QMainWindow)`

### Layout

```
QHBoxLayout (central_widget, márgenes 4px, spacing 4px)
└── QSplitter (horizontal, no colapsable)
    ├── PreviewCanvas  [stretch 1]
    └── ControlPanel   [width fijo: 240 px, stretch 0]
```

### Inicialización (`__init__`)

- Tamaño mínimo: **850 × 550 px**
- Tamaño adaptativo: hasta **1280 × 800 px** (90% de la pantalla disponible)
- Secuencia de arranque:
  1. `init_ui()` — construye el layout
  2. `apply_dark_theme()` — aplica el QSS global
  3. `setup_menu_and_shortcuts()` — menús y atajos
  4. `create_welcome_canvas()` — lienzo azul oscuro 1920×1080 de bienvenida

### Tema global — `apply_dark_theme()` (líneas 329–471)

El método aplica un bloque QSS único a toda la ventana. Widgets cubiertos:

| Widget | Estilo destacado |
|---|---|
| `QMainWindow` | Fondo `#0f1016` |
| `QWidget` | Fuente `Segoe UI / Arial`, `9pt`, color `#e2e8f0` |
| `QMenuBar` | Fondo `#161622`, borde inferior `#28283a` |
| `QMenu` | Fondo `#1c1d2a`, selección `#2563eb` |
| `QTabWidget / QTabBar` | Fondo activo `#181824`, color activo `#60a5fa`, borde inferior azul |
| `QLineEdit / QComboBox` | Fondo `#20202e`, foco `#3b82f6` |
| `QSpinBox` | Igual que inputs, foco azul |
| `QSlider` | Ranura `#28283a`, sub-page `#2563eb`, handle `#60a5fa` (12 px, circular) |
| `QScrollBar` | 8 px, handle `#334155` |
| `QStatusBar` | Fondo `#12121c`, texto `#94a3b8` |
| `QProgressDialog / QProgressBar` | Fondo oscuro, chunk `#2563eb` |

### Barra de menú

| Menú | Acción | Atajo |
|---|---|---|
| Archivo | Cargar Foto o Vídeo… | `Ctrl+O` |
| Archivo | Guardar Resultado… | `Ctrl+S` |
| Archivo | Salir | `Ctrl+Q` |
| Ver | Ajustar a la Ventana | `Ctrl+0` |

### Señales conectadas

| Origen | Señal | Destino |
|---|---|---|
| `canvas` | `position_changed` | `on_canvas_position_changed` → actualiza posición libre en el panel |
| `canvas` | `time_seeked` | `on_video_time_seeked` → extrae fotograma del vídeo |
| `control_panel` | `config_changed` | `on_config_changed` → redibuja la marca de agua |
| `control_panel` | `open_image_requested` | `open_media_dialog` |
| `control_panel` | `save_image_requested` | `save_media_dialog` |

### Exportación de vídeo en hilo — `VideoExportWorker(QThread)`

Worker que procesa la exportación sin bloquear la UI:

| Señal | Tipo | Descripción |
|---|---|---|
| `progress_changed` | `float` | Porcentaje de avance (0.0–1.0) |
| `finished_signal` | `bool, str` | Éxito + ruta o mensaje de error |

Muestra un `QProgressDialog` modal durante la exportación con botón **Cancelar**.

### Drag & Drop

La ventana acepta arrastrar archivos directamente desde el explorador:
- Formatos de vídeo: `.mp4 .mov .mkv .avi .webm .flv .wmv .m4v`
- Formatos de imagen: `.png .jpg .jpeg .webp .bmp .tiff .tif`

---

## 2. `control_panel.py` — Panel de Controles

**Clases:** `ColorButton(QPushButton)`, `ControlPanel(QWidget)`

### Layout general

```
QVBoxLayout (márgenes 6px, spacing 6px)
├── QHBoxLayout → [📂 Cargar] [💾 Guardar]
├── QTabWidget
│   ├── Tab "✍️ Texto"
│   └── Tab "🖼️ Logo"
├── QFrame "Estilo" (fondo #181824, borde #28283a)
│   ├── Fila Opacidad  → QSlider 0–100% + label valor
│   └── Fila Rotación  → QSlider -180°–+180° + label + botón reset "0°"
└── QFrame "Posición" (fondo #181824, borde #28283a)
    ├── Header  → "Posición:" + label estado (#38bdf8)
    ├── QGridLayout 3×3 → 9 botones de preset
    └── Fila márgenes  → SpinBox X (0–800 px) + SpinBox Y (0–800 px)
```

### Botones principales

| Botón | Color fondo | Hover | Señal emitida |
|---|---|---|---|
| 📂 Cargar | `#2563eb` | `#1d4ed8` | `open_image_requested` |
| 💾 Guardar | `#059669` | `#047857` | `save_image_requested` |

Altura fija: **28 px**. Cursor de mano (`PointingHandCursor`).

### Tab "✍️ Texto" — `create_text_tab()`

| Control | Detalles |
|---|---|
| `QLineEdit` | Texto de la marca, valor inicial `© Mi Marca de Agua` |
| `QComboBox` | Editable, lista fuentes del sistema, preselecciona Arial/Segoe UI/Calibri |
| `ColorButton` | Muestra color actual con fondo RGB, texto adaptativo por luminancia (umbral 140) |
| Botón **B** | Negrita, checkable, `28×26 px` |
| Botón **I** | Cursiva, checkable, fuente serif en el botón |
| Botón **U** | Subrayado, checkable |
| Slider tamaño | Rango 8–300 px, valor inicial 52 + botones ➖/➕ (±2) |

Los botones B/I/U tienen tres estados visuales:
- Normal: `#242436` / texto `#cbd5e1`
- Hover: `#313148` / borde `#60a5fa`
- Checked (activo): `#2563eb` / texto blanco / borde `#60a5fa`

### Tab "🖼️ Logo" — `create_logo_tab()`

| Control | Detalles |
|---|---|
| `QLineEdit` (read-only) | Ruta del logo seleccionado |
| Botón `...` | Abre `QFileDialog` para PNG/JPG/WebP |
| Slider escala | Rango 1–100%, valor inicial 20% |

### Sección Posición — Matriz 3×3

9 botones checkables (solo uno activo a la vez) con tooltips:

```
↖ Arriba Izq   ↑ Arriba Centro   ↗ Arriba Der
← Centro Izq   •     Centro      → Centro Der
↙ Abajo Izq    ↓ Abajo Centro    ↘ Abajo Der  ← (defecto)
```

El label de estado muestra la posición activa en `#38bdf8`.  
En modo arrastre libre muestra `Libre (x,y)` y deselecciona todos los botones.

### Configuración exportada — `get_current_config() → dict`

```python
{
    "mode":        "text" | "logo",
    "text":        str,
    "font_path":   str,
    "font_size":   int,        # 8–300
    "color":       (r, g, b),
    "is_bold":     bool,
    "is_italic":   bool,
    "is_underline":bool,
    "shadow":      False,      # reservado
    "outline":     False,      # reservado
    "logo_path":   str,
    "scale":       float,      # 1.0–100.0
    "opacity":     float,      # 0.0–1.0
    "rotation":    float,      # -180.0–180.0
    "preset":      str,        # "bottom_right" | "custom" | …
    "margin_x":    int,        # px
    "margin_y":    int,        # px
    "pos_x":       int,        # solo en modo custom
    "pos_y":       int,        # solo en modo custom
    "relative_pos":False
}
```

Cada cambio de cualquier control dispara `emit_config()` → señal `config_changed`.

### `ColorButton` — Widget personalizado

```python
class ColorButton(QPushButton):
    color_changed = pyqtSignal(tuple)  # emite (r, g, b)
```

- Fondo del botón = color actual en RGB
- Texto del botón = `🎨 {label}`
- Color del texto calculado por luminancia: oscuro (`#0f172a`) si luminancia > 140, claro (`#f8fafc`) si no

---

## 3. `preview_canvas.py` — Lienzo de Previsualización

**Clases:** `DraggableWatermarkItem(QGraphicsPixmapItem)`, `PreviewCanvas(QWidget)`

### Layout

```
QVBoxLayout (sin márgenes)
├── QGraphicsView (stretch 1)  →  lienzo principal
│   └── QFrame flotante (12,12)  →  barra de zoom
└── QFrame (altura 38 px)  →  barra de vídeo (oculta si imagen)
```

### `QGraphicsView` — Configuración

| Propiedad | Valor |
|---|---|
| Antialiasing | Activado |
| SmoothPixmapTransform | Activado |
| ViewportUpdateMode | `FullViewportUpdate` |
| TransformationAnchor | `AnchorUnderMouse` (zoom centrado en cursor) |
| Fondo | `#14141c` |
| Borde | `1px solid #28283a`, `border-radius: 6px` |

### Escena gráfica — capas Z

| Z-value | Item |
|---|---|
| `0` | `QGraphicsPixmapItem` — imagen/fotograma base |
| `10` | `DraggableWatermarkItem` — marca de agua arrastrable |

### Barra flotante de zoom (`create_floating_toolbar`)

Frame semitransparente (`rgba(26,26,38,0.85)`) anclado en posición `(12, 12)` sobre el `QGraphicsView`. Se reposiciona en `on_view_resize`.

| Botón | Función |
|---|---|
| ⛶ Ajustar | `fit_in_view()` → `fitInView` manteniendo aspecto ratio |
| 1:1 | `reset_zoom()` → `resetTransform()` |
| ➕ | `zoom_in()` → `scale(1.2, 1.2)` |
| ➖ | `zoom_out()` → `scale(1/1.2, 1/1.2)` |

Estilo hover: fondo `#3b82f6`.

### Barra de vídeo (`create_video_timeline`)

Altura fija **38 px**, fondo `#181824`. Solo visible en modo vídeo.

| Control | Detalles |
|---|---|
| Botón ▶ Play / ⏸ Pausa | Ancho 60 px, fondo azul `#2563eb` |
| `QSlider` timeline | Rango 0–1000 (normalizado), emite `time_seeked` |
| Label tiempo | `MM:SS / MM:SS`, color `#93c5fd` |

**Reproducción en preview:** `QTimer` a 100 ms (~10 fps). Avanza 0.2 s por tick y emite `time_seeked`.

### Interacciones del ratón

| Acción | Resultado |
|---|---|
| Rueda del ratón | Zoom × 1.15 o ÷ 1.15 centrado en cursor |
| Clic derecho / rueda central + arrastrar | Pan (desplazamiento) del lienzo |
| Clic izquierdo sobre marca de agua | Inicia arrastre libre (`DraggableWatermarkItem`) |
| Soltar marca de agua | Emite `position_changed(x, y)` → `MainWindow` → `ControlPanel.set_custom_drag_position` |

### `DraggableWatermarkItem`

Extiende `QGraphicsPixmapItem` con flags `ItemIsMovable | ItemSendsGeometryChanges | ItemIsSelectable`.  
Cursor: `SizeAllCursor`. Notifica al canvas padre en cada movimiento.

### Señales públicas de `PreviewCanvas`

| Señal | Tipo | Descripción |
|---|---|---|
| `position_changed` | `float, float` | Posición (x, y) de la marca al arrastrar |
| `time_seeked` | `float` | Segundo del vídeo seleccionado |

### Método estático `pil_to_qimage`

Convierte `PIL.Image` → `QImage` (formato `RGBA8888`):
1. Convierte a `RGBA` si no lo es
2. Extrae bytes raw con `tobytes("raw", "RGBA")`
3. Devuelve copia del `QImage` para evitar referencias a memoria liberada

---

## Flujo de datos entre componentes

```
ControlPanel.get_current_config()
        │
        │ config_changed (dict)
        ▼
MainWindow.on_config_changed()
        │
        │ canvas.update_watermark(config)
        ▼
PreviewCanvas.update_watermark()
        │
        ├─ WatermarkEngine.create_text_element()  →  PIL.Image
        ├─ WatermarkEngine.create_logo_element()  →  PIL.Image
        ├─ WatermarkEngine.calculate_preset_position()  →  (x, y)
        └─ DraggableWatermarkItem.setPixmap() + setPos()
```

```
Usuario arrastra marca de agua
        │
        │ DraggableWatermarkItem.mouseMoveEvent
        ▼
PreviewCanvas.on_watermark_dragged()
        │  position_changed(x, y)
        ▼
MainWindow.on_canvas_position_changed()
        │
        ▼
ControlPanel.set_custom_drag_position()
        → lbl_pos_status = "Libre (x,y)"
        → todos los preset_buttons.setChecked(False)
```

---

## Formatos soportados

| Tipo | Extensiones |
|---|---|
| Imagen | `.png .jpg .jpeg .webp .bmp .tiff .tif` |
| Vídeo | `.mp4 .mov .mkv .avi .webm .flv .wmv .m4v` |
