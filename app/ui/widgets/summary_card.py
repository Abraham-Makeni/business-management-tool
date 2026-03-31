from PySide6.QtWidgets import QLabel, QVBoxLayout

from app.ui.design_system.widgets import GlassCard, SubtitleLabel


class SummaryCard(GlassCard):
    def __init__(self, title: str, value: str = "") -> None:
        super().__init__()

        self.title_label = SubtitleLabel(title)

        self.value_label = QLabel(value or "—")
        self.value_label.setStyleSheet("font-size: 24px; font-weight: 800;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(str(value) if value not in (None, "") else "—")
