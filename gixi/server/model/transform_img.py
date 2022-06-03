from torch import nn
from torch import tensor
from torch import Tensor


class TransformImg(nn.Module):
    def __init__(self, mean: float = 0.3, std: float = 0.3):
        super().__init__()
        self.register_buffer('img_mean', tensor(mean))
        self.register_buffer('img_std', tensor(std))

    def forward(self, imgs: Tensor):
        return (imgs - self.img_mean) / self.img_std
