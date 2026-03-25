from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.database.models.product import Product


class ProductFormDialog(QDialog):
    def __init__(self, parent=None, product: Product | None = None) -> None:
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Add Product" if product is None else "Edit Product")
        self.setModal(True)
        self.resize(420, 260)

        self.name_input = QLineEdit()
        self.sku_input = QLineEdit()
        self.barcode_input = QLineEdit()

        self.buying_price_input = QDoubleSpinBox()
        self.buying_price_input.setMaximum(1_000_000_000)
        self.buying_price_input.setDecimals(2)

        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setMaximum(1_000_000_000)
        self.selling_price_input.setDecimals(2)

        self.stock_input = QDoubleSpinBox()
        self.stock_input.setMaximum(1_000_000_000)
        self.stock_input.setDecimals(2)

        self.reorder_input = QDoubleSpinBox()
        self.reorder_input.setMaximum(1_000_000_000)
        self.reorder_input.setDecimals(2)

        form = QFormLayout()
        form.addRow("Name", self.name_input)
        form.addRow("SKU", self.sku_input)
        form.addRow("Barcode", self.barcode_input)
        form.addRow("Buying Price", self.buying_price_input)
        form.addRow("Selling Price", self.selling_price_input)
        form.addRow("Stock Qty", self.stock_input)
        form.addRow("Reorder Level", self.reorder_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if self.product is not None:
            self._load_product()

    def _load_product(self) -> None:
        self.name_input.setText(self.product.name)
        self.sku_input.setText(self.product.sku or "")
        self.barcode_input.setText(self.product.barcode or "")
        self.buying_price_input.setValue(float(self.product.buying_price))
        self.selling_price_input.setValue(float(self.product.selling_price))
        self.stock_input.setValue(float(self.product.quantity_in_stock))
        self.reorder_input.setValue(float(self.product.reorder_level))

    def _validate_and_accept(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Product name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "sku": self.sku_input.text().strip() or None,
            "barcode": self.barcode_input.text().strip() or None,
            "buying_price": float(self.buying_price_input.value()),
            "selling_price": float(self.selling_price_input.value()),
            "quantity_in_stock": float(self.stock_input.value()),
            "reorder_level": float(self.reorder_input.value()),
        }
