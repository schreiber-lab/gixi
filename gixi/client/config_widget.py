# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Type

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton

from pyqtgraph.parametertree import Parameter, ParameterTree


from ..server.app_config import AppConfig, JobConfig
from ..server.config import Config

from .tools import center_widget


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.Window, True)
        self.setWindowModality(Qt.WindowModal)
        self.setGeometry(0, 0, 1200, 500)
        center_widget(self)

        self.parameter_tree = ConfigParamTree(self)
        self.submit_btn = QPushButton('Submit job', self)
        self.save_config = QPushButton('Save config', self)
        self.load_config = QPushButton('Load config', self)
        self.cancel_btn = QPushButton('Cancel', self)
        self._init_ui()
        self._connect()

    def _connect(self):
        self.submit_btn.clicked.connect(self._on_submit_clicked)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.save_config.clicked.connect(self._save_config)
        self.load_config.clicked.connect(self._load_config)

    @pyqtSlot()
    def _on_cancel_clicked(self):
        self.hide()

    @pyqtSlot()
    def _on_submit_clicked(self):
        config = self._save_config()
        self.sigSubmitJobClicked.emit(config)
        self.hide()

    @pyqtSlot()
    def _save_config(self):
        config = self.parameter_tree.app_config
        path = Path(config.job_config.config_path)
        config.save_to_config(path)
        return config

    @pyqtSlot()
    def _load_config(self):
        config = self.parameter_tree.app_config
        path = config.job_config.config_path
        config = AppConfig.from_config(path, config)
        self.parameter_tree.set_config(config)

    def _init_ui(self):
        layout = QGridLayout(self)
        layout.addWidget(self.parameter_tree, 0, 0, 1, 2)
        layout.addWidget(self.submit_btn, 1, 0)
        layout.addWidget(self.cancel_btn, 1, 1)
        layout.addWidget(self.save_config, 2, 0)
        layout.addWidget(self.load_config, 2, 1)


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
