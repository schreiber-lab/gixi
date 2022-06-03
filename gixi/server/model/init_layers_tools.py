from typing import Tuple, List

import torch
from torch import nn
import torch.nn.functional as F

from torchvision.models import resnet18

import numpy as np


def copy_resnet_kernels(model, layer_pairs: List[Tuple[str, str]], resnet=None):
    resnet = resnet or resnet18(True)

    src_names, dest_names = list(zip(*layer_pairs))

    src_modules = {n: m for n, m in resnet.named_modules() if n in src_names}
    dest_modules = {n: m for n, m in model.named_modules() if n in dest_names}

    for s_name, d_name in zip(src_names, dest_names):
        copy_conv_layer(src_modules[s_name], dest_modules[d_name])


@torch.no_grad()
def copy_conv_layer(conv_src, conv_dest):
    assert isinstance(conv_src, nn.Conv2d)
    assert isinstance(conv_dest, nn.Conv2d)

    conv_src_weight = _reshape_conv_weight(conv_src.weight, conv_dest.weight.shape)
    conv_dest.weight.copy_(conv_src_weight)


def _reshape_conv_weight(weight, target_shape):
    if weight.shape == target_shape:
        return weight

    if weight.shape[-2:] != target_shape[-2:]:
        weight = F.interpolate(weight, target_shape[-2:])

    if weight.shape == target_shape:
        return weight

    src_kernels = int(np.prod(weight.shape[:2]))
    target_kernels = int(np.prod(target_shape[:2]))

    weight = weight.view(-1, *weight.shape[-2:])

    indices = np.random.choice(np.arange(src_kernels), target_kernels, replace=(src_kernels < target_kernels))

    weight = weight[indices]

    return weight.view(*target_shape)
