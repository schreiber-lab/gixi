import torch

from .utils import interp1d


@torch.no_grad()
def torch_he(img, bins: int = 1000):
    bin_edges = torch.linspace(img.min(), img.max(), bins + 1, device=img.device)
    bin_d = (bin_edges[1] - bin_edges[0])
    bin_centers = bin_edges[:-1] + bin_d / 2
    img_flat = img.view(-1)
    hist = torch.histc(img_flat, bins=bins)
    cdf = torch.cumsum(hist, 0)
    cdf = cdf / cdf[-1]
    res = interp1d(bin_centers, cdf, img_flat)
    return res.view(img.shape)
