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
from app.ui.screens.inventory_screen import InventoryScreen
from app.ui.screens.pos_screen import POSScreen
from app.ui.screens.products_screen import ProductsScreen
from app.ui.screens.settings_screen import SettingsScreen


class AppWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Business Management Tool")
        self.resize(1280, 760)

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(220)
        for item in ["Dashboard", "Products", "Categories", "Inventory", "Sales", "Settings"]:
            QListWidgetItem(item, self.nav_list)

        self.stack = QStackedWidget()
        self.stack.addWidget(DashboardScreen())
        self.stack.addWidget(ProductsScreen())
        self.stack.addWidget(CategoriesScreen())
        self.stack.addWidget(InventoryScreen())
        self.stack.addWidget(POSScreen())
        self.stack.addWidget(SettingsScreen())

        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.nav_list)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(splitter)

        self.setCentralWidget(container)