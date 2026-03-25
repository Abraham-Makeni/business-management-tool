from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.dashboard_service import DashboardService
from app.ui.widgets.summary_card import SummaryCard


class DashboardScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.business = ensure_default_business()
        self.dashboard_service = DashboardService()

        self.title = QLabel("Dashboard")
        self.title.setStyleSheet("font-size: 20px; font-weight: 700;")

        self.refresh_btn = QPushButton("Refresh")

        self.sales_card = SummaryCard("Today's Sales", "KES 0.00")
        self.transactions_card = SummaryCard("Today's Transactions", "0")
        self.expenses_card = SummaryCard("Today's Expenses", "KES 0.00")
        self.balance_card = SummaryCard("Estimated Balance", "KES 0.00")
        self.low_stock_card = SummaryCard("Low Stock Items", "0")

        grid = QGridLayout()
        grid.addWidget(self.sales_card, 0, 0)
        grid.addWidget(self.transactions_card, 0, 1)
        grid.addWidget(self.expenses_card, 1, 0)
        grid.addWidget(self.balance_card, 1, 1)
        grid.addWidget(self.low_stock_card, 2, 0, 1, 2)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.refresh_btn)
        layout.addLayout(grid)
        layout.addStretch()

        self.refresh_btn.clicked.connect(self.load_summary)
        self.load_summary()

    def showEvent(self, event: QEvent) -> None:
        """Refresh dashboard data when the screen becomes visible."""
        super().showEvent(event)
        if event.type() == QEvent.Show:
            self.load_summary()

    def load_summary(self) -> None:
        summary = self.dashboard_service.get_summary(self.business.id)
        self.sales_card.set_value(f"KES {summary['sales_total']:.2f}")
        self.transactions_card.set_value(str(summary['transaction_count']))
        self.expenses_card.set_value(f"KES {summary['expenses_total']:.2f}")
        self.balance_card.set_value(f"KES {summary['estimated_balance']:.2f}")
        self.low_stock_card.set_value(str(summary['low_stock_count']))