from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtCore import pyqtSlot

from gixi.client.image_viewer import ImageViewer
from gixi.client.polar_viewer import PolarViewer


class ImageTab(QTabWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_viewer = ImageViewer(self)
        self.polar_viewer = PolarViewer(self)
        self.addTab(self.image_viewer, 'Image Viewer')
        self.addTab(self.polar_viewer, 'Polar Viewer')

    @pyqtSlot(object)
    def set_image(self, img):
        self.image_viewer.set_image(img)
        self.polar_viewer.clear_image()

    @pyqtSlot(object)
    def set_data(self, data: dict):
        img = data['img']
        polar_img = data['polar_img']
        boxes = data['boxes']
        self.image_viewer.set_image(img)
        self.polar_viewer.set_image(polar_img)
        self.image_viewer.set_rois(boxes)
        self.polar_viewer.set_rois(boxes)
