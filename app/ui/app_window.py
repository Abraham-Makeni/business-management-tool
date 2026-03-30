from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QWidget,
    QLabel,
)

from app.ui.screens.categories_screen import CategoriesScreen
from app.ui.screens.dashboard_screen import DashboardScreen
from app.ui.screens.expenses_screen import ExpensesScreen
from app.ui.screens.first_time_setup_screen import FirstTimeSetupScreen
from app.ui.screens.inventory_screen import InventoryScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.pos_screen import POSScreen
from app.ui.screens.products_screen import ProductsScreen
from app.ui.screens.reports_screen import ReportsScreen
from app.ui.screens.settings_screen import SettingsScreen
from app.ui.screens.users_screen import UsersScreen
from app.database.seed import ensure_default_business
from app.services.auth_service import AuthenticationService
from app.services.session_manager import SessionManager
from app.services.permissions import *


class AppWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Business Management Tool")
        self.resize(1280, 760)

        self.auth_service = AuthenticationService()

        # Create login and setup screens
        self.login_screen = LoginScreen(business_name=self.get_business_name())
        self.login_screen.login_successful.connect(self.show_main_interface)

        self.first_time_setup_screen = FirstTimeSetupScreen()
        self.first_time_setup_screen.setup_completed.connect(self.show_main_interface)

        # Main interface widgets are created when the user logs in
        self.nav_list = None
        self.logout_button = None
        self.stack = None
        self.drawer_open = False
        self.nav_container = None

        # Show first-run setup or login depending on owner existence
        if self.auth_service.owner_exists():
            self.setCentralWidget(self.login_screen)
        else:
            self.setCentralWidget(self.first_time_setup_screen)

    def setup_navigation(self):
        """Setup navigation items based on user role."""
        self.nav_list.clear()

        # Define navigation items with required permissions and stack indexes
        nav_items = [
            ("Dashboard", VIEW_DASHBOARD, 0),
            ("Products", VIEW_PRODUCTS, 1),
            ("Categories", VIEW_CATEGORIES, 2),
            ("Inventory", VIEW_INVENTORY, 3),
            ("Sales", ACCESS_SALES, 4),
            ("Expenses", RECORD_EXPENSES, 5),
            ("Reports", VIEW_REPORTS, 6),
            ("Users", MANAGE_USERS, 7),
            ("Settings", MANAGE_SETTINGS, 8),
        ]

        for item_text, permission, stack_index in nav_items:
            if SessionManager.has_permission(permission):
                item = QListWidgetItem(item_text, self.nav_list)
                item.setData(Qt.UserRole, stack_index)

        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)

    def get_business_name(self) -> str:
        business = ensure_default_business()
        return business.business_name or "Business Tool"

    def show_main_interface(self):
        """Show the main application interface after successful login."""
        # Create the main interface widgets each time so they are fresh
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(220)
        self.nav_list.currentRowChanged.connect(self.switch_page)

        self.logout_button = QPushButton("Log Out")
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setFixedHeight(40)

        self.menu_button = QPushButton("☰")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.clicked.connect(self.toggle_drawer)

        self.stack = QStackedWidget()
        self.stack.addWidget(DashboardScreen())
        self.stack.addWidget(ProductsScreen())
        self.stack.addWidget(CategoriesScreen())
        self.stack.addWidget(InventoryScreen())
        self.stack.addWidget(POSScreen())
        self.stack.addWidget(ExpensesScreen())
        self.stack.addWidget(ReportsScreen())
        self.stack.addWidget(UsersScreen())
        self.stack.addWidget(SettingsScreen())

        # Setup navigation based on role (now that user is logged in)
        self.setup_navigation()

        self.nav_container = QWidget()
        self.nav_container.setObjectName("navContainer")
        self.nav_container.setFixedWidth(220)
        nav_layout = QVBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)
        nav_layout.addWidget(self.nav_list)
        nav_layout.addWidget(self.logout_button)
        nav_layout.addStretch()
        self.nav_container.hide()

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.nav_container)
        content_layout.addWidget(self.stack, 1)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(10)
        header_layout.addWidget(self.menu_button)
        header_title = QLabel(self.get_business_name())
        header_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        layout.addWidget(header)
        layout.addLayout(content_layout)

        self.setCentralWidget(container)
        # Get username safely
        current_user = SessionManager.get_current_user()
        username = current_user.username if current_user else "Unknown"
        self.setWindowTitle(f"Business Management Tool - {username}")

    def toggle_drawer(self) -> None:
        if not self.nav_container:
            return
        self.drawer_open = not self.drawer_open
        if self.drawer_open:
            self.nav_container.show()
            self.menu_button.setText("×")
        else:
            self.nav_container.hide()
            self.menu_button.setText("☰")

    def switch_page(self, row: int) -> None:
        item = self.nav_list.item(row)
        if not item:
            return
        stack_index = item.data(Qt.UserRole)
        if stack_index is not None:
            self.stack.setCurrentIndex(int(stack_index))

    def logout(self) -> None:
        SessionManager.logout_user()
        self.login_screen = LoginScreen(business_name=self.get_business_name())
        self.login_screen.login_successful.connect(self.show_main_interface)
        self.setCentralWidget(self.login_screen)
        self.setWindowTitle("Business Management Tool")