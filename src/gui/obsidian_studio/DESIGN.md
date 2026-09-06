---
name: Obsidian Studio
colors:
  surface: '#121319'
  surface-dim: '#121319'
  surface-bright: '#383940'
  surface-container-lowest: '#0d0e14'
  surface-container-low: '#1a1b21'
  surface-container: '#1e1f26'
  surface-container-high: '#292a30'
  surface-container-highest: '#34343b'
  on-surface: '#e3e1ea'
  on-surface-variant: '#c3c6d7'
  inverse-surface: '#e3e1ea'
  inverse-on-surface: '#2f3037'
  outline: '#8d90a0'
  outline-variant: '#434655'
  surface-tint: '#b4c5ff'
  primary: '#b4c5ff'
  on-primary: '#002a78'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#0053db'
  secondary: '#68dba9'
  on-secondary: '#003825'
  secondary-container: '#25a475'
  on-secondary-container: '#00311f'
  tertiary: '#7bd0ff'
  on-tertiary: '#00354a'
  tertiary-container: '#00759f'
  on-tertiary-container: '#e1f2ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#85f8c4'
  secondary-fixed-dim: '#68dba9'
  on-secondary-fixed: '#002114'
  on-secondary-fixed-variant: '#005137'
  tertiary-fixed: '#c4e7ff'
  tertiary-fixed-dim: '#7bd0ff'
  on-tertiary-fixed: '#001e2c'
  on-tertiary-fixed-variant: '#004c69'
  background: '#121319'
  on-background: '#e3e1ea'
  surface-variant: '#34343b'
  surface-canvas: '#14141c'
  surface-panel: '#181824'
  surface-input: '#20202e'
  surface-input-focus: '#252536'
  surface-toolbar: '#1a1a26'
  surface-button-neutral: '#242436'
  surface-button-hover: '#313148'
  surface-utility: '#334155'
  border-subtle: '#28283a'
  border-interactive: '#3b3b52'
  border-input: '#333346'
  border-focus: '#3b82f6'
  accent-electric: '#3b82f6'
  accent-cyan: '#38bdf8'
  accent-light-blue: '#60a5fa'
  accent-ice-blue: '#93c5fd'
  accent-blue-hover: '#bfdbfe'
  primary-hover: '#1d4ed8'
  success-hover: '#047857'
  text-primary: '#f8fafc'
  text-body: '#e2e8f0'
  text-secondary: '#cbd5e1'
  text-muted: '#94a3b8'
  text-inverse: '#0f172a'
typography:
  headline-app:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '700'
    lineHeight: 18px
    letterSpacing: -0.01em
  headline-panel:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.01em
  body-default:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: '0'
  body-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: '0'
  control-label:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.01em
  control-input:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: '0'
  value-indicator:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.02em
  badge-status:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.02em
  utility-micro:
    fontFamily: Inter
    fontSize: 9px
    fontWeight: '700'
    lineHeight: 10px
    letterSpacing: '0'
  format-glyph:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: '0'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xxs: 2px
  xs: 4px
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  margin-window: 4px
  margin-panel: 6px
  panel-width: 240px
  row-height-control: 26px
  row-height-action: 28px
  timeline-height: 38px
---

## Brand & Style

The design system establishes a focused, high-density desktop creative studio aesthetic inspired by precision media authoring tools like Figma, Adobe Lightroom, and Screen Studio. The brand identity balances technical discipline with fluid tactile feedback, targeting creative professionals, content producers, photographers, and video editors who demand zero-latency visual authoring.

The visual style blends **Technical Minimalism** with **Atmospheric Planar Dark Surfaces**. Deep obsidian, slate, and zinc foundations recede completely into the working environment, ensuring that the loaded user media—whether 4K video or high-resolution photography—remains the sole hero of the workspace. Visual hierarchy is achieved without heavy drop shadows; instead, hairline 1px architectural borders, subtle tonal shifts between recessed and elevated planes, and vibrant targeted chromatic accents define interactive states. Electric cobalt blue drives primary actions and telemetry highlights, vivid cyan guides visual spatial feedback, and a focused emerald green anchors irreversible export and save commitments.

## Colors

The chromatic architecture is strictly hierarchical, engineered for sustained low-strain focus during extended editing sessions:

- **Primary (`#2563eb`)**: High-energy cobalt royal blue deployed exclusively for focal execution triggers, active selection states, segmented progress fills, and active slider tracks.
- **Secondary (`#059669`)**: Saturated emerald green dedicated to write operations, export milestones, and definitive artifact generation.
- **Tertiary (`#38bdf8`)**: Electric cyan indicator accent used for live coordinate telemetry, spatial positioning status, and canvas alignment state.
- **Neutral (`#0f1016`)**: Deep pitch slate canvas ground that absorbs visual glare and anchors the desktop window chrome.

### Named Surfaces & Borders
- **Recessed Inputs (`#20202e`)** & **Interactive Buttons (`#242436`)**: Provide tactile depth within the `#181824` sidebar panels.
- **Borders (`#28283a`, `#333346`, `#3b3b52`)**: Form hair-thin structural seams defining splitters, frame panels, and segmented modules without visual bloat.
- **Telemetry Readouts (`#93c5fd`)**: Distinct pastel blue hue tuned for immediate scanning of numeric metrics (degrees, percentages, pixel offsets, and timecodes).

## Typography

Typography prioritizes micro-scale legibility and high information density. Utilizing Inter (paired with system fallback stacks Segoe UI and San Francisco on native desktop targets), the type scale avoids exaggerated displays in favor of razor-sharp control clarity.

- **Header / Telemetry Pairing**: Group labels (e.g., "Opacidad:", "Rotación:", "Posición:") use `control-label` at 11px bold in `#cbd5e1`, matched directly opposite with `value-indicator` in glowing `#93c5fd` or `#38bdf8`.
- **System Metrics**: Numeric indicators for scale, opacity, degrees, and coordinates maintain slight tracking expansion (`+0.02em`) to guarantee quick glances do not mistake numerals across dense inspectors.
- **Micro Glyphs**: Precision controls and stepper steppers rely on `utility-micro` (9px bold) for compact, tactile square triggers.

## Layout & Spacing

The layout philosophy follows a **Split-Pane Ergonomic Studio** architecture designed to eliminate vertical scrolling within standard desktop heights (from 550px up to 4K displays):

- **Main Splitter Grid**: A horizontal two-compartment structure:
  - **Viewport Canvas (`stretch: 1`)**: Fluid graphics stage expanding dynamically to all available screen space.
  - **Inspector Sidebar (`panel-width: 240px`, `stretch: 0`)**: Fixed-width docking column containing all essential transformation and styling tool modules.
- **Rhythm**: Spacing operates on an ultra-compact 4px grid base (`spacing.unit`). Internal panel margins are fixed at `6px`, with rows spaced at `4px` to `6px`. This strict density guarantees that tab configurations, opacity/rotation controls, the 3x3 alignment matrix, and pixel margin inputs fit concurrently on screen without pagination or folding.
- **Responsive Adaptability**: Minimum window boundaries are clamped at `850px × 550px`. At initial runtime, the system scales smoothly up to `90%` of screen geometry (capped at `1280px × 800px`), locking tool density while providing maximal breathing room to the central graphics viewport.

## Elevation & Depth

Visual depth is achieved through **Low-Contrast Outlines & Planar Tiers** rather than heavy diffusion drop shadows, preserving crisp screen boundaries and eliminating GPU rendering overhead:

- **Base Level 0 (Ground Canvas)**: `#0f1016` as the outer application shell.
- **Level 1 (Working Surfaces)**:
  - Central interactive canvas framed in `#14141c` with a 1px border of `#28283a`.
  - Sidebar control containers resting on `#181824` with hairline `#28283a` bounds.
- **Level 2 (Recessed Form Controls)**: Inputs, text areas, and spinboxes cut into Level 1 using `#20202e` with `#333346` borders, shifting to `#252536` with a glowing `#3b82f6` border on focus.
- **Level 3 (Tactile Toggles & Swatches)**: Format buttons, neutral presets, and utility tools at `#242436` bordered by `#3b3b52`.
- **Floating Overlays**: Floating view controls (such as the canvas zoom pill) utilize frosted obsidian backing `rgba(26, 26, 38, 0.85)` with a 1px `#3b3b52` border, suspended directly over viewport imagery.

## Shapes

The design system adopts a **Soft (Level 1)** geometric silhouette. In professional desktop tools, compact controls require restrained curvature to maximize screen real estate and maintain visual alignment:

- **Standard Controls & Cards (`4px` / `0.25rem`)**: Action buttons, input fields, and sidebar sections maintain a clean 4px radius.
- **Compact Toggles & Swatches (`2px` - `3px`)**: Format buttons (`B`, `I`, `U`), matrix preset tiles, and micro stepper triggers.
- **Viewport Panels & Floating Toolbars (`6px`)**: External graphics containers and floating canvas controls feature a slightly softer 6px radius to separate them as independent floating layers.
- **Circular Elements (`full` / `9999px`)**: Reserved strictly for the 12px slider handle thumbs and radio indicators.

## Components

### Buttons & Action Triggers
- **Primary Action ("Cargar")**: Fixed height `28px`, background `#2563eb`, hover `#1d4ed8`, text `#ffffff` (11px bold), border radius `4px`.
- **Commit Action ("Guardar")**: Fixed height `28px`, background `#059669`, hover `#047857`, text `#ffffff` (11px bold), border radius `4px`.
- **Format Toggles (Bold, Italic, Underline)**: `28×26px` square triggers. Default state `#242436` with `#cbd5e1` text and 1px `#3b3b52` outline; hover state `#313148` with `#60a5fa` outline; active state `#2563eb` with white text.
- **Micro Steppers & Resets (`➕`, `➖`, `0°`)**: `20×20px` to `22×20px` utility squares, background `#334155`, text `#ffffff`, typography `utility-micro`.
- **Dynamic Color Swatch (`ColorButton`)**: Dynamic preview container displaying current RGB fill. Borders expand to `2px solid #60a5fa` on hover. Label text automatically computes luminance, flipping between deep slate (`#0f172a`) and crisp white (`#f8fafc`).

### 3×3 Alignment Matrix
A dedicated 9-button grid arranged in 3 tight rows (`spacing: 2px`). Each directional cell represents Top-Left through Bottom-Right anchors. Inactive cells display `#242436` with 1px `#3b3b52` border; the selected cell illuminates in `#2563eb` with a `#60a5fa` border. When free-dragging watermarks directly on the canvas, all 9 matrix cells disengage, and the telemetry status updates to `Libre (X, Y)` in `#38bdf8`.

### Sliders & Numeric Adjusters
- **Horizontal Sliders**: Slim 5px track (`#28283a`) with cobalt fill (`#2563eb`) on the active left page. Circular 12px thumb handle (`#60a5fa`) with a 1px `#93c5fd` perimeter, brightening to `#bfdbfe` during scrubbing.
- **Coordinate Spinboxes**: Recessed `#20202e` fields with `#333346` borders and `#f8fafc` monospaced values, bounded by right-aligned micro stepper buttons.

### Tabs & Segmented Navigators
Horizontal tabs ("Texto" / "Logo") housed directly above the tool groups. Unselected tabs sit at `#12121c` with `#94a3b8` text. Selected tabs transition to `#181824` with glowing `#60a5fa` text and an active 2px bottom underline in `#3b82f6`.

### Preview Canvas & Video Scrubbing Bar
- **Interactive Viewport**: Matte `#14141c` canvas supporting hardware-accelerated pan and mouse-wheel zoom centered on cursor coordinates. Watermark graphic items show a 4-way move cursor (`SizeAllCursor`) during drag operations.
- **Floating Pill Toolbar**: Fixed at `(12px, 12px)` over the preview, housing Fit, 1:1, Zoom In, and Zoom Out actions in a translucent obsidian capsule.
- **Video Scrubbing Bar**: Docked 38px timeline footer visible during video editing. Features a 60px royal blue Play/Pause button, a continuous normalized timeline scrubber, and a glowing `#93c5fd` digital timecode counter (`MM:SS / MM:SS`).