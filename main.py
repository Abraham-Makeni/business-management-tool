from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
import sys


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Business Management Tool")
        self.setMinimumSize(1200, 700)

        label = QLabel("Business Management Tool MVP")
        label.setMargin(20)
        self.setCentralWidget(label)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()