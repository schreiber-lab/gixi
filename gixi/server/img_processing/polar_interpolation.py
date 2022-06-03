from typing import Tuple

import cv2 as cv
import numpy as np

from ..app_config import AppConfig


class PolarInterpolation(object):
    def __init__(self, config: AppConfig):
        self.config = config
        self.shape = (
            config.q_space.q_z_num,
            config.q_space.q_xy_num
        )
        self.polar_shape = (
            config.polar_config.angular_size,
            config.polar_config.q_size
        )
        self.yy, self.zz = _get_polar_grid((0, 0), self.shape, self.polar_shape)
        self.algorithm = config.polar_config.algorithm

        if self.algorithm not in (cv.INTER_LINEAR, cv.INTER_CUBIC, cv.INTER_LANCZOS4):
            self.algorithm = cv.INTER_LINEAR

    def __call__(self, img: np.ndarray) -> np.ndarray or None:
        return _calc_polar_img(img, self.yy, self.zz, self.algorithm)


def calc_polar_image(img: np.ndarray,
                     beam_center: Tuple[float, float] = (0, 0),
                     shape: Tuple[int, int] = (10, 10),
                     polar_shape: Tuple[int, int] = (512, 512),
                     algorithm=cv.INTER_LINEAR) -> np.ndarray or None:
    yy, zz = _get_polar_grid(beam_center, shape, polar_shape)

    return _calc_polar_img(img, yy, zz, algorithm)


def _calc_polar_img(img: np.ndarray, yy: np.ndarray, zz: np.ndarray, algorithm) -> np.ndarray or None:
    try:
        return cv.remap(img.astype(np.float32),
                        yy.astype(np.float32),
                        zz.astype(np.float32),
                        interpolation=algorithm)
    except cv.error:
        return


def _get_polar_grid(beam_center: Tuple[float, float] = (0, 0),
                    shape: Tuple[int, int] = (10, 10),
                    polar_shape: Tuple[int, int] = (512, 512)) -> Tuple[np.ndarray, np.ndarray]:
    y0, z0 = beam_center

    y = (np.arange(shape[1]) - y0)
    z = (np.arange(shape[0]) - z0)

    yy, zz = np.meshgrid(y, z)
    rr = np.sqrt(yy ** 2 + zz ** 2)
    phi = np.arctan2(zz, yy)
    r_range = (rr.min(), rr.max())
    phi_range = phi.min(), phi.max()

    phi = np.linspace(*phi_range, polar_shape[0])
    r = np.linspace(*r_range, polar_shape[1])

    r_matrix = r[np.newaxis, :].repeat(polar_shape[0], axis=0)
    p_matrix = phi[:, np.newaxis].repeat(polar_shape[1], axis=1)

    polar_yy = r_matrix * np.cos(p_matrix) + y0
    polar_zz = r_matrix * np.sin(p_matrix) + z0

    return polar_yy, polar_zz
