from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.inventory_service import InventoryService
from app.ui.design_system.async_job import AsyncRunner, JobHandle
from app.ui.design_system.table import Column, TableView
from app.ui.design_system.widgets import PrimaryButton, TitleLabel


class InventoryScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.inventory_service = InventoryService()
        self.async_runner = AsyncRunner()

        self.title = TitleLabel("Stock History")
        self.refresh_btn = PrimaryButton("Refresh")

        self.table = TableView(
            columns=[
                Column("id", "ID"),
                Column("product_id", "Product"),
                Column("type", "Type"),
                Column("quantity", "Quantity", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("notes", "Notes"),
                Column("date", "Date"),
            ]
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.title)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.table)

        self.refresh_btn.clicked.connect(self.load_movements)
        self.table.refresh_btn.clicked.connect(self.load_movements)
        self.load_movements()

    def load_movements(self) -> None:
        self.refresh_btn.setEnabled(False)
        self.table.refresh_btn.setEnabled(False)

        def work():
            return self.inventory_service.list_recent_movements(limit=200)

        def ok(movements):
            rows = []
            for m in movements:
                rows.append(
                    {
                        "id": m.id,
                        "product_id": m.product_id,
                        "type": m.movement_type,
                        "quantity": f"{m.quantity:.2f}",
                        "notes": m.reference or "",
                        "date": m.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                )
            self.table.set_rows(rows)
            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        def err(_trace: str):
            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        self.async_runner.run(work, JobHandle(on_success=ok, on_error=err))
