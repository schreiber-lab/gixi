import logging
from typing import Tuple, List, Dict
from pathlib import Path
import sys

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


class FeatureDetector(object):
    def __init__(self, config: AppConfig):
        self.log = logging.getLogger(__name__)
        self.device: torch.device = config.device
        self.config = config
        self._scale = _init_scale(config)

        try:
            self.model = get_basic_model_1(config)
            self.log.info('Model loaded successfully!')
        except Exception as err:
            self.model = None
            self.log.exception(err)
            self.log.error('Model did not load. Stop the server')
            sys.exit(-1)

        self.log.info(f'Device: {self.device}')

    @torch.no_grad()
    def __call__(self, data_list: List[dict]) -> List[dict]:
        polar_images = torch.tensor(np.array([data['polar_img'] for data in data_list]), device=self.device)[:, None]
        boxes_list, scores_list = self.model(polar_images)

        for i in range(len(boxes_list)):
            boxes_list[i] *= self._scale

        for data_dict, boxes, scores in zip(data_list, boxes_list, scores_list):
            data_dict['boxes'] = to_np(boxes)
            data_dict['scores'] = to_np(scores)

        return data_list


class ProcessImages(object):
    def __init__(self, config: AppConfig):
        self.log = logging.getLogger(__name__)
        self.device: torch.device = config.device
        self.config = config
        self.q_config = config.q_space

        self.contrast = ContrastCorrection(config.contrast)
        self.q_interp = QInterpolation(self.q_config)
        self.p_interp = PolarInterpolation(config)

    def polar_interpolation(self, img: np.ndarray):
        return self.p_interp(img)

    def q_interpolation(self, img: np.ndarray):
        return self.q_interp(img)

    @property
    def expected_shape(self) -> tuple:
        return self.q_interp.config.size_y, self.q_interp.config.size_x

    def __call__(self, img_paths: Tuple[Path, ...]) -> Dict[str, np.ndarray] or None:
        try:
            img = np.sum([read_image(path) for path in img_paths], 0)

            if img.shape != self.expected_shape:
                return

            img = self.q_interp(self.contrast(img))
            polar_img = self.p_interp(img)

            return {'img': img, 'polar_img': polar_img, 'paths': img_paths}
        except Exception as err:
            self.log.exception(err)
            return


def _init_scale(config: AppConfig):
    a_size, q_size = config.polar_config.angular_size, config.polar_config.q_size
    return 1. / torch.tensor([q_size, a_size, q_size, a_size], dtype=torch.float32, device=config.device)[None]
