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
        src_name = src_name.split('.')[0]
        if add_time:
            src_name = src_name + dt.strftime(dt.now(), '-%d_%b_%H-%M-%S')
        self.folder_path = self.parent_folder_path / src_name
        self.log.info(f'Saving images to {str(self.folder_path)} ... ')
        self.folder_path.mkdir(exist_ok=True)

    def save(self, file_name: str, data_dict: dict, attrs: dict = None):
        file_name = Path(file_name).name.split('.')[0] + '.gixi'

        with File(self.folder_path / file_name, 'w') as f:
            save_image_data(data_dict, f, attrs)

        self.log.info(f'Saved {file_name}')

    @staticmethod
    def read(filepath: str or Path):
        return read_gixi(filepath)


def read_gixi(filepath: str or Path) -> dict:
    with File(filepath, 'r') as f:
        data_dict = {k: f[k][()] for k in f.keys()}
        data_dict['attrs'] = dict(f.attrs)
        return data_dict


class H5FileManager(object):
    def __init__(self, path: Path):
        self.log = logging.getLogger(__name__)
        self.path = path

    @property
    def name(self) -> str:
        return self.path.name

    def init_folder(self, folder_name: str) -> str:
        return init_group(self.path, folder_name)

    def save(self, folder_name: str, file_name: str, data_dict: dict, attrs: dict = None):
        with h5py.File(self.path, 'a') as f:
            if folder_name not in f:
                f.create_group(folder_name)
            group = init_img_group(file_name, f[folder_name])
            save_image_data(data_dict, group, attrs)
            self.log.info(f'Saved image {folder_name}/{file_name}')

    def read(self, image_key: str) -> dict or None:
        try:
            with h5py.File(self.path, 'r') as f:
                if image_key in f:
                    img_folder = f[image_key]
                    data_dict = {k: img_folder[k][()] for k in img_folder.keys()}
                    return data_dict
        except Exception as err:
            self.log.exception(err)

    def read_dataset(self, key: str) -> np.ndarray or None:
        try:
            with h5py.File(self.path, 'r') as f:
                if key in f:
                    return f[key][()]
        except Exception as err:
            self.log.exception(err)

    def parse_group(self, folder_name: str) -> list or None:
        try:
            with h5py.File(self.path, 'r') as f:
                group = _get_group(folder_name, f)
                if group and isinstance(group, h5py.Group):
                    return sorted([group[k].name for k in group.keys()])
        except Exception as err:
            self.log.exception(err)

    def get_key_type(self, key: str) -> H5Items:
        try:
            with h5py.File(self.path, 'r') as f:
                group = _get_group(key, f)
                if not group:
                    return H5Items.not_exist
                if isinstance(group, h5py.File):
                    return H5Items.file
                if isinstance(group, h5py.Dataset):
                    return H5Items.dataset
                elif IMAGE_DATASET_ATTR in group.attrs:
                    return H5Items.image_dataset
                return H5Items.group
        except Exception as err:
            self.log.exception(err)
            return H5Items.error


def _get_group(group_name: str, f: h5py.File) -> h5py.Group or h5py.Dataset or None:
    if not group_name or group_name == '/':
        return f
    if group_name not in f:
        return
    return f[group_name]


def init_group(path: Path, name) -> str:
    with h5py.File(path, 'a') as f:
        group_name: str = name
        i = 1
        while group_name in f:
            group_name = f'{name}_{str(i).zfill(5)}'
            i += 1
        f.create_group(group_name)
    return group_name


def init_img_group(file_name: str, group: h5py.Group) -> h5py.Group:
    i = 1
    img_group_name = file_name

    while img_group_name in group:
        img_group_name = file_name + str(i).zfill(5)
        i += 1
    return group.create_group(img_group_name)


def save_image_data(data: dict, group: h5py.Group, attrs: dict = None):
    attrs = attrs or {}
    attrs[IMAGE_DATASET_ATTR] = IMAGE_DATASET_ATTR
    group.attrs.update(attrs)
    save_data_to_h5(data, group)


def save_data_to_h5(data: Dict[str, np.ndarray], group: h5py.Group):
    for k, v in data.items():
        group.create_dataset(k, data=v, dtype=v.dtype)
