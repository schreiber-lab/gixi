import os
from pathlib import Path

from gixi.server.app_config import AppConfig
from gixi.server.time_record import TimeRecorder


class BasicServer(object):
    def __init__(self, config: AppConfig):
        self.config = config
        self.src_path: Path = config.src_path
        self.dest_path: Path = config.dest_path

        if not config.cluster_config.use_cuda:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""

        assert self.src_path.is_dir() or self.src_path.is_symlink(), f'Directory {self.src_path} does not exist!'

    def get_time_recorder(self) -> TimeRecorder:
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()

    def save_time_records(self) -> TimeRecorder:
        path = self.config.record_filename

        if not path:
            return TimeRecorder('')

        time_records = self.get_time_recorder()
        time_records.save(path)
        return time_records
