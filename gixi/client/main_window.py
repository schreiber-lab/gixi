import argparse
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow

from pyqtgraph.dockarea import DockArea, Dock

from PyQt5.QtCore import Qt, pyqtSlot

from gixi.client.logs import QtLogWidgetHolder, set_log_config, ServerLogWidget
from gixi.client.data_holder import DataHolder
from gixi.client.file_tab import FileTab
from gixi.client.image_tab import ImageTab
from gixi.client.radial_profiles import RadialProfilesWidget
from gixi.client.config_widget import ConfigWidget
from gixi.client.tools import center_widget, Icon
from gixi.client.exception_message import UncaughtHook

DEFAULT_DIR = str(Path.home().absolute())


class MainWindow(QMainWindow):
    def __init__(self, base_dir: str = DEFAULT_DIR):
        super().__init__()
        self.setGeometry(0, 0, 1500, 700)
        self.main_widget = MainWidget(self, base_dir)
        self.setCentralWidget(self.main_widget)
        self.setWindowTitle('gixi')
        self.setWindowIcon(Icon('window_icon'))

        self._init_menubar()
        center_widget(self)
        self.exception_hook = UncaughtHook(self)

        self.show()

    def _init_menubar(self):
        self.menubar = self.menuBar()

        # Submit job

        self.file_menu = self.menubar.addMenu('Cluster')
        self.file_menu.addAction('Submit job', self._open_submit_job_window)

    @pyqtSlot()
    def _open_submit_job_window(self):
        self.main_widget.submit_job_window.show()


class MainWidget(DockArea):
    def __init__(self, parent=None, base_dir: str = DEFAULT_DIR):
        super().__init__(parent)

        self.data_controller = DataHolder(self)
        self.file_tab = FileTab(base_dir, self)
        self.log_holder = QtLogWidgetHolder(self)
        self.server_log = ServerLogWidget(parent=self)
        self.image_tab = ImageTab(self)
        # self.radial_profiles = RadialProfilesWidget(self)
        self.submit_job_window = ConfigWidget(self.data_controller.current_config, self)
        self.docks = {}

        self._init_ui()
        self._connect()

    def _init_ui(self):
        self._add_dock(self.file_tab, 'FileTab')
        self._add_dock(self.log_holder.widget, 'Client Logs', position='bottom', size=(10, 100))
        self._add_dock(self.server_log, 'Server Logs', position='right', relativeTo=self.docks['Client Logs'])
        self._add_dock(self.image_tab, 'ImageTab', position='right', size=(500, 500))
        # self._add_dock(self.radial_profiles, 'RadialProfiles', position='right', size=(500, 500))
        # self._hide_dock_callable('RadialProfiles')()

    def _add_dock(self, widget, name, size: tuple = (200, 200), position: str = 'right', relativeTo=None):
        dock = Dock(name)
        dock.addWidget(widget)
        self.addDock(dock, size=size, position=position, relativeTo=relativeTo)
        self.docks[name] = dock

    def _hide_dock_callable(self, name):
        def func(*args):
            self.docks[name].hide()

        return func

    def _show_dock_callable(self, name):
        def func(*args):
            self.docks[name].show()

        return func

    def _connect(self):
        self.file_tab.file_viewer.sigImageFileClicked.connect(self.data_controller.set_image)
        self.file_tab.file_viewer.sigGixiFileClicked.connect(self.data_controller.read_gixi)
        self.file_tab.h5_viewer.sigImageDatasetClicked.connect(self.data_controller.set_data)
        self.file_tab.h5_viewer.sigDatasetClicked.connect(self.data_controller.set_dataset)
        self.file_tab.file_viewer.sigH5FileClicked.connect(self.file_tab.switch_to_h5)
        self.file_tab.file_viewer.sigH5FileClicked.connect(self.file_tab.h5_viewer.set_h5_path)
        # self.file_tab.cif_viewer.sigCifFileClicked.connect(self.data_controller.set_cif)
        self.data_controller.sigImageUpdated.connect(self.image_tab.set_image)
        self.data_controller.sigDataUpdated.connect(self.image_tab.set_data)
        # self.data_controller.sigImageUpdated.connect(self.radial_profiles.clear_data)
        # self.data_controller.sigDataUpdated.connect(self._show_dock_callable('RadialProfiles'))
        # self.data_controller.sigImageUpdated.connect(self._hide_dock_callable('RadialProfiles'))
        # self.data_controller.sigDataUpdated.connect(self.radial_profiles.set_data)
        # self.data_controller.sigCifProfileUpdated.connect(self.radial_profiles.set_cif_profile)
        # self.data_controller.sigCifProfileUpdated.connect(self._show_dock_callable('RadialProfiles'))
        self.submit_job_window.sigSubmitJobClicked.connect(self.data_controller.submit_job)
        self.submit_job_window.sigCurrentConfigUpdated.connect(self.server_log.set_config)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str, default=None)
    args = parser.parse_args()
    return args


def main(path: str = DEFAULT_DIR):
    args = parse_args()

    set_log_config()

    path = args.dir if args.dir and Path(args.dir).is_dir() else path

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    q_app = QApplication([])

    app = MainWindow(path)
    app.show()

    return q_app.exec_()
