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
    pyqtSignal
)

from .tools import get_folder_filepath


class FileViewer(QMainWindow):
    sigImageFileClicked = pyqtSignal(str)
    sigH5FileClicked = pyqtSignal(str)

    def __init__(self, base_path: str, parent=None):
        super().__init__(parent)

        self.file_widget = FileViewWidget(base_path, parent)
        self.file_widget.sigImageFileClicked.connect(self.sigImageFileClicked)
        self.file_widget.sigH5FileClicked.connect(self.sigH5FileClicked)

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
        update_toolbar.addAction('Update', self.file_widget.update_files)
        update_toolbar.addAction('Change dir', self.change_base_path)


class FileViewWidget(QWidget):
    sigImageFileClicked = pyqtSignal(str)
    sigH5FileClicked = pyqtSignal(str)
    sigCifFileClicked = pyqtSignal(str)

    def __init__(self, base_path: str, parent=None):
        super().__init__(parent=parent)
        self.base_path = base_path
        self.log = logging.getLogger(__name__)
        self._init_ui()
        self._connect_ui()

        self.tree.setRootIndex(self.model.setRootPath(base_path))

    def set_base_path(self, base_path: str):
        self.base_path = base_path
        self.update_files()

    def update_files(self):
        self.tree.setRootIndex(self.model.setRootPath(''))
        self.tree.setRootIndex(self.model.setRootPath(self.base_path))

    def _init_ui(self):
        self.model = QFileSystemModel()

        self.tree = QTreeView(self)
        self.tree.setUniformRowHeights(True)
        self.tree.setModel(self.model)

        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)

        self.tree.setWindowTitle("Files")
        self.tree.resize(640, 480)

        window_layout = QVBoxLayout()
        window_layout.addWidget(self.tree)

        self.setLayout(window_layout)

    def _connect_ui(self):
        self.tree.selectionModel().currentChanged.connect(self._on_clicked)
        self.tree.doubleClicked.connect(self._on_double_clicked)

    def _on_double_clicked(self, index):
        path = self.model.filePath(index)

        if path and Path(path).is_file() and path.endswith('.h5'):
            self.sigH5FileClicked.emit(path)

    def _on_clicked(self, index):
        path = self.model.filePath(index)

        if path and Path(path).is_file() and path.endswith('.tif'):
            self.log.info(f'{path} clicked.')
            self.sigImageFileClicked.emit(path)

        if path and Path(path).is_file() and path.endswith('.cif'):
            self.log.info(f'{path} clicked.')
            self.sigCifFileClicked.emit(path)
