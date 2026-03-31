# Design System (Enterprise B/W Glass UI)

## Principles
- **Palette**: strictly black/white/grayscale only.
- **Surfaces**: glassmorphism via semi-transparent whites on black.
- **States**: clear hover/focus/pressed/disabled styling in QSS.
- **Performance**: DB/service calls must not block the UI thread.

## How it’s applied
- The app stylesheet is loaded in `main.py` via `load_app_stylesheet()` from `app/ui/design_system/theme.py`.
- Glass surfaces use the dynamic property `glass="true"` (see `GlassCard`).
- Titles/subtitles use `title="true"` and `subtitle="true"` properties.

## Reusable components
- `app/ui/design_system/widgets.py`
  - `GlassCard`: glass panel/card surface
  - `TitleLabel`, `SubtitleLabel`: consistent typography tokens
  - `PrimaryButton`: primary action button style
- `app/ui/design_system/async_job.py`
  - `AsyncRunner`: threadpool runner for non-blocking UI
  - `JobHandle`: success/fail callbacks (fail gets traceback string)
- `app/ui/design_system/table.py`
  - `TableView`: sortable, filterable QTableView wrapper (enterprise default)
  - `SimpleTableModel`: dict-backed model

## Screen patterns
- **Load data** using `AsyncRunner` and disable relevant buttons while in-flight.
- **Tables**: prefer `TableView` and map service objects to row dictionaries.
- **Dialogs**: keep glass styling through global theme; avoid inline colors.

## Next upgrades (optional)
- Pagination controls in `TableView` for very large datasets
- Inline editing using a delegate (still grayscale)
- SVG icon pack under `app/ui/assets/icons/` (monochrome)

