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
from app.services.category_service import CategoryService
from app.ui.design_system.async_job import AsyncRunner, JobHandle
from app.ui.design_system.table import Column, TableView
from app.ui.design_system.widgets import PrimaryButton, TitleLabel
from app.ui.widgets.category_form import CategoryFormDialog


class CategoriesScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.business = ensure_default_business()
        self.category_service = CategoryService()
        self.categories = []
        self.async_runner = AsyncRunner()

        self.title = TitleLabel("Categories")

        self.add_btn = PrimaryButton("Add Category")
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.delete_btn = QPushButton("Remove")
        self.delete_btn.setEnabled(False)
        self.refresh_btn = QPushButton("Refresh")

        actions = QHBoxLayout()
        actions.addWidget(self.add_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()
        actions.addWidget(self.refresh_btn)

        self.table = TableView(
            columns=[
                Column("id", "ID", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("name", "Name"),
            ]
        )

        self.empty_state_label = QLabel("No categories yet. Add one to get started.")
        self.empty_state_label.setStyleSheet("color: rgba(255,255,255,140); font-size: 13px;")
        self.empty_state_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.title)
        layout.addLayout(actions)
        layout.addWidget(self.empty_state_label)
        layout.addWidget(self.table)

        self.add_btn.clicked.connect(self.add_category)
        self.edit_btn.clicked.connect(self.edit_selected_category)
        self.delete_btn.clicked.connect(self.delete_selected_category)
        self.refresh_btn.clicked.connect(self.load_categories)
        self.table.table.selectionModel().selectionChanged.connect(lambda *_: self.on_selection_changed())
        self.table.refresh_btn.clicked.connect(self.load_categories)

        self.load_categories()

    def on_selection_changed(self) -> None:
        """Enable/disable buttons based on selection."""
        has_selection = self.table.table.currentIndex().isValid()
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def load_categories(self) -> None:
        self.refresh_btn.setEnabled(False)
        self.table.refresh_btn.setEnabled(False)

        def work():
            return self.category_service.list_categories(self.business.id)

        def ok(categories):
            self.categories = categories
            rows = [{"id": c.id, "name": c.name} for c in self.categories]
            self.table.set_rows(rows)

            is_empty = len(self.categories) == 0
            self.empty_state_label.setVisible(is_empty)
            self.table.setVisible(not is_empty)
            if is_empty:
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)

            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        def err(_trace: str):
            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        self.async_runner.run(work, JobHandle(on_success=ok, on_error=err))

    def get_selected_category(self):
        selected = self.table.selected_row()
        if not selected:
            return None
        category_id = int(selected["id"])
        for category in self.categories:
            if category.id == category_id:
                return category
        return None

    def add_category(self) -> None:
        dialog = CategoryFormDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.category_service.create_category(self.business.id, data["name"])
                QMessageBox.information(self, "Success", "Category added successfully.")
                self.load_categories()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def edit_selected_category(self) -> None:
        category = self.get_selected_category()
        if category is None:
            QMessageBox.information(self, "No Selection", "Select a category first.")
            return

        dialog = CategoryFormDialog(self, category=category)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.category_service.update_category(category.id, self.business.id, data["name"])
                QMessageBox.information(self, "Success", "Category updated successfully.")
                self.load_categories()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def delete_selected_category(self) -> None:
        category = self.get_selected_category()
        if category is None:
            QMessageBox.information(self, "No Selection", "Select a category first.")
            return

        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete category '{category.name}'?",
        )
        if result != QMessageBox.Yes:
            return

        try:
            self.category_service.delete_category(category.id)
            QMessageBox.information(self, "Success", "Category removed successfully.")
            self.load_categories()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
