from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.pos_service import POSService
from app.services.product_service import ProductService


class POSScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.business = ensure_default_business()
        self.product_service = ProductService()
        self.pos_service = POSService()

        self.products = []
        self.cart = []

        self.title = QLabel("Sales")
        self.title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search product by name, SKU, or barcode")

        self.product_list = QListWidget()

        self.add_btn = QPushButton("Add to Cart")
        self.remove_btn = QPushButton("Remove Selected")
        self.clear_btn = QPushButton("Clear Cart")

        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total"])
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cart_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cart_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMaximum(1_000_000_000)
        self.discount_input.setDecimals(2)
        self.discount_input.setPrefix("Discount: ")

        self.total_label = QLabel("Total: 0.00")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.cash_btn = QPushButton("Complete Cash Sale")
        self.mpesa_btn = QPushButton("Complete M-Pesa Sale")

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Find Product"))
        left_layout.addWidget(self.search_input)
        left_layout.addWidget(QLabel("Products"))
        left_layout.addWidget(self.product_list)
        left_layout.addWidget(self.add_btn)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Cart"))
        right_layout.addWidget(self.cart_table)

        actions = QHBoxLayout()
        actions.addWidget(self.remove_btn)
        actions.addWidget(self.clear_btn)
        actions.addStretch()

        checkout = QGridLayout()
        checkout.addWidget(self.discount_input, 0, 0, 1, 2)
        checkout.addWidget(self.total_label, 1, 0, 1, 2)
        checkout.addWidget(self.cash_btn, 2, 0)
        checkout.addWidget(self.mpesa_btn, 2, 1)

        right_layout.addLayout(actions)
        right_layout.addLayout(checkout)

        content = QHBoxLayout()
        content.addLayout(left_layout, 2)
        content.addLayout(right_layout, 3)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.title)
        main_layout.addLayout(content)

        self.search_input.textChanged.connect(self.filter_products)
        self.add_btn.clicked.connect(self.add_selected_product_to_cart)
        self.remove_btn.clicked.connect(self.remove_selected_cart_item)
        self.clear_btn.clicked.connect(self.clear_cart)
        self.discount_input.valueChanged.connect(self.refresh_cart_table)
        self.cash_btn.clicked.connect(lambda: self.complete_sale("cash"))
        self.mpesa_btn.clicked.connect(lambda: self.complete_sale("mpesa"))

        self.load_products()

    def load_products(self) -> None:
        self.products = [p for p in self.product_service.list_products() if p.active]
        self.render_product_list(self.products)

    def render_product_list(self, products) -> None:
        self.product_list.clear()
        for product in products:
            label = f"{product.name} | KES {product.selling_price:.2f} | Stock: {product.quantity_in_stock:.2f}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, product.id)
            self.product_list.addItem(item)

    def filter_products(self) -> None:
        term = self.search_input.text().strip().lower()
        if not term:
            self.render_product_list(self.products)
            return

        filtered = []
        for product in self.products:
            haystack = " ".join([
                product.name or "",
                product.sku or "",
                product.barcode or "",
            ]).lower()
            if term in haystack:
                filtered.append(product)

        self.render_product_list(filtered)

    def add_selected_product_to_cart(self) -> None:
        item = self.product_list.currentItem()
        if item is None:
            QMessageBox.information(self, "No Selection", "Select a product first.")
            return

        product_id = int(item.data(Qt.UserRole))
        product = next((p for p in self.products if p.id == product_id), None)
        if product is None:
            QMessageBox.warning(self, "Missing Product", "Product could not be found.")
            return

        if product.quantity_in_stock <= 0:
            QMessageBox.warning(self, "Out of Stock", "This product is out of stock.")
            return

        existing = next((x for x in self.cart if x["product_id"] == product.id), None)
        if existing:
            if existing["quantity"] + 1 > product.quantity_in_stock:
                QMessageBox.warning(self, "Stock Limit", "Cannot add more than available stock.")
                return
            existing["quantity"] += 1
        else:
            self.cart.append(
                {
                    "product_id": product.id,
                    "name": product.name,
                    "quantity": 1.0,
                    "unit_price": float(product.selling_price),
                }
            )

        self.refresh_cart_table()

    def refresh_cart_table(self) -> None:
        self.cart_table.setRowCount(len(self.cart))
        subtotal = 0.0

        for row, item in enumerate(self.cart):
            line_total = item["quantity"] * item["unit_price"]
            subtotal += line_total

            self.cart_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"{item['quantity']:.2f}"))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{line_total:.2f}"))

        total = subtotal - float(self.discount_input.value())
        if total < 0:
            total = 0.0

        self.total_label.setText(f"Total: {total:.2f}")
        self.cart_table.resizeColumnsToContents()

    def remove_selected_cart_item(self) -> None:
        row = self.cart_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Select a cart item first.")
            return

        self.cart.pop(row)
        self.refresh_cart_table()

    def clear_cart(self) -> None:
        self.cart.clear()
        self.discount_input.setValue(0.0)
        self.refresh_cart_table()

    def complete_sale(self, payment_method: str) -> None:
        if not self.cart:
            QMessageBox.information(self, "Empty Cart", "Add items to the cart first.")
            return

        transaction_ref = None
        if payment_method == "mpesa":
            transaction_ref = "MANUAL-MPESA"

        try:
            sale = self.pos_service.process_sale(
                business_id=self.business.id,
                cart_items=self.cart,
                payment_method=payment_method,
                discount=float(self.discount_input.value()),
                cashier_id=None,
                transaction_ref=transaction_ref,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Sale Failed", str(exc))
            return

        QMessageBox.information(
            self,
            "Sale Complete",
            f"Sale saved successfully.\n\nSale No: {sale.id}\nTotal: {sale.total:.2f}"
        )

        self.cart.clear()
        self.discount_input.setValue(0.0)
        self.refresh_cart_table()
        self.load_products()
