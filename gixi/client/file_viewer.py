import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QFileSystemModel,
    QTreeView,
    QWidget,
    QMainWindow,
    QVBoxLayout
)
from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot,
)

from gixi.client.tools import get_folder_filepath

from pathlib import Path
import os
from datetime import datetime as dt

from PyQt5.QtWidgets import (
    QTreeView,
    QMenu,
    QShortcut,
)
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QKeySequence
from PyQt5.QtCore import Qt

from gixi.client.tools import Icon


class FileViewer(QMainWindow):
    sigImageFileClicked = pyqtSignal(str)
    sigGixiFileClicked = pyqtSignal(str)
    sigH5FileClicked = pyqtSignal(str)

    def __init__(self, base_path: str, parent=None):
        super().__init__(parent)

        self.file_widget = FileTree(base_path, parent)
        self.file_widget.sigImageFileClicked.connect(self.sigImageFileClicked)
        self.file_widget.sigH5FileClicked.connect(self.sigH5FileClicked)
        self.file_widget.sigGixiFileClicked.connect(self.sigGixiFileClicked)

        self.setCentralWidget(self.file_widget)
        self.setWindowTitle('File View')

        self._init_toolbars()

    def change_base_path(self):
        path = get_folder_filepath(self, 'Choose a directory')
        if path:
            self.set_base_path(str(path.absolute()))

    def set_base_path(self, base_path: str):
        self.file_widget.set_base_path(base_path)

    def _init_toolbars(self):
        update_toolbar = self.addToolBar('Update')
        update_toolbar.addAction('Update', self.file_widget.update_selected_folder)
        update_toolbar.addAction('Change dir', self.change_base_path)


class FileTree(QTreeView):
    sigImageFileClicked = pyqtSignal(str)
    sigH5FileClicked = pyqtSignal(str)
    sigCifFileClicked = pyqtSignal(str)
    sigGixiFileClicked = pyqtSignal(str)

    def __init__(self, base_path: str or Path, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger(__name__)
        self._model = FileModel(Path(base_path))
        self.setModel(self._model)
        self.setEditTriggers(QTreeView.NoEditTriggers)

        self.setSelectionMode(self.SingleSelection)
        self.selectionModel().currentChanged.connect(self._on_clicked)

        self.setUniformRowHeights(True)
        self.setAnimated(False)
        self.setIndentation(20)

        self.customContextMenuRequested.connect(self._context_menu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.header().setSectionsClickable(True)
        self.header().setSortIndicatorShown(True)
        self.header().sortIndicatorChanged.connect(self._model.sort)

        self._init_shortcuts()
        self.show()

    def _init_shortcuts(self):
        self.update_folder_shortcut = QShortcut(QKeySequence.Refresh, self)
        self.update_folder_shortcut.activated.connect(lambda *x: self.update_selected_folder())

    def set_base_path(self, path):
        path = Path(path)
        self._model.update_root(path)

    def update_selected_folder(self):
        indices = self.selectionModel().selectedIndexes()
        if not indices:
            return
        index = indices[0]
        item = self._model.itemFromIndex(index)

        if isinstance(item, FileItem):
            item = item.parent()
        if isinstance(item, FolderItem):
            item.update()

    def _on_clicked(self, index):
        item = self._model.item_from_index(index)

        if isinstance(item, FileItem):
            self._on_file_clicked(item)
        elif isinstance(item, FolderItem):
            item.on_clicked()
            self.setExpanded(item.index(), True)

    def _on_file_clicked(self, item: 'FileItem'):
        path = item.path

        if not path.is_file():
            return

        if path.suffix == '.tif':
            self.log.debug(f'{path} clicked.')
            self.sigImageFileClicked.emit(str(path))
            return

        if path.suffix == '.gixi':
            self.log.debug(f'{path} clicked.')
            self.sigGixiFileClicked.emit(str(path))
            return

    def _context_menu(self, position):
        item = self._model.itemFromIndex(self.indexAt(position))

        if not isinstance(item, FolderItem):
            return

        menu = QMenu()
        update_folder = menu.addAction('Update folder')
        update_folder.triggered.connect(item.update)

        menu.exec_(self.viewport().mapToGlobal(position))


class FileModel(QStandardItemModel):
    def __init__(self, root_path: Path = None):
        super().__init__()
        self.setHorizontalHeaderLabels(['Name', 'Type', 'Size', 'Date Modified'])
        self.base_path = root_path or Path.home()
        self.update_root(self.base_path)

    def update_root(self, root_path: Path):
        self.base_path = root_path
        for row in reversed(range(self.rowCount())):
            self.removeRow(row)
        self.appendRow(_get_item_row(self.base_path))

    def on_click(self, row: int):
        if self.paths[row][2]:
            return
        item = self.item(row, 0)

        if isinstance(item, FolderItem):
            item.update()

    def item_from_index(self, index):
        item = self.itemFromIndex(index)
        if not item:
            return
        parent = item.parent()
        if parent:
            return parent.child(item.row(), 0)
        else:
            return self.item(item.row(), 0)


def _get_item_row(path: Path):
    if path.is_dir():
        base_item = FolderItem(path)
    else:
        base_item = FileItem(path)
    item_row = [base_item] + [QStandardItem(txt) for txt in _get_path_row_data(path)]
    return item_row


class FileItem(QStandardItem):
    def __init__(self, path: Path):
        super().__init__(path.name)
        self.path = path


class FolderItem(QStandardItem):
    def __init__(self, path: Path):
        super().__init__(path.name)
        self.path = path
        self.setIcon(Icon('folder'))
        self._updated: bool = False

    def on_clicked(self):
        if not self._updated:
            self.update()
        self._updated = True

    def _fill(self):
        paths = sorted(list(self.path.glob('*')))
        for path in paths:
            self.appendRow(_get_item_row(path))

    def update(self):
        self.clear()
        self._fill()

    def clear(self):
        self.removeRows(0, self.rowCount())


def _get_path_row_data(path: Path):
    if path.is_dir():
        return ['File Folder', '', _get_path_mtime(path)]
    return [_get_file_type(path), _get_file_size(path), _get_path_mtime(path)]


def _get_path_mtime(path: Path) -> str:
    return dt.fromtimestamp(os.path.getmtime(path)).strftime('%d/%m/%y %H:%M')


def _get_file_size(path: Path) -> str:
    byte_size = os.path.getsize(path)
    return get_size_str(byte_size)


def get_size_str(n_bytes):
    if n_bytes >= 1000 ** 3:
        size_str = f'{round(n_bytes / 1000 ** 3, 2)} Gb'
    elif n_bytes >= 1000 ** 2:
        size_str = f'{round(n_bytes / 1000 ** 2)} Mb'
    elif n_bytes >= 1000:
        size_str = f'{round(n_bytes / 1000)} Kb'
    else:
        size_str = f'{round(n_bytes / 1000)} bytes'
    return size_str


def _get_file_type(path: Path):
    return path.suffix[1:] + ' File'
