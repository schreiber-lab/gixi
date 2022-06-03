import numpy as np

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QColor

from pyqtgraph import ROI, RectROI


class BasicRoiRing(ROI):
    def __init__(self,
                 radius: float = 1,
                 width: float = 1,
                 angle: float = 0,
                 angle_std: float = 1,
                 center: tuple = (0, 0),
                 movable: bool = False,
                 parent=None,
                 **kwargs):

        super().__init__(center,
                         (radius, radius),
                         movable=movable,
                         parent=parent,
                         **kwargs)

        self._center = center
        self._radius = radius
        self._width = width
        self._angle = angle
        self._angle_std = angle_std

        self.aspectLocked = True
        self.set_radius(self._radius)
        self.setPen(QColor(0, 0, 255))

    def update_pos(self):
        self.set_radius(self._radius)

    def set_center(self, center: tuple):
        self._center = center
        d = self._radius + self._width / 2
        pos = (center[1] - d, center[0] - d)
        self.setPos(pos)

    def set_radius(self, radius):
        self._radius = radius if radius > 0 else 0
        s = 2 * radius + self._width
        self.setSize((s, s))
        self.set_center(self._center)

    def set_width(self, width):
        self._width = width
        self.set_radius(self._radius)

    def set_angle(self, angle):
        self._angle = angle
        self.set_center(self._center)

    def set_angle_std(self, angle):
        self._angle_std = angle
        self.set_center(self._center)

    def set_params(self, *,
                   radius: float = None, width: float = None, angle: float = None,
                   angle_std: float = None, center: tuple = None):

        should_set_radius: bool = False

        if radius is not None and radius != self._radius:
            self._radius = radius
            should_set_radius = True
        if width is not None and width != self._width:
            self._width = width
            should_set_radius = True
        if angle is not None and angle != self._angle:
            self._angle = angle
        if angle_std is not None and angle_std != self._angle_std:
            self._angle_std = angle_std
        if center is not None and self._center != center:
            self._center = center
        if should_set_radius:
            self.set_radius(radius)
        else:
            self.set_center(self._center)

    def paint(self, p, opt, widget):
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(self.currentPen)

        x1, y1 = 0, 0
        x2, y2 = x1 + self._width, y1 + self._width
        x3, y3 = x1 + self._width / 2, y1 + self._width / 2
        d1, d2, d3 = (2 * self._radius + self._width,
                      2 * self._radius - self._width,
                      2 * self._radius)

        # p.scale(self._radius, self._radius)
        r1 = QRectF(x1, y1, d1, d1)
        r2 = QRectF(x2, y2, d2, d2)
        r3 = QRectF(x3, y3, d3, d3)
        angle = - self._angle or 0
        angle_std = self._angle_std or 360
        a1, a2 = int((angle - angle_std / 2) * 16), int(angle_std * 16)
        p.drawArc(r1, a1, a2)
        p.drawArc(r2, a1, a2)
        dash_pen = QPen(self.currentPen)
        dash_pen.setStyle(Qt.DashLine)
        p.setPen(dash_pen)
        p.drawArc(r3, a1, a2)

    def getArrayRegion(self, arr, img=None, axes=(0, 1), **kwds):
        """
        Return the result of ROI.getArrayRegion()
        masked by the elliptical shape
        of the ROI. Regions outside the ellipse are set to 0.
        """
        # Note: we could use the same method as used by PolyLineROI, but this
        # implementation produces a nicer mask.
        arr = ROI.getArrayRegion(self, arr, img, axes, **kwds)
        if arr is None or arr.shape[axes[0]] == 0 or arr.shape[axes[1]] == 0:
            return arr
        w = arr.shape[axes[0]]
        h = arr.shape[axes[1]]
        ## generate an ellipsoidal mask
        mask = np.fromfunction(
            lambda x, y: (((x + 0.5) / (w / 2.) - 1) ** 2 + ((y + 0.5) / (h / 2.) - 1) ** 2) ** 0.5 < 1, (w, h))

        # reshape to match array axes
        if axes[0] > axes[1]:
            mask = mask.T
        shape = [(n if i in axes else 1) for i, n in enumerate(arr.shape)]
        mask = mask.reshape(shape)

        return arr * mask

    def shape(self):
        self.path = QPainterPath()
        self.path.addEllipse(self.boundingRect())
        return self.path

    def set_box(self, box: np.ndarray, img_shape):
        x0, y0, x1, y1 = box
        max_radius = np.sqrt(np.sum(np.asarray(img_shape) ** 2))
        r_c = max_radius
        p_c = 90
        r = (x0 + x1) / 2 * r_c
        w = abs(x1 - x0) * r_c
        a = (y0 + y1) / 2 * p_c
        a_std = abs(y1 - y0) * p_c

        self._radius = r
        self._width = w
        self._angle = a
        self._angle_std = a_std

        self.update_pos()


class Roi2DRect(RectROI):
    def __init__(self):
        super().__init__(pos=(0, 0), size=(1, 1), centered=False, sideScalers=False)

        self.handle = self.handles[0]['item']
        self.handles.pop(0)
        self.handle.disconnectROI(self)
        self.handle.hide()  # how to remove???
        self.setPen(QColor(0, 0, 255))

    def set_box(self, box: np.ndarray, img_shape):
        a_size, q_size = img_shape
        x0, y0, x1, y1 = box
        x0 *= q_size
        y0 *= a_size
        x1 *= q_size
        y1 *= a_size

        w, a_w = abs(x1 - x0), abs(y1 - y0)

        pos = [x0, y0]
        size = [w, a_w]
        self.setSize(size)
        self.setPos(pos)
