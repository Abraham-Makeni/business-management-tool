import sys

from PySide6.QtWidgets import QApplication

from app.core.config import APP_NAME
from app.database.seed import ensure_default_business
from app.ui.app_window import AppWindow


def main() -> None:
    ensure_default_business()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()