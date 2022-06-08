import logging
from pathlib import Path

from PyQt5.QtWidgets import QMenu, QTreeView, QMainWindow, QShortcut
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QItemSelectionModel

import numpy as np

from gixi.client.h5utils import H5FileManager, H5Items

from gixi.client.tools import get_h5_filepath


class H5Model(QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)


class GroupItem(QStandardItem):
    def __init__(self, group_name: str, file_manager: H5FileManager):
        name = group_name.split('/')[-1]
        super().__init__(name)
        self.group_name = group_name
        self.file_manager = file_manager
        self._updated: bool = False

    @property
    def item_type(self) -> H5Items:
        return H5Items.group

    def on_clicked(self):
        if self._updated:
            return
        self.update_item()

    @property
    def is_updated(self) -> bool:
        return self._updated

    def get_child_by_name(self, group_name: str) -> 'GroupItem' or None:
        for row in range(self.rowCount()):
            item = self.child(row)
            if item.group_name == group_name:
                return item

    def update_item(self):
        new_group_names = self.file_manager.parse_group(self.group_name)

        if not new_group_names:
            return

        self._updated = True
        self.remote_children()
        self.appendRows(
            list(
                filter(
                    lambda x: bool(x),
                    [
                        get_item(group_name, self.file_manager)
                        for group_name in new_group_names]
                )
            )
        )

    def remote_children(self):
        if self.rowCount():
            self.removeRows(0, self.rowCount())


class ImageItem(GroupItem):
    @property
    def item_type(self) -> H5Items:
        return H5Items.image_dataset

    def update_item(self):
        pass


class DatasetItem(ImageItem):
    @property
    def item_type(self) -> H5Items:
        return H5Items.dataset

    def read_dataset(self) -> np.ndarray or None:
        return self.file_manager.read_dataset(self.group_name)


class FileItem(GroupItem):
    def __init__(self, file_manager: H5FileManager):
        super().__init__(file_manager.name, file_manager)
        self.group_name = '/'


def get_item(group_name: str, file_manager: H5FileManager) -> GroupItem or None:
    item_type = file_manager.get_key_type(group_name)
    if item_type == H5Items.not_exist:
        return
    if item_type == H5Items.dataset:
        return DatasetItem(group_name, file_manager)
    if item_type == H5Items.image_dataset:
        return ImageItem(group_name, file_manager)
    return GroupItem(group_name, file_manager)


class H5FileViewerWidget(QTreeView):
    sigImageDatasetClicked = pyqtSignal(dict)
    sigDatasetClicked = pyqtSignal(object)

    def __init__(self, parent=None, file_manager: H5FileManager = None):
        super().__init__(parent)
        self.log = logging.getLogger(__name__)
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setEditTriggers(QTreeView.NoEditTriggers)

        self.selectionModel().currentChanged.connect(self._on_clicked)
        self.customContextMenuRequested.connect(self._context_menu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_manager = None

        if file_manager:
            self.set_file(file_manager)

        self.update_shortcut = QShortcut(QKeySequence("F5"), self)
        self.update_shortcut.activated.connect(self._update_item)

        self.show()

    @pyqtSlot()
    def _update_item(self):
        try:
            index = self.selectionModel().currentIndex()
            item = self._model.itemFromIndex(index)
            if item.item_type == H5Items.group:
                item.update_item()
            elif item.item_type in (H5Items.dataset, H5Items.image_dataset):
                row = item.row()
                parent = item.parent()
                parent.update_item()
                self.selectionModel().setCurrentIndex(
                    parent.child(row).index(),
                    QItemSelectionModel.ClearAndSelect
                )
        except Exception as err:
            self.log.exception(err)

    def set_file(self, file_manager: H5FileManager):
        self._model.clear()
        self._model.appendRow(FileItem(file_manager))
        self.file_manager = file_manager

    def update_file(self):
        try:
            self._model.item(0, 0).update_item()
        except:
            pass

    def _on_clicked(self, index):
        item = self._model.itemFromIndex(index)
        try:
            item.on_clicked()
            if item.item_type == H5Items.image_dataset:
                data = self.file_manager.read(item.group_name)
                if data:
                    self.sigImageDatasetClicked.emit(data)
            elif item.item_type == H5Items.group:
                self.setExpanded(item.index(), True)
            elif item.item_type == H5Items.dataset:
                data = item.read_dataset()
                if data is not None:
                    self.sigDatasetClicked.emit(data)
        except AttributeError:
            pass

    def _context_menu(self, position):
        item = self._model.itemFromIndex(self.indexAt(position))
        if not hasattr(item, 'item_type'):
            return
        menu = QMenu()
        if item.item_type == H5Items.group:
            update_folder = menu.addAction('Update')
            update_folder.triggered.connect(item.update_item)

        menu.exec_(self.viewport().mapToGlobal(position))


class H5Viewer(QMainWindow):
    sigImageDatasetClicked = pyqtSignal(dict)
    sigDatasetClicked = pyqtSignal(object)

    def __init__(self, file_manager: H5FileManager = None, parent=None):
        super().__init__(parent)
        self.h5_widget = H5FileViewerWidget(self, file_manager)
        self.setCentralWidget(self.h5_widget)

        self.setWindowTitle('H5 File View')

        self._init_toolbars()

        self.h5_widget.sigImageDatasetClicked.connect(self.sigImageDatasetClicked)
        self.h5_widget.sigDatasetClicked.connect(self.sigDatasetClicked)

    def change_h5_path(self):
        path = get_h5_filepath(self, 'Choose an h5 file')
        if path:
            self.set_h5_path(path)

    def set_h5_path(self, path: Path or str):
        if not isinstance(path, Path):
            path = Path(path)
        if not path.is_file():
            return
        self.h5_widget.set_file(H5FileManager(path))

    def _init_toolbars(self):
        update_toolbar = self.addToolBar('Update')
        update_toolbar.addAction('Update', self.h5_widget.update_file)
        update_toolbar.addAction('Change file', self.change_h5_path)
