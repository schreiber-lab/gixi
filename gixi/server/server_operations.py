import logging
from typing import Tuple, List, Dict
from pathlib import Path
import sys
import warnings

import numpy as np
import torch

from gixi.server.models_collection import get_basic_model_1
from gixi.server.img_processing import (
    PolarInterpolation,
    QInterpolation,
    ContrastCorrection,
)
from gixi.server.app_config import AppConfig
from gixi.server.tools import read_image, to_np
from gixi.server.time_record import TimeRecorder


class FeatureDetector(object):
    def __init__(self, config: AppConfig, time_recorder: TimeRecorder = None):
        self.log = logging.getLogger(__name__)
        self.time_recorder = time_recorder or TimeRecorder('detector', no_record=config.log_config.no_time_record)
        self.device: torch.device = config.device
        self.config = config
        self._scale = _init_scale(config)

        try:
            with self.time_recorder('load_model'):
                self.model = get_basic_model_1(config)
            self.log.debug('Model loaded successfully!')
        except Exception as err:
            self.model = None
            self.log.exception(err)
            self.log.error('Model did not load. Stop the server')
            sys.exit(-1)

        self.log.debug(f'Device: {self.device}')

    @torch.no_grad()
    def __call__(self, data_list: List[dict]) -> List[dict]:
        polar_images = torch.tensor(
            [data['processed_img'] for data in data_list],
            dtype=torch.float32,
            device=self.device
        )[:, None]

        boxes_list, scores_list = self.model(polar_images)

        for i in range(len(boxes_list)):
            boxes_list[i] *= self._scale

        for data_dict, boxes, scores in zip(data_list, boxes_list, scores_list):
            data_dict['boxes'] = to_np(boxes)
            data_dict['scores'] = to_np(scores)

        return data_list


class ProcessImages(object):
    def __init__(self, config: AppConfig, time_recorder: TimeRecorder = None):
        self.time_recorder = time_recorder or TimeRecorder('process_images', no_record=config.log_config.no_time_record)

        self.log = logging.getLogger(__name__)
        self.device: torch.device = config.device
        self.config = config

        self.contrast = ContrastCorrection(config.contrast)
        self.q_interp = QInterpolation(config)
        self.p_interp = PolarInterpolation(config)

        self._save_img = config.save_config.save_img
        self._save_q_img = config.save_config.save_q_img
        self._save_polar_img = config.save_config.save_polar_img

    def polar_interpolation(self, img: np.ndarray):
        with self.time_recorder('polar'):
            return self.p_interp(img)

    def q_interpolation(self, img: np.ndarray):
        with self.time_recorder('q_space'):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=RuntimeWarning)
                return self.q_interp(img)

    def __call__(self, img_paths: Tuple[Path, ...]) -> Dict[str, np.ndarray] or None:
        try:
            with self.time_recorder('read'):
                img = np.sum([read_image(path) for path in img_paths], 0)

            if img.shape != self.q_interp.expected_shape:
                return

            res_dict: Dict[str, np.ndarray] = {}

            if self._save_img:
                res_dict['img'] = img
            if self._save_q_img:
                res_dict['q_img'] = self.q_interpolation(img)

            polar_img = self.polar_interpolation(img)

            if self._save_polar_img:
                res_dict['polar_img'] = polar_img

            res_dict['processed_img'] = self.contrast(polar_img)

            return res_dict
        except Exception as err:
            self.log.exception(err)
            return


def _init_scale(config: AppConfig):
    a_size, q_size = config.polar_config.angular_size, config.polar_config.q_size
    return 1. / torch.tensor([q_size, a_size, q_size, a_size], dtype=torch.float32, device=config.device)[None]
