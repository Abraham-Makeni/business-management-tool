from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class SummaryCard(QFrame):
    def __init__(self, title: str, value: str = "") -> None:
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #d9d9d9;
                border-radius: 10px;
                background: white;
                padding: 8px;
            }
        """)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 13px; color: #555;")

        self.value_label = QLabel(value or "—")
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #222;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(str(value) if value not in (None, "") else "—")
