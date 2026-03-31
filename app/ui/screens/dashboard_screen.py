from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.dashboard_service import DashboardService
from app.ui.widgets.summary_card import SummaryCard
from app.ui.design_system.async_job import AsyncRunner, JobHandle
from app.ui.design_system.widgets import GlassCard, PrimaryButton, SubtitleLabel, TitleLabel


class DashboardScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.business = ensure_default_business()
        self.dashboard_service = DashboardService()
        self.async_runner = AsyncRunner()

        self.title = TitleLabel("Dashboard")
        self.subtitle = SubtitleLabel("KPIs and operational health")

        self.refresh_btn = PrimaryButton("Refresh")

        self.sales_card = SummaryCard("Today's Sales", "KES 0.00")
        self.transactions_card = SummaryCard("Today's Transactions", "0")
        self.expenses_card = SummaryCard("Today's Expenses", "KES 0.00")
        self.balance_card = SummaryCard("Estimated Balance", "KES 0.00")
        self.low_stock_card = SummaryCard("Low Stock Items", "0")

        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.refresh_btn)

        grid = QGridLayout()
        grid.addWidget(self.sales_card, 0, 0)
        grid.addWidget(self.transactions_card, 0, 1)
        grid.addWidget(self.expenses_card, 1, 0)
        grid.addWidget(self.balance_card, 1, 1)
        grid.addWidget(self.low_stock_card, 2, 0, 1, 2)

        self.chart_stub = GlassCard()
        chart_layout = QVBoxLayout(self.chart_stub)
        chart_layout.setContentsMargins(14, 14, 14, 14)
        chart_layout.setSpacing(8)
        chart_title = QLabel("Analytics")
        chart_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        chart_note = SubtitleLabel("Charts are lazy-loaded to keep the UI fast.")
        chart_layout.addWidget(chart_title)
        chart_layout.addWidget(chart_note)
        chart_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addLayout(header)
        layout.addWidget(self.subtitle)
        layout.addLayout(grid)
        layout.addWidget(self.chart_stub, 1)
        layout.addStretch()

        self.refresh_btn.clicked.connect(self.load_summary)
        self.load_summary()

    def showEvent(self, event: QEvent) -> None:
        """Refresh dashboard data when the screen becomes visible."""
        super().showEvent(event)
        if event.type() == QEvent.Show:
            self.load_summary()

    def load_summary(self) -> None:
        self.refresh_btn.setEnabled(False)

        def work():
            return self.dashboard_service.get_summary(self.business.id)

        def ok(summary):
            self.sales_card.set_value(f"KES {summary['sales_total']:.2f}")
            self.transactions_card.set_value(str(summary['transaction_count']))
            self.expenses_card.set_value(f"KES {summary['expenses_total']:.2f}")
            self.balance_card.set_value(f"KES {summary['estimated_balance']:.2f}")
            self.low_stock_card.set_value(str(summary['low_stock_count']))
            self.refresh_btn.setEnabled(True)

        def err(_trace: str):
            self.refresh_btn.setEnabled(True)

        self.async_runner.run(work, JobHandle(on_success=ok, on_error=err))