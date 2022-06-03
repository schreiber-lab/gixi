from typing import List, Callable


class TransformList(object):
    def __init__(self, transforms: List[Callable]):
        self.transforms = list(transforms)

    def __call__(self, x):
        for t in self.transforms:
            x = t(x)
        return x
