from typing import Tuple

import torch
from torch import Tensor
from torchvision.ops import nms


from ..app_config import AppConfig


class PostProcessing(object):
    def __init__(self, config: AppConfig):
        self.config = config
        self.scale = _init_scale(config)
        self.nms_level = config.postprocessing_config.nms_level
        self.score_level = config.postprocessing_config.score_level

    def __call__(self, boxes: Tensor, scores: Tensor) -> Tuple[Tensor, Tensor]:
        indices = nms(boxes, scores, self.nms_level)
        boxes, scores = boxes[indices], scores[indices]
        indices = scores >= self.score_level
        boxes, scores = boxes[indices], scores[indices]
        boxes = boxes * self.scale
        return boxes, scores


def _init_scale(config: AppConfig):
    a_size, q_size = config.polar_config.angular_size, config.polar_config.q_size
    return 1. / torch.tensor([q_size, a_size, q_size, a_size], dtype=torch.float32, device=config.device)[None]
