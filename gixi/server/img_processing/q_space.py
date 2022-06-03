import numpy as np

from qmap_interpolation import *

from ..app_config import QSpaceConfig


class QInterpolation(object):
    def __init__(self, q_config):
        self.detector_geometry = None
        self.q_map = None
        self.config = None

        self.c_image = ConvertedImage()
        self.set_q_config(q_config)

    def set_q_config(self, q_config: QSpaceConfig):
        beam_center = BeamCenter(int(q_config.z0), int(q_config.y0))
        size = Size(q_config.size_x, q_config.size_y)

        instrument = Instrument(q_config.wavelength, size, q_config.pixel_size)

        detector_geometry = DetectorGeometry(instrument, beam_center,
                                             q_config.incidence_angle,
                                             q_config.distance)

        q_map = QMap(0, q_config.q_xy_max, int(q_config.q_xy_num),
                     0, q_config.q_z_max, int(q_config.q_z_num))

        self.detector_geometry = detector_geometry
        self.q_map = q_map
        self.config = q_config

    def __call__(self, img):
        img = self.flip(img)
        c_image = self.c_image

        c_image.clear()
        c_image.append_images(Image(img, self.detector_geometry))
        converted = c_image.calculate_converted_image(self.q_map)

        return converted

    def flip(self, img):
        if self.config.flip_x:
            img = np.flip(img, 1)
        if self.config.flip_y:
            img = np.flip(img, 0)
        return img
