import sys
import logging
import traceback

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox

from app.core.config import APP_NAME
from app.core.logging_config import setup_logging
from app.database.init_db import init_db
from app.database.seed import ensure_default_business
from app.ui.design_system.theme import load_app_stylesheet
from app.ui.app_window import AppWindow


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    init_db()
    ensure_default_business()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(load_app_stylesheet())

    def excepthook(exc_type, exc, tb):
        logger.critical("Unhandled exception", exc_info=(exc_type, exc, tb))
        msg = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            QMessageBox.critical(None, "Unexpected Error", msg)
        except Exception:
            # If Qt isn't available for some reason, fall back to stderr
            sys.__stderr__.write(msg + "\n")

    sys.excepthook = excepthook

    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()