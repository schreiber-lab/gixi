import os
from pathlib import Path

from gixi.server.app_config import AppConfig
from gixi.server.time_record import TimeRecorder


class BasicServer(object):
    TIME_RECORDS_PATH: Path = Path(__file__).parents[3] / 'time_records'

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
        if not self.config.log_config.record_time or not self.config.log_config.record_filename:
            return TimeRecorder('')

        self.TIME_RECORDS_PATH.mkdir(exist_ok=True)
        time_records = self.get_time_recorder()
        time_records.save(self.TIME_RECORDS_PATH / self.config.log_config.record_filename)
        return time_records
