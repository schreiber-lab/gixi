import torch
from torch import Tensor

from torchvision.ops import box_iou


def box_is_within_anchor(boxes: Tensor, anchors: Tensor) -> Tensor:
    boxes = boxes[:, None]
    anchors = anchors[None]
    return (
            (boxes[..., 0] >= anchors[..., 0]) &
            (boxes[..., 1] >= anchors[..., 1]) &
            (boxes[..., 2] <= anchors[..., 2]) &
            (boxes[..., 3] <= anchors[..., 3])
    ).type(torch.float)


# TODO: optimize by simply calculating area ratio
def box_iou_within_anchor(boxes: Tensor, anchors: Tensor) -> Tensor:
    return box_iou(boxes, anchors) * box_is_within_anchor(boxes, anchors)
