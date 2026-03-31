from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from app.database.seed import ensure_default_business
from app.services.auth_service import AuthenticationService
from app.services.permissions import MANAGE_USERS
from app.services.session_manager import SessionManager


class UsersScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.auth_service = AuthenticationService()
        self.business = ensure_default_business()
        self._initialized = False
        from app.ui.design_system.async_job import AsyncRunner

        self.async_runner = AsyncRunner()

    def _init_ui(self) -> None:
        if self._initialized:
            return

        if not SessionManager.has_permission(MANAGE_USERS):
            self.show_permission_denied()
            return

        from app.ui.design_system.widgets import GlassCard, PrimaryButton, SubtitleLabel, TitleLabel

        title = TitleLabel("User Management")
        subtitle = SubtitleLabel("Create staff accounts, reset credentials, and manage access.")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Optional email")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Optional phone")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Temporary password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_input = QComboBox()
        self.role_input.addItems(["cashier", "inventory_manager", "owner"])

        add_form = QFormLayout()
        add_form.addRow("Name:", self.name_input)
        add_form.addRow("Username:", self.username_input)
        add_form.addRow("Email:", self.email_input)
        add_form.addRow("Phone:", self.phone_input)
        add_form.addRow("Role:", self.role_input)
        add_form.addRow("Password:", self.password_input)

        create_button = PrimaryButton("Add User")
        create_button.clicked.connect(self.add_user)
        create_button.setMinimumHeight(40)

        self.user_list_container = QWidget()
        self.user_list_layout = QVBoxLayout(self.user_list_container)
        self.user_list_layout.setSpacing(10)
        self.user_list_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.user_list_container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(add_form)
        layout.addWidget(create_button)
        existing = QLabel("Existing users")
        existing.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(existing)
        layout.addWidget(self.scroll_area)
        layout.addStretch()

        self._initialized = True
        self.load_users()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._init_ui()

    def show_permission_denied(self) -> None:
        layout = QVBoxLayout(self)
        denied_label = QLabel("Access Denied")
        denied_label.setStyleSheet("font-size: 18px; font-weight: 700;")
        denied_label.setAlignment(Qt.AlignCenter)

        message_label = QLabel("You don't have permission to manage users.")
        message_label.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(denied_label)
        layout.addWidget(message_label)
        layout.addStretch()

    def clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_users(self) -> None:
        self.clear_layout(self.user_list_layout)

        users = self.auth_service.get_users_for_business(self.business.id)
        for user in users:
            self.user_list_layout.addWidget(self.build_user_widget(user))

        self.user_list_layout.addStretch()

    def build_user_widget(self, user) -> QWidget:
        from app.ui.design_system.widgets import GlassCard

        widget = GlassCard()

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        user_info = QLabel(
            f"{user.name} ({user.username}) — {user.role.replace('_', ' ').title()}"
            f"\nStatus: {'Active' if user.status else 'Disabled'}"
        )
        user_info.setWordWrap(True)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        toggle_button = QPushButton("Disable" if user.status else "Enable")
        toggle_button.clicked.connect(lambda _, u=user: self.toggle_user_status(u))
        action_layout.addWidget(toggle_button)

        reset_button = QPushButton("Reset Password")
        reset_button.clicked.connect(lambda _, u=user: self.reset_password_dialog(u))
        action_layout.addWidget(reset_button)

        if user.role == "owner" and user.status:
            active_owner_count = self.auth_service.get_active_owner_count()
            if active_owner_count <= 1:
                toggle_button.setEnabled(False)

        layout.addWidget(user_info, 1)
        layout.addLayout(action_layout)

        return widget

    def add_user(self) -> None:
        name = self.name_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text()
        role = self.role_input.currentText()

        if not name or not username or not password:
            QMessageBox.warning(self, "Invalid Input", "Name, username, and password are required.")
            return

        try:
            self.auth_service.create_user(
                business_id=self.business.id,
                name=name,
                username=username,
                password=password,
                role=role,
                email=email or None,
                phone=phone or None,
            )
            QMessageBox.information(self, "User Added", "Staff account created successfully.")
            self.name_input.clear()
            self.username_input.clear()
            self.email_input.clear()
            self.phone_input.clear()
            self.password_input.clear()
            self.role_input.setCurrentIndex(0)
            self.load_users()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to create user: {exc}")

    def toggle_user_status(self, user) -> None:
        if user.status:
            if not self.auth_service.disable_user(user.id):
                QMessageBox.warning(
                    self,
                    "Action Denied",
                    "Unable to disable the last active owner account.",
                )
                return
        else:
            if not self.auth_service.enable_user(user.id):
                QMessageBox.warning(
                    self,
                    "Action Failed",
                    "Unable to enable this account.",
                )
                return

        self.load_users()

    def reset_password_dialog(self, user) -> None:
        new_password, ok = QInputDialog.getText(
            self,
            "Reset Password",
            f"Enter a new password for {user.username}:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not new_password:
            return

        confirm_password, ok = QInputDialog.getText(
            self,
            "Confirm Password",
            "Confirm the new password:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or new_password != confirm_password:
            QMessageBox.warning(self, "Reset Failed", "Passwords do not match.")
            return

        if not self.auth_service.reset_user_password(user.id, new_password):
            QMessageBox.critical(self, "Reset Failed", "Unable to reset the password.")
            return

        QMessageBox.information(self, "Password Reset", "Password was reset successfully.")
