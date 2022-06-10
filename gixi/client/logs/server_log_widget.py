import logging

from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QPushButton, QGridLayout
from PyQt5.QtCore import pyqtSlot

from gixi.server.app_config import AppConfig
from gixi.client.logs.log_handler import process_server_logs

__all__ = [
    'ServerLogWidget',
]


class ServerLogWidget(QWidget):
    def __init__(self, config: AppConfig = None, parent=None, use_html: bool = False):
        super().__init__(parent)
        self._use_html = use_html
        self._config = config or AppConfig()

        self.log = logging.getLogger(__name__)
        self._init_ui()
        self._connect()

    def _init_ui(self):
        self.widget = QPlainTextEdit(self)
        self.widget.setReadOnly(True)

        self.update_btn = QPushButton('Update logs')
        self.clear_btn = QPushButton('Clear')

        layout = QGridLayout(self)
        layout.addWidget(self.update_btn, 0, 0)
        layout.addWidget(self.clear_btn, 0, 1)
        layout.addWidget(self.widget, 1, 0, 2, 2)

    def _connect(self):
        self.update_btn.clicked.connect(self.update_log)
        self.clear_btn.clicked.connect(self.widget.clear)

    @pyqtSlot()
    def update_log(self):
        self.widget.clear()
        log = self.get_log()

        if not log:
            return

        if self._use_html:
            self.widget.appendHtml(log)
        else:
            self.widget.appendPlainText(log)

    def get_log(self) -> str:
        path = self._config.log_filename
        if not path:
            return ''

        try:
            with open(str(path), 'r') as f:
                if self._use_html:
                    html = process_server_logs(f)
                else:
                    return f.read()
            return html
        except FileNotFoundError:
            return ''
        except Exception as err:
            self.log.exception(err)
            return ''

    @pyqtSlot(AppConfig)
    def set_config(self, config: AppConfig):
        self._config = config
        self.update_log()
