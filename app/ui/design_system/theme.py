from pathlib import Path


def load_app_stylesheet() -> str:
    qss_path = Path(__file__).with_name("theme.qss")
    return qss_path.read_text(encoding="utf-8")

