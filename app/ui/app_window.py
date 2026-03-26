from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QWidget,
)

from app.ui.screens.categories_screen import CategoriesScreen
from app.ui.screens.dashboard_screen import DashboardScreen
from app.ui.screens.expenses_screen import ExpensesScreen
from app.ui.screens.inventory_screen import InventoryScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.pos_screen import POSScreen
from app.ui.screens.products_screen import ProductsScreen
from app.ui.screens.reports_screen import ReportsScreen
from app.ui.screens.settings_screen import SettingsScreen
from app.services.session_manager import SessionManager
from app.services.permissions import *


class AppWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Business Management Tool")
        self.resize(1280, 760)

        # Create login screen
        self.login_screen = LoginScreen()
        self.login_screen.login_successful.connect(self.show_main_interface)

        # Create main interface widgets
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(220)

        self.stack = QStackedWidget()
        self.stack.addWidget(DashboardScreen())
        self.stack.addWidget(ProductsScreen())
        self.stack.addWidget(CategoriesScreen())
        self.stack.addWidget(InventoryScreen())
        self.stack.addWidget(POSScreen())
        self.stack.addWidget(ExpensesScreen())
        self.stack.addWidget(ReportsScreen())
        self.stack.addWidget(SettingsScreen())

        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)

        # Don't setup navigation yet - will be done after login
        # self.setup_navigation()

        # Show login screen first
        self.setCentralWidget(self.login_screen)

    def setup_navigation(self):
        """Setup navigation items based on user role."""
        self.nav_list.clear()

        # Define navigation items with required permissions
        nav_items = [
            ("Dashboard", VIEW_DASHBOARD),
            ("Products", VIEW_PRODUCTS),
            ("Categories", VIEW_CATEGORIES),
            ("Inventory", VIEW_INVENTORY),
            ("Sales", ACCESS_SALES),
            ("Expenses", RECORD_EXPENSES),
            ("Reports", VIEW_REPORTS),
            ("Settings", MANAGE_SETTINGS),
        ]

        for item_text, permission in nav_items:
            if SessionManager.has_permission(permission):
                QListWidgetItem(item_text, self.nav_list)

        # Set default selection if list is not empty
        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)

    def show_main_interface(self):
        """Show the main application interface after successful login."""
        # Setup navigation based on role (now that user is logged in)
        self.setup_navigation()

        # Create the main splitter layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.nav_list)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(splitter)

        self.setCentralWidget(container)
        # Get username safely
        current_user = SessionManager.get_current_user()
        username = current_user.username if current_user else "Unknown"
        self.setWindowTitle(f"Business Management Tool - {username}")