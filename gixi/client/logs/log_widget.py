from PyQt5.QtWidgets import QPlainTextEdit

from gixi.client.tools import SingletonMeta

__all__ = [
    'QtLogWidgetHolder',
]


class QtLogWidgetHolder(metaclass=SingletonMeta):
    def __init__(self, parent=None):
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def log(self, log: str):
        self.widget.appendHtml(log)
