import torch


def clamp_boxes(boxes, size: int = 512):
    torch.clamp_(boxes[:, 0], min=0)
    torch.clamp_(boxes[:, 1], min=0)
    torch.clamp_(boxes[:, 2], max=size)
    torch.clamp_(boxes[:, 3], max=size)
