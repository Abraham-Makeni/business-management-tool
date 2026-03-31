from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.settings_service import SettingsService
from app.services.session_manager import SessionManager
from app.services.permissions import MANAGE_SETTINGS


class SettingsScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def _init_ui(self) -> None:
        """Initialize the UI components (called lazily when screen is shown)."""
        if self._initialized:
            return

        # Check permissions
        if not SessionManager.has_permission(MANAGE_SETTINGS):
            self.show_permission_denied()
            return

        self.business = ensure_default_business()
        self.settings_service = SettingsService()

        from app.ui.design_system.widgets import PrimaryButton, TitleLabel

        self.title = TitleLabel("Settings")

        # Business Profile Section
        profile_section = QLabel("Business Profile")
        profile_section.setStyleSheet("font-size: 14px; font-weight: 700;")

        form = QFormLayout()

        # Business Name
        self.business_name_input = QLineEdit()
        self.business_name_input.setText(self.business.business_name or "")
        form.addRow("Business Name:", self.business_name_input)

        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setText(self.business.phone or "")
        self.phone_input.setPlaceholderText("e.g. +254712345678")
        form.addRow("Phone:", self.phone_input)

        # Location
        self.location_input = QLineEdit()
        self.location_input.setText(self.business.location or "")
        self.location_input.setPlaceholderText("e.g. Nairobi or Shop Address")
        form.addRow("Location:", self.location_input)

        # Preferences Section
        preferences_section = QLabel("Preferences")
        preferences_section.setStyleSheet("font-size: 14px; font-weight: 700; margin-top: 20px;")
        form.addRow(preferences_section)

        # Currency
        self.currency_input = QLineEdit()
        self.currency_input.setText(self.business.currency or "KES")
        self.currency_input.setPlaceholderText("e.g. KES")
        form.addRow("Currency:", self.currency_input)

        # Tax Percent
        self.tax_percent_input = QDoubleSpinBox()
        self.tax_percent_input.setDecimals(2)
        self.tax_percent_input.setRange(0.0, 100.0)
        self.tax_percent_input.setValue(float(self.business.tax_percent or 0.0))
        self.tax_percent_input.setSuffix(" %")
        form.addRow("Tax (%):", self.tax_percent_input)

        # Receipt Footer
        self.receipt_footer_input = QLineEdit()
        self.receipt_footer_input.setText(self.business.receipt_footer or "")
        self.receipt_footer_input.setPlaceholderText("e.g. Thank you for your purchase!")
        form.addRow("Receipt Footer:", self.receipt_footer_input)

        # Buttons
        save_btn = PrimaryButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_btn)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.title)
        layout.addWidget(profile_section)
        layout.addLayout(form)
        layout.addLayout(button_layout)
        layout.addStretch()

        self._initialized = True

    def showEvent(self, event):
        """Called when the screen is shown."""
        super().showEvent(event)
        self._init_ui()

    def show_permission_denied(self):
        """Show permission denied message."""
        layout = QVBoxLayout(self)
        denied_label = QLabel("Access Denied")
        denied_label.setStyleSheet("font-size: 18px; font-weight: 700;")
        denied_label.setAlignment(Qt.AlignCenter)

        message_label = QLabel("You don't have permission to access Settings.")
        message_label.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(denied_label)
        layout.addWidget(message_label)
        layout.addStretch()

    def save_settings(self) -> None:
        """Save business settings."""
        try:
            business_name = self.business_name_input.text().strip()
            if not business_name:
                QMessageBox.warning(self, "Invalid Input", "Business name is required.")
                return

            self.settings_service.update_business_settings(
                business_id=self.business.id,
                business_name=business_name,
                phone=self.phone_input.text(),
                location=self.location_input.text(),
                currency=self.currency_input.text(),
                tax_percent=self.tax_percent_input.value(),
                receipt_footer=self.receipt_footer_input.text(),
            )

            QMessageBox.information(self, "Success", "Settings saved successfully!")
            # Refresh business object
            self.business = self.settings_service.get_business_settings(self.business.id)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {exc}")