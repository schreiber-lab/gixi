import cv2 as cv
import numpy as np

from ..app_config import ContrastConfig


class ContrastCorrection(object):
    def __init__(self, contrast_config: ContrastConfig = None):
        self.config = contrast_config or ContrastConfig()

    def __call__(self, img: np.ndarray):
        if self.config.disable:
            return img
        return preprocess_exp(img, self.config.limit, self.config.coef, self.config.log)


def clahe(img, limit: float = 5000):
    return cv.createCLAHE(clipLimit=limit, tileGridSize=(1, 1)).apply(img.astype('uint16'))


def norm(img):
    return (img - img.min()) / (img.max() - img.min())


def preprocess_exp(img, limit: float = 2000, coef: float = 5000, log: bool = True):
    if log:
        img = np.log10(norm(img) * coef + 1)
    return norm(clahe(norm(img) * coef, limit)).astype(np.float32)
