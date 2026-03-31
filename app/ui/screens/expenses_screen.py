from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.expense_service import ExpenseService
from app.ui.design_system.async_job import AsyncRunner, JobHandle
from app.ui.design_system.table import Column, TableView
from app.ui.design_system.widgets import PrimaryButton, TitleLabel
from app.ui.widgets.expense_form import ExpenseFormDialog


class ExpensesScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.business = ensure_default_business()
        self.expense_service = ExpenseService()
        self.expenses = []
        self.async_runner = AsyncRunner()

        self.title = TitleLabel("Expenses")

        self.add_btn = PrimaryButton("Record Expense")
        self.refresh_btn = QPushButton("Refresh")

        actions = QHBoxLayout()
        actions.addWidget(self.add_btn)
        actions.addStretch()
        actions.addWidget(self.refresh_btn)

        self.table = TableView(
            columns=[
                Column("id", "ID", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("category", "Category"),
                Column("amount", "Amount", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("payment", "Payment"),
                Column("reference", "Reference"),
                Column("date", "Date"),
            ]
        )

        self.empty_state_label = QLabel("No expenses recorded yet.")
        self.empty_state_label.setStyleSheet("color: rgba(255,255,255,140); font-size: 13px;")
        self.empty_state_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.title)
        layout.addLayout(actions)
        layout.addWidget(self.empty_state_label)
        layout.addWidget(self.table)

        self.add_btn.clicked.connect(self.add_expense)
        self.refresh_btn.clicked.connect(self.load_expenses)
        self.table.refresh_btn.clicked.connect(self.load_expenses)

        self.load_expenses()

    def load_expenses(self) -> None:
        self.refresh_btn.setEnabled(False)
        self.table.refresh_btn.setEnabled(False)

        def work():
            return self.expense_service.list_recent_expenses(self.business.id, limit=200)

        def ok(expenses):
            self.expenses = expenses
            rows = []
            for e in self.expenses:
                rows.append(
                    {
                        "id": e.id,
                        "category": e.category,
                        "amount": f"{e.amount:.2f}",
                        "payment": e.payment_method.upper(),
                        "reference": e.reference or "",
                        "date": e.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                )
            self.table.set_rows(rows)

            is_empty = len(self.expenses) == 0
            self.empty_state_label.setVisible(is_empty)
            self.table.setVisible(not is_empty)

            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        def err(_trace: str):
            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        self.async_runner.run(work, JobHandle(on_success=ok, on_error=err))

    def add_expense(self) -> None:
        dialog = ExpenseFormDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.expense_service.create_expense(
                    business_id=self.business.id,
                    category=data["category"],
                    amount=data["amount"],
                    description=data["description"],
                    payment_method=data["payment_method"],
                    reference=data["reference"],
                    recorded_by=None,
                )
                QMessageBox.information(self, "Success", "Expense recorded successfully.")
                self.load_expenses()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))
