from typing import List
from pathlib import Path

from gixi.server.time_record import TimeRecorder

from ..h5utils import H5FileManager
from ..app_config import AppConfig, SaveConfig


class SaveData(object):
    def __init__(self, config: AppConfig, time_recorder: TimeRecorder = None):
        self.time_recorder = time_recorder or TimeRecorder('save_data', no_record=config.log_config.no_time_record)

        self.save_config = config.save_config
        self._keys = _init_save_keys(self.save_config)
        self.src_path = config.src_path
        self.h5file = H5FileManager(config.dest_path)
        self.group_name = self.h5file.init_folder(self.src_path.name)

    def __call__(self, data_dicts: List[dict]):
        for data_dict in data_dicts:
            self.save_data(data_dict)

    def save_data(self, data_dict: dict):
        if not data_dict:
            return

        paths = data_dict.pop('paths')
        path_names = ','.join(_get_path_name(p, self.src_path) for p in paths)

        if data_dict:
            with self.time_recorder():
                file_name = _get_path_name(paths[0], self.src_path)
                data_dict = {k: data_dict[k] for k in self._keys}
                self.h5file.save(self.group_name, file_name, data_dict, attrs=dict(paths=path_names))


def _get_path_name(path: Path, rel_folder: Path) -> str:
    # TODO: support other formats than .tif
    return str(path.relative_to(rel_folder)).split('.tif')[0]


def _init_save_keys(config: SaveConfig):
    keys = ['boxes']
    if config.save_img:
        keys.append('img')
    if config.save_scores:
        keys.append('scores')
    if config.save_polar_img:
        keys.append('polar_img')
    return keys
