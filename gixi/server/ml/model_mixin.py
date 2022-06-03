from typing import Union
from collections import OrderedDict
from pathlib import Path

import torch
from torch.nn import Module

ModelType = Union[Module, 'ModelMixin']


class ModelMixin:
    MODEL_DIR: Path = Path(__file__).parents[1] / 'saved_models'

    def cpu_state_dict(self: ModelType):
        return OrderedDict([(k, v.to('cpu')) for k, v in self.state_dict().items()])

    def model_path(self: ModelType, name: str) -> Path:
        if '.h5' not in name:
            name = f'{name}.h5'
        return self.MODEL_DIR / name

    def load_model(self: ModelType, name: str, device: torch.device = 'cuda'):
        self.load_state_dict(torch.load(self.model_path(name), map_location=device))

    def save_model(self: ModelType, name: str):
        torch.save(self.state_dict(), self.model_path(name))

    @property
    def is_cuda(self: ModelType) -> bool:
        return next(self.parameters()).is_cuda

    @property
    def device(self: ModelType) -> torch.device:
        return next(self.parameters()).device
