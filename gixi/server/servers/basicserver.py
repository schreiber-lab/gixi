import os
from pathlib import Path

from ..app_config import AppConfig


class BasicServer(object):
    def __init__(self, config: AppConfig):
        self.config = config
        self.src_path: Path = config.src_path
        self.dest_path: Path = config.dest_path

        if not config.cluster_config.use_cuda:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""

        assert self.src_path.is_dir() or self.src_path.is_symlink(), f'Directory {self.src_path} does not exist!'

    def run(self):
        pass
