from typing import Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

__all__ = [
    'give_matching_indices',
    'np_iou',
]


def give_matching_indices(
        boxes: np.ndarray,
        prev_boxes: np.ndarray,
        thresh: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    iou_mtx = np_iou(prev_boxes, boxes)
    prev_ind, current_ind = linear_sum_assignment(-iou_mtx)

    indices = iou_mtx[prev_ind, current_ind] > thresh
    prev_ind, current_ind = prev_ind[indices], current_ind[indices]
    iou_values = iou_mtx[prev_ind, current_ind]

    return current_ind, prev_ind, iou_values


def np_iou(boxes_1: np.ndarray, boxes_2: np.ndarray):
    x11, y11, x12, y12 = np.split(boxes_1, 4, axis=1)
    x21, y21, x22, y22 = np.split(boxes_2, 4, axis=1)
    x_a = np.maximum(x11, np.transpose(x21))
    y_a = np.maximum(y11, np.transpose(y21))
    x_b = np.minimum(x12, np.transpose(x22))
    y_b = np.minimum(y12, np.transpose(y22))
    inter_area = np.maximum((x_b - x_a + 1), 0) * np.maximum((y_b - y_a + 1), 0)
    box_a_area = (x12 - x11 + 1) * (y12 - y11 + 1)
    box_b_area = (x22 - x21 + 1) * (y22 - y21 + 1)

    return inter_area / (box_a_area + np.transpose(box_b_area) - inter_area)
