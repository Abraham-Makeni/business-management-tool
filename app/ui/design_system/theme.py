from pathlib import Path

from app.services.theme_service import ThemeService


def load_app_stylesheet(theme: str | None = None) -> str:
    selected_theme = theme or ThemeService.get_theme()
    qss_file = ThemeService.get_theme_file(selected_theme)
    qss_path = Path(__file__).with_name(qss_file)
    if not qss_path.exists():
        qss_path = Path(__file__).with_name("theme.qss")
    return qss_path.read_text(encoding="utf-8")

