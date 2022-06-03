import logging
from pathlib import Path
from enum import Enum

import h5py
import numpy as np


class H5Items(Enum):
    error = -1
    not_exist = 0
    group = 1
    dataset = 2
    image_dataset = 3
    file = 4


IMAGE_DATASET_ATTR: str = 'IMAGE_DATASET'


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
            group.attrs.update(attrs or {})
            save_image_data(data_dict, group)
            self.log.info(f'Saved {folder_name}/{file_name}.')

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
            group_name = f'{name}_{i}'
            i += 1
        f.create_group(group_name)
    return group_name


def init_img_group(file_name: str, group: h5py.Group) -> h5py.Group:
    i = 1
    img_group_name = file_name

    while img_group_name in group:
        img_group_name = file_name + str(i)
        i += 1
    return group.create_group(img_group_name)


def save_image_data(data: dict, group: h5py.Group):
    group.attrs[IMAGE_DATASET_ATTR] = IMAGE_DATASET_ATTR
    save_data_to_h5(data, group)


def save_data_to_h5(data: dict, group: h5py.Group):
    for k, v in data.items():
        group.create_dataset(k, data=v, dtype=v.dtype)
