import logging

from gixi.client.logs.log_widget import QtLogWidgetHolder


class QtLogHandler(logging.Handler):
    @staticmethod
    def append_log(log: str):
        level, *message = log.split()
        message = _set_html_color(' '.join(message), level)
        QtLogWidgetHolder().log(message)

    def emit(self, record):
        self.append_log(self.format(record))


def process_server_logs(lines):
    html = []
    for line in lines:
        level, *message = line.split()
        html.append(_set_html_color(' '.join(message), level))
    return '\n'.join(html)


_LOG_COLOR_DICT = dict(DEBUG='green', INFO='black', WARNING='yellow', ERROR='red')


def _set_html_color(message, level):
    return f'<font color="{_LOG_COLOR_DICT.get(level, "black")}"> {message}'
