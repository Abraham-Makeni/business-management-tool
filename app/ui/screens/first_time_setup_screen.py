from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.seed import ensure_default_business
from app.services.auth_service import AuthenticationService
from app.services.session_manager import SessionManager
from app.services.settings_service import SettingsService


class FirstTimeSetupScreen(QWidget):
    setup_completed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.auth_service = AuthenticationService()
        self.settings_service = SettingsService()
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle("First-Time Setup - Business Tool")
        self.setFixedSize(500, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(18)

        title = QLabel("Set up your business")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Create the owner account to secure your system.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)

        business = ensure_default_business()

        self.business_name_input = QLineEdit()
        self.business_name_input.setPlaceholderText("Business name")
        self.business_name_input.setText(business.business_name or "")
        form.addRow("Business Name:", self.business_name_input)

        self.owner_name_input = QLineEdit()
        self.owner_name_input.setPlaceholderText("Owner full name")
        form.addRow("Owner Name:", self.owner_name_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Owner username")
        form.addRow("Username:", self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Optional email for recovery")
        form.addRow("Email:", self.email_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Optional phone number")
        form.addRow("Phone:", self.phone_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter a secure password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirm Password:", self.confirm_password_input)

        layout.addLayout(form)

        self.create_button = QPushButton("Create Owner Account")
        self.create_button.setMinimumHeight(45)
        self.create_button.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.create_button.clicked.connect(self.create_owner_account)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.create_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        note = QLabel(
            "Once completed, the owner account will be used for all staff management and login control."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray;")
        layout.addWidget(note)
        layout.addStretch()

    def create_owner_account(self) -> None:
        business_name = self.business_name_input.text().strip()
        owner_name = self.owner_name_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not business_name:
            QMessageBox.warning(self, "Invalid Input", "Business name is required.")
            return

        if not owner_name:
            QMessageBox.warning(self, "Invalid Input", "Owner name is required.")
            return

        if not username:
            QMessageBox.warning(self, "Invalid Input", "Owner username is required.")
            return

        if not password:
            QMessageBox.warning(self, "Invalid Input", "Owner password is required.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            return

        try:
            business = ensure_default_business()
            self.settings_service.update_business_settings(
                business_id=business.id,
                business_name=business_name,
                phone=phone,
            )

            owner = self.auth_service.create_user(
                business_id=business.id,
                name=owner_name,
                username=username,
                password=password,
                role="owner",
                email=email or None,
                phone=phone or None,
                must_change_password=False,
            )

            SessionManager.login_user(owner)
            QMessageBox.information(
                self,
                "Setup Complete",
                "Owner account created successfully. You are now logged in.",
            )
            self.setup_completed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Setup Error", f"Unable to create owner account: {exc}")
