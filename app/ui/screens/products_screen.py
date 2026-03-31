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
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.services.signals import app_signals
from app.ui.design_system.async_job import AsyncRunner, JobHandle
from app.ui.design_system.table import Column, TableView
from app.ui.design_system.widgets import PrimaryButton, TitleLabel
from app.ui.widgets.product_form import ProductFormDialog
from app.ui.widgets.stock_adjustment_dialog import StockAdjustmentDialog


class ProductsScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.product_service = ProductService()
        self.category_service = CategoryService()
        self.inventory_service = InventoryService()
        self.business = ensure_default_business()
        self.products = []
        self.async_runner = AsyncRunner()

        self.title = TitleLabel("Products")

        self.add_btn = PrimaryButton("Add Product")
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.delete_btn = QPushButton("Remove")
        self.delete_btn.setEnabled(False)
        self.adjust_btn = QPushButton("Change Stock")
        self.adjust_btn.setEnabled(False)
        self.refresh_btn = QPushButton("Refresh")

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.add_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addWidget(self.adjust_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.refresh_btn)

        self.table = TableView(
            columns=[
                Column("id", "ID", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("name", "Name"),
                Column("category", "Category"),
                Column("sku", "SKU"),
                Column("buying_price", "Buying Price", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("selling_price", "Selling Price", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                Column("stock", "Stock", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]
        )

        self.empty_state_label = QLabel("No products yet. Add one to get started.")
        self.empty_state_label.setStyleSheet("color: rgba(255,255,255,140); font-size: 13px;")
        self.empty_state_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.title)
        layout.addLayout(actions_layout)
        layout.addWidget(self.empty_state_label)
        layout.addWidget(self.table)

        self.add_btn.clicked.connect(self.add_product)
        self.edit_btn.clicked.connect(self.edit_selected_product)
        self.delete_btn.clicked.connect(self.delete_selected_product)
        self.adjust_btn.clicked.connect(self.adjust_selected_stock)
        self.refresh_btn.clicked.connect(self.load_products)
        self.table.table.selectionModel().selectionChanged.connect(lambda *_: self.on_selection_changed())
        self.table.refresh_btn.clicked.connect(self.load_products)

        self.load_products()

    def on_selection_changed(self) -> None:
        """Enable/disable buttons based on selection."""
        has_selection = self.table.table.currentIndex().isValid()
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.adjust_btn.setEnabled(has_selection)

    def load_products(self) -> None:
        self.refresh_btn.setEnabled(False)
        self.table.refresh_btn.setEnabled(False)

        def work():
            return self.product_service.list_products(self.business.id)

        def ok(products):
            self.products = products
            rows = []
            for p in self.products:
                category_name = p.category.name if getattr(p, "category", None) is not None else ""
                rows.append(
                    {
                        "id": p.id,
                        "name": p.name,
                        "category": category_name,
                        "sku": p.sku or "",
                        "buying_price": f"{p.buying_price:.2f}",
                        "selling_price": f"{p.selling_price:.2f}",
                        "stock": f"{p.quantity_in_stock:.2f}",
                    }
                )

            self.table.set_rows(rows)

            is_empty = len(self.products) == 0
            self.empty_state_label.setVisible(is_empty)
            self.table.setVisible(not is_empty)
            if is_empty:
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.adjust_btn.setEnabled(False)

            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        def err(_trace: str):
            self.refresh_btn.setEnabled(True)
            self.table.refresh_btn.setEnabled(True)

        self.async_runner.run(work, JobHandle(on_success=ok, on_error=err))

    def get_selected_product(self):
        selected = self.table.selected_row()
        if not selected:
            return None
        product_id = int(selected["id"])
        for product in self.products:
            if product.id == product_id:
                return product
        return None

    def add_product(self) -> None:
        categories = self.category_service.list_categories(self.business.id)
        dialog = ProductFormDialog(self, categories=categories)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.product_service.create_product(
                    business_id=self.business.id,
                    name=data["name"],
                    sku=data["sku"],
                    barcode=data["barcode"],
                    category_id=data["category_id"],
                    buying_price=data["buying_price"],
                    selling_price=data["selling_price"],
                    quantity_in_stock=data["quantity_in_stock"],
                    reorder_level=data["reorder_level"],
                )
                QMessageBox.information(self, "Success", "Product added successfully.")
                self.load_products()
                app_signals.product_changed.emit()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def edit_selected_product(self) -> None:
        product = self.get_selected_product()
        if product is None:
            QMessageBox.information(self, "No Selection", "Select a product first.")
            return

        categories = self.category_service.list_categories(self.business.id)
        dialog = ProductFormDialog(self, product=product, categories=categories)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.product_service.update_product(
                    product_id=product.id,
                    name=data["name"],
                    sku=data["sku"],
                    barcode=data["barcode"],
                    category_id=data["category_id"],
                    buying_price=data["buying_price"],
                    selling_price=data["selling_price"],
                    quantity_in_stock=data["quantity_in_stock"],
                    reorder_level=data["reorder_level"],
                )
                QMessageBox.information(self, "Success", "Product updated successfully.")
                self.load_products()
                app_signals.product_changed.emit()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def delete_selected_product(self) -> None:
        product = self.get_selected_product()
        if product is None:
            QMessageBox.information(self, "No Selection", "Select a product first.")
            return

        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete product '{product.name}'?",
        )
        if result != QMessageBox.Yes:
            return

        try:
            self.product_service.delete_product(product.id)
            QMessageBox.information(self, "Success", "Product removed successfully.")
            self.load_products()
            app_signals.product_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def adjust_selected_stock(self) -> None:
        product = self.get_selected_product()
        if product is None:
            QMessageBox.information(self, "No Selection", "Select a product first.")
            return

        dialog = StockAdjustmentDialog(self, product=product)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.inventory_service.adjust_stock(
                    product_id=product.id,
                    movement_type=data["movement_type"],
                    quantity=data["quantity"],
                    reference=data["reference"],
                )
                QMessageBox.information(self, "Success", "Stock updated successfully.")
                self.load_products()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))
