import numpy as np
import cv2 as cv

from gixi.server.app_config import QSpaceConfig, PolarConversionConfig, AppConfig

__all__ = [
    'QInterpolation',
    'PolarInterpolation',
    'convert2q_space',
    'convert2polar_space',
    'convert_img',
    'get_detector_q_grid',
    'get_detector_polar_grid',
]


class QInterpolation(object):
    def __init__(self, config: AppConfig):
        self.config = config
        self._flip_x, self._flip_y = self.config.q_space.flip_x, self.config.q_space.flip_y
        self.xy, self.zz = self._get_grid()
        self.algorithm = config.polar_config.algorithm

        if self.algorithm not in (cv.INTER_LINEAR, cv.INTER_CUBIC, cv.INTER_LANCZOS4):
            self.algorithm = cv.INTER_LINEAR

    def _get_grid(self):
        return get_detector_q_grid(self.config.q_space)

    def __call__(self, img: np.ndarray):
        img = self.flip(img)
        return convert_img(img, self.xy, self.zz, self.algorithm)

    @property
    def expected_shape(self) -> tuple:
        return self.config.q_space.size_y, self.config.q_space.size_x

    def flip(self, img: np.ndarray):
        if self._flip_x:
            img = np.flip(img, 1)
        if self._flip_y:
            img = np.flip(img, 0)
        return img


class PolarInterpolation(QInterpolation):
    def _get_grid(self):
        return get_detector_polar_grid(self.config.q_space, self.config.polar_config)


def convert2q_space(img: np.ndarray, q_config: QSpaceConfig, algorithm: int = cv.INTER_LINEAR):
    xy, zz = get_detector_q_grid(q_config)
    return convert_img(img, xy, zz, algorithm)


def convert2polar_space(img: np.ndarray,
                        q_config: QSpaceConfig,
                        polar_config: PolarConversionConfig,
                        algorithm: int = cv.INTER_LINEAR
                        ):
    xy, zz = get_detector_polar_grid(q_config, polar_config)
    return convert_img(img, xy, zz, algorithm)


def convert_img(img: np.ndarray, xy: np.ndarray, zz: np.ndarray, algorithm: int = cv.INTER_LINEAR):
    return cv.remap(img.astype(np.float32), xy.astype(np.float32), zz.astype(np.float32), algorithm)


def get_detector_q_grid(q_config: QSpaceConfig):
    q_xy, q_z = _get_q_grid(q_config)
    xy, zz = _get_detector_grid(q_config, q_xy, q_z)
    return xy, zz


def get_detector_polar_grid(q_config: QSpaceConfig, polar_config: PolarConversionConfig):
    q_xy, q_z = _get_q_polar_grid(q_config, polar_config)
    xy, zz = _get_detector_grid(q_config, q_xy, q_z)
    return xy, zz


def _get_detector_grid(q_config: QSpaceConfig, q_xy: np.ndarray, q_z: np.ndarray):
    k = 2 * np.pi / q_config.wavelength

    d = q_config.distance / q_config.pixel_size

    q_xy, q_z = q_xy / k, q_z / k

    q2 = q_xy ** 2 + q_z ** 2

    norm = d / (1 - q2 / 2)

    alpha = np.pi / 180 * q_config.incidence_angle

    sin, cos = np.sin(alpha), np.cos(alpha)

    zz = (norm * (q_z - sin) + d * sin) / cos

    yy2 = norm ** 2 - zz ** 2 - d ** 2
    yy2[yy2 < 0] = np.nan
    yy = np.sqrt(yy2)

    zz += q_config.z0
    yy += q_config.y0

    return yy, zz


def _get_q_grid(q_config: QSpaceConfig):
    q_xy = np.linspace(0, q_config.q_xy_max, q_config.q_xy_num)
    q_z = np.linspace(0, q_config.q_z_max, q_config.q_z_num)

    q_xy, q_z = np.meshgrid(q_xy, q_z)
    return q_xy, q_z


def _get_q_polar_grid(q_config: QSpaceConfig, polar_config: PolarConversionConfig):
    q_max = np.sqrt(q_config.q_xy_max ** 2 + q_config.q_z_max ** 2)

    r = np.linspace(0, q_max, polar_config.q_size)
    phi = np.linspace(0, np.pi / 2, polar_config.angular_size)

    rr, pp = np.meshgrid(r, phi)

    q_z = rr * np.sin(pp)
    q_xy = rr * np.cos(pp)

    return q_xy, q_z
