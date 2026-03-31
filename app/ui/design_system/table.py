from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class Column:
    key: str
    title: str
    align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


class SimpleTableModel(QAbstractTableModel):
    def __init__(self, columns: list[Column], rows: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self.columns = columns
        self._rows: list[dict[str, Any]] = rows or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.columns[section].title
        return str(section + 1)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = self.columns[index.column()]

        value = row.get(col.key, "")

        if role == Qt.ItemDataRole.DisplayRole:
            return "" if value is None else str(value)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(col.align)
        return None

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row_index: int) -> dict[str, Any] | None:
        if row_index < 0 or row_index >= len(self._rows):
            return None
        return self._rows[row_index]


class ContainsFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._term = ""

    def set_term(self, term: str) -> None:
        self._term = (term or "").strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if not self._term:
            return True
        model = self.sourceModel()
        if model is None:
            return True
        cols = model.columnCount()
        for c in range(cols):
            idx = model.index(source_row, c, source_parent)
            text = str(model.data(idx, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self._term in text:
                return True
        return False


class TableView(QWidget):
    """Enterprise table: filter + sortable columns (pagination hook-ready)."""

    def __init__(self, columns: list[Column], parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter…")
        self.search.setClearButtonEnabled(True)

        self.count_label = QLabel("0 rows")

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Reload data")

        top = QHBoxLayout()
        top.addWidget(self.search, 1)
        top.addWidget(self.count_label)
        top.addWidget(self.refresh_btn)

        self.table = QTableView()
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.model = SimpleTableModel(columns, rows=[])
        self.proxy = ContainsFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.table.setModel(self.proxy)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)

        self.search.textChanged.connect(self._on_filter_changed)

    def _on_filter_changed(self, text: str) -> None:
        self.proxy.set_term(text)
        self._update_count()

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self.model.set_rows(rows)
        self._update_count()
        self.table.resizeColumnsToContents()

    def _update_count(self) -> None:
        self.count_label.setText(f"{self.proxy.rowCount()} rows")

    def selected_row(self) -> dict[str, Any] | None:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        src_idx = self.proxy.mapToSource(idx)
        return self.model.row_at(src_idx.row())

