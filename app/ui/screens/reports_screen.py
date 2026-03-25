from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.backup_service import BackupService
from app.services.export_service import ExportService
from app.services.reporting_service import ReportingService


class ReportsScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.business = ensure_default_business()
        self.reporting_service = ReportingService()
        self.export_service = ExportService()
        self.backup_service = BackupService()

        self.title = QLabel("Reports")
        self.title.setStyleSheet("font-size: 20px; font-weight: 700;")

        self.refresh_btn = QPushButton("Refresh")
        self.backup_btn = QPushButton("Backup Database")

        top_actions = QHBoxLayout()
        top_actions.addWidget(self.refresh_btn)
        top_actions.addStretch()
        top_actions.addWidget(self.backup_btn)

        self.summary_label = QLabel("Summary will appear here")

        self.tabs = QTabWidget()

        self.low_stock_table = QTableWidget(0, 4)
        self.low_stock_table.setHorizontalHeaderLabels(["ID", "Product", "Stock", "Reorder Level"])
        self.low_stock_export_btn = QPushButton("Export Low Stock")

        self.expenses_table = QTableWidget(0, 2)
        self.expenses_table.setHorizontalHeaderLabels(["Category", "Total Amount"])
        self.expenses_export_btn = QPushButton("Export Expenses")

        self.movements_table = QTableWidget(0, 5)
        self.movements_table.setHorizontalHeaderLabels(["ID", "Product ID", "Type", "Quantity", "Date"])
        self.movements_export_btn = QPushButton("Export Stock History")

        self.top_items_table = QTableWidget(0, 3)
        self.top_items_table.setHorizontalHeaderLabels(["Item", "Qty Sold", "Sales Amount"])
        self.top_items_export_btn = QPushButton("Export Top Items")

        self.tabs.addTab(self._wrap_tab(self.low_stock_table, self.low_stock_export_btn), "Low Stock")
        self.tabs.addTab(self._wrap_tab(self.expenses_table, self.expenses_export_btn), "Expenses")
        self.tabs.addTab(self._wrap_tab(self.movements_table, self.movements_export_btn), "Stock History")
        self.tabs.addTab(self._wrap_tab(self.top_items_table, self.top_items_export_btn), "Top Items")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(top_actions)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.tabs)

        self.refresh_btn.clicked.connect(self.load_reports)
        self.backup_btn.clicked.connect(self.backup_database)

        self.low_stock_export_btn.clicked.connect(self.export_low_stock)
        self.expenses_export_btn.clicked.connect(self.export_expenses)
        self.movements_export_btn.clicked.connect(self.export_movements)
        self.top_items_export_btn.clicked.connect(self.export_top_items)

        self.load_reports()

    def _wrap_tab(self, table: QTableWidget, button: QPushButton) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(button)
        layout.addWidget(table)
        return tab

    def load_reports(self) -> None:
        summary = self.reporting_service.get_daily_sales_summary(self.business.id)
        self.summary_label.setText(
            f"Today's Sales: KES {summary['total_sales']:.2f} | "
            f"Transactions: {summary['transaction_count']} | "
            f"Expenses: KES {summary['total_expenses']:.2f} | "
            f"Estimated Balance: KES {summary['estimated_balance']:.2f}"
        )

        low_stock = self.reporting_service.get_low_stock_products(self.business.id)
        self.low_stock_table.setRowCount(len(low_stock))
        for row, product in enumerate(low_stock):
            self.low_stock_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            self.low_stock_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.low_stock_table.setItem(row, 2, QTableWidgetItem(f"{product.quantity_in_stock:.2f}"))
            self.low_stock_table.setItem(row, 3, QTableWidgetItem(f"{product.reorder_level:.2f}"))
        self.low_stock_table.resizeColumnsToContents()

        expenses = self.reporting_service.get_expenses_by_category(self.business.id)
        self.expenses_table.setRowCount(len(expenses))
        for row, item in enumerate(expenses):
            self.expenses_table.setItem(row, 0, QTableWidgetItem(item["category"]))
            self.expenses_table.setItem(row, 1, QTableWidgetItem(f"{item['total_amount']:.2f}"))
        self.expenses_table.resizeColumnsToContents()

        movements = self.reporting_service.get_recent_stock_movements(limit=200)
        self.movements_table.setRowCount(len(movements))
        for row, movement in enumerate(movements):
            self.movements_table.setItem(row, 0, QTableWidgetItem(str(movement.id)))
            self.movements_table.setItem(row, 1, QTableWidgetItem(str(movement.product_id)))
            self.movements_table.setItem(row, 2, QTableWidgetItem(movement.movement_type))
            self.movements_table.setItem(row, 3, QTableWidgetItem(f"{movement.quantity:.2f}"))
            self.movements_table.setItem(row, 4, QTableWidgetItem(movement.created_at.strftime("%Y-%m-%d %H:%M")))
        self.movements_table.resizeColumnsToContents()

        top_items = self.reporting_service.get_top_selling_items(self.business.id, limit=20)
        self.top_items_table.setRowCount(len(top_items))
        for row, item in enumerate(top_items):
            self.top_items_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.top_items_table.setItem(row, 1, QTableWidgetItem(f"{item['qty_sold']:.2f}"))
            self.top_items_table.setItem(row, 2, QTableWidgetItem(f"{item['sales_amount']:.2f}"))
        self.top_items_table.resizeColumnsToContents()

    def export_low_stock(self) -> None:
        rows = [
            {
                "id": self.low_stock_table.item(row, 0).text(),
                "product": self.low_stock_table.item(row, 1).text(),
                "stock": self.low_stock_table.item(row, 2).text(),
                "reorder_level": self.low_stock_table.item(row, 3).text(),
            }
            for row in range(self.low_stock_table.rowCount())
        ]
        self._run_export(rows, "low_stock")

    def export_expenses(self) -> None:
        rows = [
            {
                "category": self.expenses_table.item(row, 0).text(),
                "total_amount": self.expenses_table.item(row, 1).text(),
            }
            for row in range(self.expenses_table.rowCount())
        ]
        self._run_export(rows, "expenses_by_category")

    def export_movements(self) -> None:
        rows = [
            {
                "id": self.movements_table.item(row, 0).text(),
                "product_id": self.movements_table.item(row, 1).text(),
                "type": self.movements_table.item(row, 2).text(),
                "quantity": self.movements_table.item(row, 3).text(),
                "date": self.movements_table.item(row, 4).text(),
            }
            for row in range(self.movements_table.rowCount())
        ]
        self._run_export(rows, "stock_history")

    def export_top_items(self) -> None:
        rows = [
            {
                "item": self.top_items_table.item(row, 0).text(),
                "qty_sold": self.top_items_table.item(row, 1).text(),
                "sales_amount": self.top_items_table.item(row, 2).text(),
            }
            for row in range(self.top_items_table.rowCount())
        ]
        self._run_export(rows, "top_items")

    def _run_export(self, rows: list, prefix: str) -> None:
        try:
            file_path = self.export_service.export_to_excel(rows, prefix)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def backup_database(self) -> None:
        try:
            backup_path = self.backup_service.create_backup()
            QMessageBox.information(self, "Backup Complete", f"Backup saved to:\n{backup_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed", str(exc))
