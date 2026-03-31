from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.backup_service import BackupService
from app.services.export_service import ExportService
from app.services.reporting_service import ReportingService
from app.ui.design_system.async_job import AsyncRunner, JobHandle
from app.ui.design_system.table import Column, TableView
from app.ui.design_system.widgets import PrimaryButton, SubtitleLabel, TitleLabel


class ReportsScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.business = ensure_default_business()
        self.reporting_service = ReportingService()
        self.export_service = ExportService()
        self.backup_service = BackupService()
        self.async_runner = AsyncRunner()

        self.title = TitleLabel("Reports")

        self.refresh_btn = PrimaryButton("Refresh")
        self.backup_btn = QPushButton("Backup Database")

        top_actions = QHBoxLayout()
        top_actions.addWidget(self.refresh_btn)
        top_actions.addStretch()
        top_actions.addWidget(self.backup_btn)

        self.summary_label = SubtitleLabel("Summary will appear here")

        self.tabs = QTabWidget()

        self.low_stock_table = TableView(
            columns=[
                Column("id", "ID", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("product", "Product"),
                Column("stock", "Stock", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("reorder_level", "Reorder Level", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]
        )
        self.low_stock_export_btn = QPushButton("Export Low Stock")

        self.expenses_table = TableView(
            columns=[
                Column("category", "Category"),
                Column("total_amount", "Total Amount", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]
        )
        self.expenses_export_btn = QPushButton("Export Expenses")

        self.movements_table = TableView(
            columns=[
                Column("id", "ID", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("product_id", "Product ID", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("type", "Type"),
                Column("quantity", "Quantity", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("date", "Date"),
            ]
        )
        self.movements_export_btn = QPushButton("Export Stock History")

        self.top_items_table = TableView(
            columns=[
                Column("item", "Item"),
                Column("qty_sold", "Qty Sold", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("sales_amount", "Sales Amount", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]
        )
        self.top_items_export_btn = QPushButton("Export Top Items")

        self.tabs.addTab(self._wrap_tab(self.low_stock_table, self.low_stock_export_btn), "Low Stock")
        self.tabs.addTab(self._wrap_tab(self.expenses_table, self.expenses_export_btn), "Expenses")
        self.tabs.addTab(self._wrap_tab(self.movements_table, self.movements_export_btn), "Stock History")
        self.tabs.addTab(self._wrap_tab(self.top_items_table, self.top_items_export_btn), "Top Items")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
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

    def _wrap_tab(self, table: QWidget, button: QPushButton) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(button)
        layout.addWidget(table)
        return tab

    def load_reports(self) -> None:
        self.refresh_btn.setEnabled(False)

        def work():
            summary = self.reporting_service.get_daily_sales_summary(self.business.id)
            low_stock = self.reporting_service.get_low_stock_products(self.business.id)
            expenses = self.reporting_service.get_expenses_by_category(self.business.id)
            movements = self.reporting_service.get_recent_stock_movements(limit=200)
            top_items = self.reporting_service.get_top_selling_items(self.business.id, limit=20)
            return summary, low_stock, expenses, movements, top_items

        def ok(payload):
            summary, low_stock, expenses, movements, top_items = payload
            self.summary_label.setText(
                f"Today's Sales: KES {summary['total_sales']:.2f} | "
                f"Transactions: {summary['transaction_count']} | "
                f"Expenses: KES {summary['total_expenses']:.2f} | "
                f"Estimated Balance: KES {summary['estimated_balance']:.2f}"
            )

            self.low_stock_table.set_rows(
                [
                    {
                        "id": p.id,
                        "product": p.name,
                        "stock": f"{p.quantity_in_stock:.2f}",
                        "reorder_level": f"{p.reorder_level:.2f}",
                    }
                    for p in low_stock
                ]
            )
            self.expenses_table.set_rows(
                [
                    {"category": item["category"], "total_amount": f"{item['total_amount']:.2f}"}
                    for item in expenses
                ]
            )
            self.movements_table.set_rows(
                [
                    {
                        "id": m.id,
                        "product_id": m.product_id,
                        "type": m.movement_type,
                        "quantity": f"{m.quantity:.2f}",
                        "date": m.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                    for m in movements
                ]
            )
            self.top_items_table.set_rows(
                [
                    {
                        "item": item["name"],
                        "qty_sold": f"{item['qty_sold']:.2f}",
                        "sales_amount": f"{item['sales_amount']:.2f}",
                    }
                    for item in top_items
                ]
            )

            self.refresh_btn.setEnabled(True)

        def err(_trace: str):
            self.refresh_btn.setEnabled(True)

        self.async_runner.run(work, JobHandle(on_success=ok, on_error=err))

    def export_low_stock(self) -> None:
        rows = [self.low_stock_table.model.row_at(i) for i in range(self.low_stock_table.model.rowCount())]
        rows = [r for r in rows if r is not None]
        self._run_export(rows, "low_stock")

    def export_expenses(self) -> None:
        rows = [self.expenses_table.model.row_at(i) for i in range(self.expenses_table.model.rowCount())]
        rows = [r for r in rows if r is not None]
        self._run_export(rows, "expenses_by_category")

    def export_movements(self) -> None:
        rows = [self.movements_table.model.row_at(i) for i in range(self.movements_table.model.rowCount())]
        rows = [r for r in rows if r is not None]
        self._run_export(rows, "stock_history")

    def export_top_items(self) -> None:
        rows = [self.top_items_table.model.row_at(i) for i in range(self.top_items_table.model.rowCount())]
        rows = [r for r in rows if r is not None]
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
