from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.product_service import ProductService
from app.ui.widgets.product_form import ProductFormDialog


class ProductsScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.product_service = ProductService()
        self.business = ensure_default_business()
        self.products = []

        self.title = QLabel("Products")

        self.add_btn = QPushButton("Add Product")
        self.edit_btn = QPushButton("Edit Selected")
        self.delete_btn = QPushButton("Delete Selected")
        self.refresh_btn = QPushButton("Refresh")

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.add_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.refresh_btn)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "SKU", "Buying Price", "Selling Price", "Stock"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(actions_layout)
        layout.addWidget(self.table)

        self.add_btn.clicked.connect(self.add_product)
        self.edit_btn.clicked.connect(self.edit_selected_product)
        self.delete_btn.clicked.connect(self.delete_selected_product)
        self.refresh_btn.clicked.connect(self.load_products)

        self.load_products()

    def load_products(self) -> None:
        self.products = self.product_service.list_products()
        self.table.setRowCount(len(self.products))

        for row, product in enumerate(self.products):
            id_item = QTableWidgetItem(str(product.id))
            id_item.setData(Qt.UserRole, product.id)

            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, QTableWidgetItem(product.name))
            self.table.setItem(row, 2, QTableWidgetItem(product.sku or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f"{product.buying_price:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{product.selling_price:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{product.quantity_in_stock:.2f}"))

        self.table.resizeColumnsToContents()

    def get_selected_product_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return int(item.data(Qt.UserRole))

    def get_selected_product(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            return None
        for product in self.products:
            if product.id == product_id:
                return product
        return None

    def add_product(self) -> None:
        dialog = ProductFormDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.product_service.create_product(
                    business_id=self.business.id,
                    name=data["name"],
                    sku=data["sku"],
                    barcode=data["barcode"],
                    buying_price=data["buying_price"],
                    selling_price=data["selling_price"],
                    quantity_in_stock=data["quantity_in_stock"],
                    reorder_level=data["reorder_level"],
                )
                self.load_products()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def edit_selected_product(self) -> None:
        product = self.get_selected_product()
        if product is None:
            QMessageBox.information(self, "No Selection", "Select a product first.")
            return

        dialog = ProductFormDialog(self, product=product)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.product_service.update_product(
                    product_id=product.id,
                    name=data["name"],
                    sku=data["sku"],
                    barcode=data["barcode"],
                    buying_price=data["buying_price"],
                    selling_price=data["selling_price"],
                    quantity_in_stock=data["quantity_in_stock"],
                    reorder_level=data["reorder_level"],
                )
                self.load_products()
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
            self.load_products()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
