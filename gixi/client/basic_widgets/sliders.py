# -*- coding: utf-8 -*-
import logging

from PyQt5.QtWidgets import (QSlider, QLineEdit, QHBoxLayout,
                             QLabel,
                             QSizePolicy, QWidget)
from PyQt5.QtGui import QPainter, QPainterPath, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRectF

import numpy as np


from gixi.client.tools import color_animation

logger = logging.getLogger(__name__)


class DoubleSlider(QSlider):
    valueChangedByHand = pyqtSignal(float)
    _MAX_INT = int(1e9)

    def __init__(self, orientation=Qt.Horizontal, parent=None, decimals: int = 5,
                 value: float = 0, bounds: tuple = (0, 1), log_scale: bool = False):
        super().__init__(orientation=orientation, parent=parent)
        self.decimals: int = decimals
        self._pressed: bool = False
        self._log_scale: bool = log_scale
        self.sliderPressed.connect(self._set_pressed)
        self.sliderReleased.connect(self._set_released)
        self.sliderReleased.connect(self.emit_value)
        self.valueChanged.connect(self._check_and_emit)

        super().setMinimum(0)
        super().setMaximum(self._MAX_INT)

        self._min_value = bounds[0]
        self._max_value = bounds[1]
        if self._log_scale and bounds[0] <= 0:
            raise ValueError(f'Wrong minimal bound for log scale: {bounds[0]}')
        self.setValue(value)

    def emit_value(self, *args):
        self.valueChangedByHand.emit(self.value())

    def _set_pressed(self, *args):
        self._pressed = True

    def _set_released(self, *args):
        self._pressed = False

    def _check_and_emit(self, *args):
        if self._pressed:
            self.emit_value()

    def set_decimals(self, decimals):
        self.decimals = decimals

    @property
    def _value_range(self):
        return self._max_value - self._min_value

    def _real_to_view(self, value):
        try:
            if self._log_scale:
                return int((np.log10(value) - np.log10(self._min_value)) /
                           (np.log10(self._max_value) - np.log10(self._min_value)) * self._MAX_INT)
            else:
                return int((value - self._min_value) / self._value_range * self._MAX_INT)
        except ZeroDivisionError:
            return 0

    def _view_to_real(self, value):
        if self._log_scale:
            return 10 ** (value / self._MAX_INT * (np.log10(self._max_value) - np.log10(self._min_value)) +
                          np.log10(self._min_value))
        else:
            return value / self._MAX_INT * self._value_range + self._min_value

    def value(self):
        return self._view_to_real(super().value())

    def setValue(self, value):
        super().setValue(self._real_to_view(value))

    def setMinimum(self, value):
        if value > self._max_value:
            raise ValueError("Minimum limit cannot be higher than maximum")
        if self._log_scale and value <= 0:
            raise ValueError(f'Wrong minimal bound for log scale: {value}')
        real_value = self.value()
        self._min_value = value
        self.setValue(real_value)
        if real_value < value:
            self.emit_value()

    def setMaximum(self, value):
        if value < self._min_value:
            raise ValueError("Minimum limit cannot be higher than maximum")

        real_value = self.value()
        self._max_value = value
        self.setValue(real_value)
        if real_value > value:
            self.emit_value()

    def setRange(self, p_int, p_int_1):
        real_value = self.value()
        self._min_value = p_int
        self._max_value = p_int_1
        if self._log_scale and p_int <= 0:
            raise ValueError(f'Wrong minimal bound for log scale: {p_int}')
        self.setValue(real_value)

    def minimum(self):
        return self._min_value

    def maximum(self):
        return self._max_value


class LabeledSlider(QWidget):
    valueChanged = pyqtSignal(float)

    _HEIGHT = 50
    _WIDTH_MIN = 200
    _WIDTH_MAX = 300

    def __init__(self, name: str, bounds: tuple = (0, 1),
                 value: float = 0,
                 parent=None, orientation=Qt.Horizontal, decimals: int = 3, scientific: bool = False,
                 log_scale: bool = False):
        super().__init__(parent=parent)
        self.name = name
        self._decimals = decimals
        self._scientific: bool = scientific
        self._bounds = bounds
        self.slider = DoubleSlider(orientation, parent, decimals, value, bounds, log_scale=log_scale)
        self.line_edit = QLineEdit(self.get_str_value())
        self.label = QLabel(name)

        self.line_edit.editingFinished.connect(self._set_value_from_text)
        self.line_edit.setStyleSheet('QLineEdit {  border: none; }')

        self.slider.valueChangedByHand.connect(self._set_value_from_slider)

        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.line_edit)

        self.setSizePolicy(
            QSizePolicy.MinimumExpanding,
            QSizePolicy.Fixed
        )

        self.setFixedHeight(self._HEIGHT)
        self.edit_width = self.fontMetrics().width(
            ' '.join([' '] * (self._decimals + 4))) + int(self._scientific) * 50
        self.line_edit.setMaximumWidth(self.edit_width)
        self.setMaximumWidth(self._WIDTH_MAX)

    def sizeHint(self) -> QSize:
        return QSize(self._WIDTH_MIN, self._HEIGHT)

    @property
    def value(self) -> float:
        return self.slider.value()

    def get_str_value(self) -> str:
        if self._decimals:
            return f'{self.slider.value():.{self._decimals}{"e" if self._scientific else "f"}}'
        else:
            return str(int(self.slider.value()))

    def _set_value_from_slider(self):
        self.line_edit.setText(self.get_str_value())
        self.valueChanged.emit(self.slider.value())

    def _set_value_from_text(self):
        value = self.line_edit.text()
        try:
            if self._decimals:
                value = float(value)
            else:
                value = int(value)
            self.slider.setValue(value)
            if value < self._bounds[0] or value > self._bounds[1]:
                raise ValueError()
        except (ValueError, OverflowError):
            self.line_edit.setText(self.get_str_value())
            color_animation(self.line_edit)

        self.valueChanged.emit(self.slider.value())

    def set_value(self, value: float, change_bounds: bool = True):
        if change_bounds and value < self.slider.minimum():
            self.slider.setMinimum(value)

        elif change_bounds and value > self.slider.maximum():
            self.slider.setMaximum(value)

        self.slider.setValue(value)
        self.line_edit.setText(self.get_str_value())


class ParametersSlider(QWidget):
    sigLowerValueChanged = pyqtSignal(float)
    sigMiddleValueChanged = pyqtSignal(float)
    sigUpperValueChanged = pyqtSignal(float)

    _rect_width = 10
    _rect_height = 20
    _padding = 30
    _slider_width = 5

    # _path_color = QColor('black')
    _rect_color = QColor(100, 100, 255)

    def __init__(self, x1=0., x2=0.5, x3=0.1,
                 min_value=0, max_value=1, parent=None):
        super().__init__(parent=parent)

        # self.setMouseTracking(True)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )

        self._pressed: int = 0

        self._min_value = min_value
        self._max_value = max_value

        self._x1 = x1
        self._x2 = x2
        self._x3 = x3

    def setValues(self, x1, x2, x3, *, adjust_range: bool = False, new_range: tuple = None):
        if x1 <= x2 <= x3:
            if adjust_range:
                self._min_value = min(self._min_value, x1)
                self._max_value = max(self._max_value, x3)
            elif new_range:
                self._min_value, self._max_value = new_range
                if self._min_value > self._max_value:
                    raise ValueError(f'Wrong range: {self._min_value} > {self._max_value}')

            if x1 < self._min_value or x3 > self._max_value:
                raise ValueError('Out of range.')

            self._x1 = x1
            self._x2 = x2
            self._x3 = x3

            self.update()

        else:
            raise ValueError(f'Wrong order: {x1}, {x2}, {x3}')

    def sizeHint(self):
        return QSize(300, self._rect_height)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.RightButton:
            ev.ignore()
        else:
            x = ev.pos().x()
            self._pressed = self._get_idx(x)

            if self._pressed:
                ev.accept()
            else:
                ev.ignore()

    def mouseReleaseEvent(self, ev):
        if self._pressed:
            ev.accept()
            self._pressed = 0
        else:
            ev.ignore()

    def mouseMoveEvent(self, ev):
        if not self._pressed:
            # idx = self._get_idx(ev.pos().x())
            # if idx:
            #     print('Hover: ', idx)
            #     ev.accept()
            # else:
            ev.ignore()

        else:
            x = ev.pos().x()
            bounds = self._get_bounds(self._pressed)

            if x < bounds[0]:
                self._set_value(bounds[0])
            elif x > bounds[1]:
                self._set_value(bounds[1])
            else:
                self._set_value(x)

    def _get_idx(self, x):
        w = self._rect_width / 2

        if abs(self._x1_view - x) <= w:
            return 1
        elif abs(self._x2_view - x) <= w:
            return 2
        elif abs(self._x3_view - x) <= w:
            return 3
        else:
            return 0

    def _get_bounds(self, idx: int):
        if not idx:
            return
        w = self._rect_width

        if idx == 1:
            return self._padding, self._x2_view - w
        elif idx == 2:
            return self._x1_view + w, self._x3_view - w
        else:
            return self._x2_view + w, self.width() - self._padding

    def _set_value(self, x):
        idx = self._pressed
        if not idx:
            return

        value = self._scale_from_view(x, idx)

        if idx == 1 and value != self._x1:
            self._x1 = value
            self.sigLowerValueChanged.emit(self._x1)
            self.update()
        elif idx == 2 and value != self._x2:
            self._x2 = value
            self.sigMiddleValueChanged.emit(self._x2)
            self.update()
        elif idx == 3 and value != self._x3:
            self._x3 = value
            self.sigUpperValueChanged.emit(self._x3)
            self.update()

    def paintEvent(self, ev):

        p = QPainter(self)

        self._x1_view = self._scale_to_view(self._x1, 1)
        self._x2_view = self._scale_to_view(self._x2, 2)
        self._x3_view = self._scale_to_view(self._x3, 3)

        p.setRenderHint(QPainter.Antialiasing)

        self._draw_slider(p)
        self._draw_rect(self._x1_view, p)
        self._draw_rect(self._x2_view, p)
        self._draw_rect(self._x3_view, p)

        p.end()

    def _draw_slider(self, p: QPainter):
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(self._padding, self.height() / 2 - self._slider_width / 2,
                   self.width() - self._padding * 2, self._slider_width),
            3, 3)
        # pen = QPen(self._path_color, 2)
        # p.setPen(pen)
        p.fillPath(path, self._rect_color)
        p.drawPath(path)

    def _draw_rect(self, x: float, p: QPainter):
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(x - self._rect_width / 2,
                   self.height() / 2 - self._rect_height / 2,
                   self._rect_width, self._rect_height),
            1, 1)
        # pen = QPen(self._path_color, 2)
        # p.setPen(pen)
        p.fillPath(path, self._rect_color)
        p.drawPath(path)

    @property
    def _length(self):
        return self.width() - 2 * self._padding - 2 * self._rect_width

    @property
    def _range(self):
        return self._max_value - self._min_value

    def _scale_to_view(self, x, idx: int):
        return self._padding + self._rect_width * (idx - 1) + \
               (x - self._min_value) / self._range * self._length

    def _scale_from_view(self, x, idx: int):
        return self._min_value + (x - self._padding - self._rect_width * (idx - 1)) * \
               self._range / self._length
