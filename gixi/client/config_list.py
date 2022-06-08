from pathlib import Path
import logging

from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from gixi.client.tools import show_error
from gixi.server.config import CONFIG_FOLDER
from gixi.server.app_config import AppConfig


class ConfigItem(QListWidgetItem):
    def __init__(self, path: Path = None, config: AppConfig = None, parent: QListWidget = None):
        assert config or path

        if not path:
            name = 'Current config'
        else:
            name = path.name

        self._name = name

        super().__init__(name, parent)

        self.path = path
        self._config = config

    def set_config(self, config: AppConfig):
        self._config = config

    def get_config(self) -> AppConfig:
        if self._config:
            return self._config
        try:
            self._config = AppConfig.from_config(str(self.path))
            return self._config
        except Exception as err:
            show_error(
                f'Could not open configuration file {self.path}',
                error_title='Configuration file error'
            )
            logging.getLogger(__name__).exception(err)
            self.listWidget().takeItem(self.listWidget().row(self))


class ConfigList(QListWidget):
    sigConfigSelectedSignal = pyqtSignal(AppConfig)

    def __init__(self, current_config: AppConfig, parent=None):
        super().__init__(parent)

        self._current_item = ConfigItem(config=current_config)
        self.addItem(self._current_item)
        self.update_paths()
        self.selectionModel().currentChanged.connect(self._on_clicked)

    @property
    def current_config(self) -> AppConfig:
        return self._current_item.get_config()

    def _on_clicked(self, index):
        item: ConfigItem = self.itemFromIndex(index)
        selected_config: AppConfig = item.get_config()
        if selected_config:
            self.sigConfigSelectedSignal.emit(selected_config)

    @pyqtSlot(AppConfig)
    def update_current_config(self, config: AppConfig):
        self._current_item.set_config(config)
        self.select_current_config()

    @pyqtSlot()
    def select_current_config(self):
        self._deselect_all()
        self._select()

    def _deselect_all(self):
        for index in self.selectionModel().selectedIndexes():
            self.selectionModel().select(index, self.selectionModel().Deselect)

    def _select(self, item: ConfigItem = None):
        item = item or self._current_item
        self.selectionModel().select(self.indexFromItem(item), self.selectionModel().Select)

    @pyqtSlot()
    def update_paths(self) -> None:
        self.clear_paths()

        for path in self.get_config_paths():
            self.addItem(ConfigItem(path))

    @pyqtSlot()
    def clear_paths(self) -> None:
        for row in reversed(range(1, self.count())):
            self.takeItem(row)

    @staticmethod
    def get_config_paths():
        return sorted(list(CONFIG_FOLDER.glob('*.yaml')))

# class ConfigListWidget(QWidget):
#     def __init__(self, parent=None):
#         super().__init__()
