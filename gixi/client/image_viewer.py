import numpy as np

from PyQt5.QtCore import pyqtSlot

from gixi.client.basic_widgets import Viewer2D
from gixi.client.rois import BasicRoiRing


class ImageViewer(Viewer2D):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rois = []

    @pyqtSlot(object)
    def set_image(self, img):
        self.remove_rois()
        self.set_data(img)

    @pyqtSlot(object)
    def set_rois(self, boxes: np.ndarray):
        if self.image is None:
            return
        self.remove_rois()

        for box in boxes:
            self._rois.append(self._add_roi(box))

    def remove_rois(self):
        while self._rois:
            self.image_plot.removeItem(self._rois.pop())

    def _add_roi(self, box: np.ndarray):
        roi_widget = BasicRoiRing()
        roi_widget.set_box(box, self.image.shape)
        self.image_plot.addItem(roi_widget)
        return roi_widget
