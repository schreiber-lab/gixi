import logging
from typing import Dict
from pathlib import Path
from enum import Enum
from datetime import datetime as dt

import h5py
from h5py import File
import numpy as np


class H5Items(Enum):
    error = -1
    not_exist = 0
    group = 1
    dataset = 2
    image_dataset = 3
    file = 4


IMAGE_DATASET_ATTR: str = 'IMAGE_DATASET'


class GixiFileManager(object):
    def __init__(self, folder_path: str or Path):
        self.log = logging.getLogger(__name__)
        self.parent_folder_path = folder_path
        assert self.parent_folder_path.is_dir()
        self.folder_path = None

    def init_folder(self, src_name: str, add_time: bool = True):
        self.folder_path = init_folder(self.parent_folder_path, src_name, add_time)
        self.log.info(f'Saving images to {str(self.folder_path)} ... ')

    def save(self, file_name: str, data_dict: dict, attrs: dict = None):
        file_name = Path(file_name).name.split('.')[0] + '.gixi'

        with File(self.folder_path / file_name, 'w') as f:
            save_image_data(data_dict, f, attrs)

        self.log.info(f'Saved {file_name}')

    @staticmethod
    def read(filepath: str or Path):
        return read_gixi(filepath)


def init_folder(parent_folder_path: Path, src_name: str, add_time: bool = True) -> Path:
    src_name = src_name.split('.')[0]
    if add_time:
        src_name = src_name + dt.strftime(dt.now(), '-%d_%b_%H-%M-%S')
    folder_path = parent_folder_path / src_name
    folder_path.mkdir(exist_ok=True)
    return folder_path


def read_gixi(filepath: str or Path) -> dict:
    with File(filepath, 'r') as f:
        data_dict = {k: f[k][()] for k in f.keys()}
        data_dict['attrs'] = dict(f.attrs)
        return data_dict


def save_image_data(data: dict, group: h5py.Group, attrs: dict = None):
    attrs = attrs or {}
    attrs[IMAGE_DATASET_ATTR] = IMAGE_DATASET_ATTR
    group.attrs.update(attrs)
    save_data_to_h5(data, group)


def save_data_to_h5(data: Dict[str, np.ndarray], group: h5py.Group):
    for k, v in data.items():
        group.create_dataset(k, data=v, dtype=v.dtype)
