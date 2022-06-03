from typing import Tuple
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from .misc import to_np
from .postprocessing import PostProcessing


@torch.no_grad()
def get_image_prediction(
        model, img: np.ndarray, post_processing: PostProcessing,
        device: torch.device = 'cuda'
) -> Tuple[np.ndarray, np.ndarray]:
    model.eval()
    boxes, scores = model(img2torch(img, device=device))
    boxes, scores = post_processing(boxes[0], scores[0])
    return to_np(boxes), to_np(scores)


def img2torch(img: np.ndarray, device: torch.device = 'cuda'):
    return torch.tensor(img[None, None], dtype=torch.float32, device=device)


def read_image(path: Path) -> np.ndarray:
    return np.array(Image.open(path))
