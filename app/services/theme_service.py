import json
from pathlib import Path

from app.core.config import DATA_DIR


class ThemeService:
    DEFAULT_THEME = "high_contrast"
    THEMES = {
        "high_contrast": "theme.qss",
        "dark": "theme_dark.qss",
        "light": "theme_light.qss",
    }
    SETTINGS_PATH = Path(DATA_DIR) / "ui_settings.json"

    @classmethod
    def get_theme(cls) -> str:
        if cls.SETTINGS_PATH.exists():
            try:
                settings = json.loads(cls.SETTINGS_PATH.read_text(encoding="utf-8"))
                theme = settings.get("theme")
                if theme in cls.THEMES:
                    return theme
            except Exception:
                pass
        return cls.DEFAULT_THEME

    @classmethod
    def set_theme(cls, theme: str) -> None:
        if theme not in cls.THEMES:
            theme = cls.DEFAULT_THEME
        cls.SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.SETTINGS_PATH.write_text(json.dumps({"theme": theme}), encoding="utf-8")

    @classmethod
    def get_theme_file(cls, theme: str | None = None) -> str:
        theme = theme or cls.get_theme()
        return cls.THEMES.get(theme, cls.THEMES[cls.DEFAULT_THEME])
