from pathlib import Path

from torch import Tensor

__all__ = [
    'to_np',
    'tensor_size',
    'get_size_str'
]


def to_np(arr):
    if isinstance(arr, Tensor):
        arr = arr.detach().cpu().numpy()
    return arr


def tensor_size(t):
    size = t.element_size() * t.nelement()
    print(get_size_str(size))


def get_size_str(size):
    if size > 1000 ** 3:
        size = f'{(size / 1000 ** 3):.2f} Gb'
    elif size > 1000 ** 2:
        size = f'{(size / 1000 ** 2):.2f} Mb'
    else:
        size = f'{(size / 1000):.2f} Kb'
    return size


def listdir(path: Path, match: str = '*'):
    paths = [(p.name, p.stat().st_size) for p in path.glob(match)]
    paths.sort(key=lambda x: x[1], reverse=True)

    for name, size in paths:
        print(name, get_size_str(size))
