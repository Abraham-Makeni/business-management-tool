from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.inventory_service import InventoryService


class InventoryScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.inventory_service = InventoryService()

        self.title = QLabel("Stock History")
        self.refresh_btn = QPushButton("Refresh")

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Product", "Type", "Quantity", "Notes", "Date"]
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.table)

        self.refresh_btn.clicked.connect(self.load_movements)
        self.load_movements()

    def load_movements(self) -> None:
        movements = self.inventory_service.list_recent_movements(limit=200)
        self.table.setRowCount(len(movements))

        for row, movement in enumerate(movements):
            self.table.setItem(row, 0, QTableWidgetItem(str(movement.id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(movement.product_id)))
            self.table.setItem(row, 2, QTableWidgetItem(movement.movement_type))
            self.table.setItem(row, 3, QTableWidgetItem(f"{movement.quantity:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(movement.reference or ""))
            self.table.setItem(row, 5, QTableWidgetItem(movement.created_at.strftime("%Y-%m-%d %H:%M")))

        self.table.resizeColumnsToContents()
