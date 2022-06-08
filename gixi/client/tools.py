import logging
from pathlib import Path

from PyQt5.QtWidgets import (QGraphicsColorizeEffect, QLineEdit,
                             QWidget, QApplication, QMessageBox,
                             QFileDialog)
from PyQt5.QtCore import QPropertyAnimation, Qt
from PyQt5.QtGui import QColor, QPen, QIcon

GLOB_IMAGE_FORMATS = 'tif files (*.tiff *.tif)'
H5_FORMATS = 'h5 files (*.h5 *.hdf5)'

logger = logging.getLogger(__name__)

ICON_PATH: Path = Path(__file__).parents[2] / 'static' / 'icons'


class SingletonMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Icon(QIcon):
    def __init__(self, name: str):
        if name.find('.') == -1:
            name += '.png'
        name = str(ICON_PATH / name)
        QIcon.__init__(self, name)


class DummySignal(object):
    def __init__(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass

    def emit(self, *args, **kwargs):
        pass

    def disconnect(self, *args, **kwargs):
        pass


def save_file_dialog(parent, title: str = 'Save File', file_format: str = 'H5 file (*.h5)',
                     *, exists: bool = False, directory: str = '') -> Path or None:
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog

    if exists:
        filename, _ = QFileDialog.getOpenFileName(parent, title, directory, file_format, options=options)
    else:
        filename, _ = QFileDialog.getSaveFileName(parent, title, directory, file_format, options=options)

    if filename:
        return Path(filename)


def get_filepath_dialog(parent, message: str, formats: str):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    filepath, _ = QFileDialog.getOpenFileName(
        parent, message, '',
        formats, options=options)
    if filepath:
        return Path(filepath)


def show_error(err: str, *, error_title: str = 'Internal Error', info_text: str = ''):
    logger.info(f'Error message shown: {error_title} - {err} {info_text}.')

    mb = QMessageBox()
    mb.setIcon(QMessageBox.Critical)
    mb.setWindowTitle(error_title)
    mb.setText(err)
    if info_text:
        mb.setInformativeText(info_text)
    mb.exec_()


def get_image_filepath(parent, message: str = 'Open image') -> Path or None:
    return get_filepath_dialog(parent, message, GLOB_IMAGE_FORMATS)


def get_h5_filepath(parent, message: str = 'Choose h5 file') -> Path or None:
    return get_filepath_dialog(parent, message, H5_FORMATS)


def get_folder_filepath(parent, message: str, *, show_files: bool = True,
                        directory: str = '', exists: bool = True) -> Path or None:
    options = QFileDialog.DontResolveSymlinks | QFileDialog.DontUseNativeDialog
    if not show_files:
        options |= QFileDialog.ShowDirsOnly

    dialog = QFileDialog(parent, caption=message, directory=directory)
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOptions(options)

    if not exists:
        dialog.setAcceptMode(QFileDialog.AcceptSave)

    if dialog.exec_() == QFileDialog.Accepted:
        folder_path = dialog.selectedFiles()[0]

        if folder_path:
            return Path(folder_path)


def get_pen(width: int = 1, color: str or QColor = 'white', style=Qt.SolidLine) -> QPen:
    if isinstance(color, str):
        color = QColor(color)
    pen = QPen(color)
    pen.setStyle(style)
    pen.setWidth(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    pen.setCosmetic(True)
    return pen


def center_widget(widget):
    frame_gm = widget.frameGeometry()
    screen = QApplication.desktop().screenNumber(
        QApplication.desktop().cursor().pos())
    center_point = QApplication.desktop().screenGeometry(
        screen).center()
    frame_gm.moveCenter(center_point)
    widget.move(frame_gm.topLeft())


def validate_scientific_value(q_line_edit: QLineEdit,
                              data_type: type or None = float,
                              empty_possible: bool = False,
                              additional_conditions: tuple = ()):
    text_value = q_line_edit.text().replace(',', '.')
    if data_type is None:
        return text_value
    try:
        value = data_type(text_value)
    except ValueError:
        if not empty_possible:
            color_animation(q_line_edit)
        return
    for condition in additional_conditions:
        if not condition(value):
            return
    return value


def color_animation(widget: QWidget, color=Qt.red):
    effect = QGraphicsColorizeEffect(widget)
    widget.setGraphicsEffect(effect)

    widget.animation = QPropertyAnimation(effect, b'color')

    widget.animation.setStartValue(QColor(color))
    widget.animation.setEndValue(QColor(Qt.black))

    widget.animation.setLoopCount(1)
    widget.animation.setDuration(1500)
    widget.animation.start()
