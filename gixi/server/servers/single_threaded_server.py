from typing import Tuple, List

import logging
from pathlib import Path

from ..app_config import AppConfig
from ..server_operations import FeatureDetector, ProcessImages
from .basicserver import BasicServer
from .image_path_gen import ImagePathGen

from .save_data import SaveData


class SingleThreadedServer(BasicServer):
    def __init__(self, config: AppConfig):
        super().__init__(config)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s]: %(funcName)s: %(message)s'
        )

        self.log = logging.getLogger(__name__)
        self.max_batch = self.config.parallel.max_batch
        self.detector = FeatureDetector(self.config)
        self.process_images = ProcessImages(self.config)
        self.image_path_gen = ImagePathGen(config)
        self.save_data = SaveData(config)

    def run(self):
        self.log.info(f'Run single-threaded server with config: {self.config}')

        batch = []

        for paths in self.image_path_gen:
            batch.append(paths)

            if len(batch) == self.max_batch:
                self.process_file(batch)
                batch.clear()

        if batch:
            self.process_file(batch)

        self.log.info('Run is completed!')

    def process_file(self, batch: List[Tuple[Path, ...]]):
        if not batch:
            return

        data_list = [self.process_images(paths) for paths in batch]
        data_list = list(filter(lambda x: x is not None, data_list))

        if not len(data_list):
            return

        data_dicts = self.detector(data_list)
        self.save_data(data_dicts)
