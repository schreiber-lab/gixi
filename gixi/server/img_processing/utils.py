import random

import torch
from torch import Tensor


def interp1d(x: Tensor, y: Tensor, x_new: Tensor) -> Tensor:
    eps = torch.finfo(y.dtype).eps
    ind = torch.searchsorted(x.contiguous(), x_new.contiguous())
    ind = torch.clamp(ind - 1, 0, x.shape[0] - 2)
    slopes = (y[1:] - y[:-1]) / (eps + (x[1:] - x[:-1]))
    return y[ind] + slopes[ind] * (x_new - x[ind])


def with_probability(probability: float):
    def wrapper(func):
        def new_func(img, *args, **kwargs):
            return func(img, *args, **kwargs) if random.random() < probability else img

        return new_func

    return wrapper


def normalize(img: Tensor) -> Tensor:
    return (img - img.min()) / (img.max() - img.min())
