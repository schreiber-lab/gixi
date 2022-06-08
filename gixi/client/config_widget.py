# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Type
import logging

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QSplitter, QMessageBox
from PyQt5.QtGui import QCloseEvent

from pyqtgraph.parametertree import Parameter, ParameterTree

from gixi.server.app_config import AppConfig, JobConfig
from gixi.server.config import Config

from gixi.client.tools import center_widget
from gixi.client.config_list import ConfigList


class ConfigParamTree(ParameterTree):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        param_children = [
            _get_config_params(conf_type.CONF_NAME, conf_type) for conf_type in AppConfig.GUI_CONFIG_GROUPS.values()
        ]

        self.param = Parameter.create(name='params', type='group', children=param_children)
        self.setParameters(self.param, showTop=False)

    def get_config(self, conf_name: str) -> Config:
        idx = list(AppConfig.GUI_CONFIG_GROUPS.keys()).index(conf_name)
        conf_type = AppConfig.GUI_CONFIG_GROUPS[conf_name]
        conf_dict = {p.name(): p.value() for p in self.param.children()[idx].children()}
        return conf_type(**conf_dict)

    @property
    def job_conf_dict(self) -> JobConfig:
        return self.get_config('job_config')

    @property
    def app_config(self) -> AppConfig:
        return AppConfig(
            **{name: self.get_config(name) for name in AppConfig.GUI_CONFIG_GROUPS.keys()}
        )

    def set_config(self, app_config: AppConfig):
        param_children = [
            _get_config_params(AppConfig.GUI_CONFIG_GROUPS[name].CONF_NAME, getattr(app_config, name))
            for name in AppConfig.GUI_CONFIG_GROUPS.keys()
        ]

        self.param = Parameter.create(name='params', type='group', children=param_children)
        self.setParameters(self.param, showTop=False)


class ConfigWidget(QWidget):
    sigSubmitJobClicked = pyqtSignal(AppConfig)
    sigCurrentConfigUpdated = pyqtSignal(AppConfig)

    def __init__(self, current_config: AppConfig, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        self.setWindowFlag(Qt.Window, True)
        self.setWindowModality(Qt.WindowModal)
        self.setGeometry(0, 0, 1200, 500)
        center_widget(self)

        self.setWindowTitle('Configuration')

        self.parameter_tree = ConfigParamTree(self)
        self.config_list = ConfigList(current_config, self)
        self.submit_btn = QPushButton('Submit job', self)
        self.update_current_config = QPushButton('Update current config', self)
        self.save_config = QPushButton('Save config', self)
        self.load_config = QPushButton('Load config', self)
        self.cancel_btn = QPushButton('Cancel', self)
        self._init_ui()
        self._connect()

    def _connect(self):
        self.submit_btn.clicked.connect(self._on_submit_clicked)
        self.update_current_config.clicked.connect(self._update_current_config)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.save_config.clicked.connect(self._save_config)
        self.load_config.clicked.connect(self._load_config)
        self.config_list.sigConfigSelectedSignal.connect(self.set_config)

    @pyqtSlot()
    def _update_current_config(self):
        current_config = self.current_config
        self.config_list.update_current_config(current_config)
        self.config_list.select_current_config()
        self.sigCurrentConfigUpdated.emit(current_config)

    @pyqtSlot()
    def _on_cancel_clicked(self):
        self._ask_before_close()
        self.hide()

    @pyqtSlot()
    def _on_submit_clicked(self):
        config = self._save_config()
        self.logger.info('Submit job')
        self.sigSubmitJobClicked.emit(config)

        self._ask_before_close()
        self.hide()

    @pyqtSlot()
    def _save_config(self):
        config = self.parameter_tree.app_config
        path = Path(config.job_config.config_path)
        self.logger.info(f'Saving new config to {str(path)}')
        config.save_to_config(path)
        self.logger.info(f'Config is saved to {str(path)}')
        self.config_list.update_paths()
        return config

    @pyqtSlot(AppConfig)
    def set_config(self, config: AppConfig):
        self.parameter_tree.set_config(config)

    @property
    def current_config(self) -> AppConfig:
        return self.parameter_tree.app_config

    @pyqtSlot()
    def _load_config(self):
        config = self.parameter_tree.app_config
        path = config.job_config.config_path
        config = AppConfig.from_config(path, config)
        self.set_config(config)
        self.logger.info(f'Config is loaded from {str(path)}')

    def _init_ui(self):
        layout = QGridLayout(self)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.parameter_tree)
        splitter.addWidget(self.config_list)

        layout.addWidget(splitter, 0, 0, 1, 2)
        layout.addWidget(self.update_current_config, 1, 0)
        layout.addWidget(self.cancel_btn, 1, 1)
        layout.addWidget(self.save_config, 2, 0)
        layout.addWidget(self.load_config, 2, 1)
        layout.addWidget(self.submit_btn, 3, 0, 1, 2)

    def _ask_before_close(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)

        msg.setText("Do you want to update the configuration?")
        msg.setWindowTitle("Close configuration")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        res = msg.exec_()

        if res == QMessageBox.Yes:
            self._update_current_config()
        elif res == QMessageBox.No:
            current_config = self.config_list.current_config
            self.set_config(current_config)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self._ask_before_close()
        super().closeEvent(a0)


def _get_config_params(name: str, config: Config or Type[Config]):
    children_params = [
        {
            'name': name,
            'type': _type_str(t),
            'title': config.PARAM_DESCRIPTIONS[name],
            'value': getattr(config, name, None)
        }
        for name, t in config.__annotations__.items()
        if name in config.PARAM_DESCRIPTIONS
    ]

    params = {'name': name, 'type': 'group', 'children': children_params}

    return params


def _type_str(t: type):
    return str(t).split("'")[1]
