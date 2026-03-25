from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.database.models.product import Product


class StockAdjustmentDialog(QDialog):
    def __init__(self, parent=None, product: Product | None = None) -> None:
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Adjust Stock")
        self.resize(400, 180)

        self.type_input = QComboBox()
        self.type_input.addItems(["stock_in", "stock_out", "adjustment", "damaged", "expired", "returned"])

        self.qty_input = QDoubleSpinBox()
        self.qty_input.setMaximum(1_000_000_000)
        self.qty_input.setDecimals(2)
        self.qty_input.setMinimum(0.01)

        self.reference_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Movement Type", self.type_input)
        form.addRow("Quantity", self.qty_input)
        form.addRow("Notes", self.reference_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        if self.qty_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than zero.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "movement_type": self.type_input.currentText(),
            "quantity": float(self.qty_input.value()),
            "reference": self.reference_input.text().strip() or None,
        }
