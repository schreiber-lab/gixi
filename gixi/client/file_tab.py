
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtCore import pyqtSlot

from gixi.client.file_viewer import FileViewer
from gixi.client.h5file_viewer import H5Viewer
from gixi.client.cif_viewer import CifViewer


class FileTab(QTabWidget):

    def __init__(self, path: str = '', parent=None):
        super().__init__(parent)
        self.file_viewer = FileViewer(path, self)
        self.h5_viewer = H5Viewer(parent=self)
        self.cif_viewer = CifViewer('', parent=self)
        self.addTab(self.file_viewer, 'File Viewer')
        self.addTab(self.h5_viewer, 'H5 Viewer')
        self.addTab(self.cif_viewer, 'Cif Viewer')

    @pyqtSlot()
    def switch_to_h5(self):
        self.setCurrentWidget(self.h5_viewer)

    @pyqtSlot()
    def switch_to_files(self):
        self.setCurrentWidget(self.file_viewer)
