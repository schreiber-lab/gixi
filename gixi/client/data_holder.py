import logging
from pathlib import Path

import numpy as np

from PyQt5.QtCore import (
    QObject,
    pyqtSlot,
    pyqtSignal,
)

from PIL import Image

from gixi.server.img_processing import ContrastCorrection
from gixi.server.app_config import AppConfig
from gixi.server.h5utils import read_gixi, init_folder

from gixi.client.submit_job import submit_job
from gixi.client.tools import show_error
from gixi.client.read_cifs import get_powder_profile


class DataHolder(QObject):
    sigImageUpdated = pyqtSignal(object)
    sigDataUpdated = pyqtSignal(dict)
    sigCifProfileUpdated = pyqtSignal(dict)
    sigWatchFolder = pyqtSignal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger(__name__)
        self.image = None
        self.data = None
        self._q_num: int = 1024
        self.current_config: AppConfig = AppConfig()
        self.contrast_correction = ContrastCorrection()

    @property
    def q_max(self):
        # TODO: info has to be taken from saved files (not from current config!)
        if self.current_config:
            return np.sqrt(self.current_config.q_space.q_z_max ** 2 + self.current_config.q_space.q_xy_max ** 2)
        else:
            return 1.

    @property
    def q(self):
        return np.linspace(0, self.q_max, self._q_num)

    @pyqtSlot(str)
    def read_gixi(self, filename: str):
        try:
            data = read_gixi(filename)
        except Exception as err:
            self.log.exception(err)
            return
        self.set_data(data)

    @pyqtSlot(AppConfig)
    def submit_job(self, config: AppConfig):
        data_folder = Path(config.job_config.data_dir).expanduser() / 'raw' / config.job_config.folder_name
        if not config.general.real_time and not data_folder.is_dir() and not data_folder.is_symlink():
            show_error(f'Data folder {str(data_folder)} does not exist.', error_title='Directory not found.')
            return
        # folder = init_folder(config.dest_path, config.src_path.name, add_time=not config.job_config.rewrite_previous)
        out, err = submit_job(config)
        self.log.info(f'Job submitted: {out}. Config: {config}.')
        if err:
            self.log.error(f'Error submitting job: {err}')
        # else:
        #     self.sigWatchFolder.emit(folder)

    @pyqtSlot(str)
    def set_image(self, path: str):
        self.log.info(f'Set image from path {path}')
        try:
            image = read_image(path)
            self.image = self.contrast_correction(image)
            self.sigImageUpdated.emit(self.image)
        except Exception as err:
            self.log.exception(err)

    @pyqtSlot(object)
    def set_data(self, data: dict):
        try:
            self._q_num = data['polar_img'].shape[1]
            self.data = {
                'img': data['img'],
                'polar_img': data['polar_img'],
                'boxes': data['boxes'],
                'q': self.q,
                'measured_profile': data['polar_img'].mean(0),
                'fitted_profile': _get_profile_from_boxes(data['boxes'], self._q_num),
            }
            self.sigDataUpdated.emit(self.data)
        except KeyError:
            return

    @pyqtSlot(str)
    def set_cif(self, path: str):
        try:
            q_profile = get_powder_profile(self.q, path)
            cif_data = {
                'q': self.q,
                'profile': q_profile,
                'name': Path(path).stem
            }
            self.sigCifProfileUpdated.emit(cif_data)
        except Exception as err:
            self.log.exception(err)

    @pyqtSlot(object)
    def set_dataset(self, dset: np.ndarray):
        if len(dset.shape) == 2:
            self.sigImageUpdated.emit(dset)

    @pyqtSlot(AppConfig)
    def set_config(self, config: AppConfig):
        self.current_config = config


def read_image(path):
    return np.array(Image.open(path))


def _get_mean_box_width(q, boxes):
    return np.mean([(x0 + x1) / 2 / 512 * q.max() for x0, y0, x1, y1 in boxes])


def _get_profile_from_boxes(boxes, num_points: int):
    q = np.linspace(0, 1, num_points)
    profile = np.zeros_like(q)
    for x0, y0, x1, y1 in boxes:
        profile += np.exp(- (q - (x0 + x1) / 2) ** 2 / 2 / (x1 - x0) ** 2)
    return profile / profile.max()
