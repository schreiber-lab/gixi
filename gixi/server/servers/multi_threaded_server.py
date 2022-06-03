import logging
import multiprocessing
from time import perf_counter

from queue import Empty

import torch
from multiprocessing import Manager

from .basicserver import BasicServer, AppConfig

from .image_path_gen import ImagePathGen
from .save_data import SaveData
from ..server_operations import ProcessImages, FeatureDetector
from ..parallelize_ops import Workers, SharedResources, run_pool


class MultiThreadedServer(BasicServer):
    def __init__(self, config: AppConfig):
        super().__init__(config)
        FastServer.LOG_LEVEL = logging.info
        self.resources = FastServerResources(config)
        self.methods = FastServer.get_method_list()
        self.model = FastModelPrediction(self.resources, config)

    def run(self):
        with run_pool(
                FastServer,
                self.resources,
                self.methods,
                config=self.config.asdict()
        ):
            self.model.run()


class FastServerResources(SharedResources):
    def __init__(self, config: AppConfig):
        manager = Manager()
        super().__init__(manager)

        self.timeout = config.cluster_config.timeout
        self.start_time = perf_counter()
        self._num_found_images = manager.Value('i', 0)
        self._num_saved_images = manager.Value('i', 0)
        self._lock_num_found_images = manager.Lock()
        self._lock_num_predicted_images = manager.Lock()
        self.max_batch = config.parallel.max_batch

        self.paths_queue = manager.Queue()
        self.stats_queue = manager.Queue()
        self.images_queue = manager.Queue(self.max_batch)
        self.results_queue = manager.Queue(self.max_batch)

    @property
    def num_found_images(self):
        return self._num_found_images.value

    def add_num_found_images(self, num: int):
        with self._lock_num_found_images:
            self._num_found_images.value += num

    @property
    def num_saved_images(self):
        return self._num_saved_images.value

    def add_num_saved_images(self, num):
        with self._lock_num_predicted_images:
            self._num_saved_images.value += num

    @property
    def is_timeout(self):
        return perf_counter() - self.start_time > self.timeout

    @property
    def finished(self) -> bool:
        return self.is_timeout or (
                self.is_stopped and
                self.num_found_images == self.num_saved_images and
                self.results_queue.empty()
        )


class FastServer(Workers):
    resources: FastServerResources

    def collect_paths(self, **kwargs):
        config = AppConfig.from_dict(kwargs['config'])

        image_path_gen = ImagePathGen(config)

        for paths in image_path_gen:
            self.resources.paths_queue.put(paths)

        self.resources.add_num_found_images(image_path_gen.num_processed_imgs)
        self.log.info(f'num_found_image = {self.resources.num_found_images}')
        self.log.info(f'Found {image_path_gen.num_processed_imgs} .tif files .')
        self.resources.stop()

    def process_images(self, timeout=0.01, **kwargs):
        config = AppConfig.from_dict(kwargs['config'])
        process = ProcessImages(config)

        while not self.resources.finished:
            try:
                img_paths = self.resources.paths_queue.get(timeout=timeout)
            except (OSError, ValueError, Empty):
                self.log.debug(f'paths_queue empty, continue.')
                continue
            self.log.debug(f'Processing {str(img_paths)}.')
            data = process(img_paths)
            if data:
                self.log.debug(f'Put result to images_queue.')
                self.resources.images_queue.put(data)
            else:
                self.log.info(f'num_found_images = {self.resources.num_found_images}')
                self.resources.add_num_found_images(-1)

    def save_data(self, timeout=0.1, **kwargs):
        config = AppConfig.from_dict(kwargs['config'])
        save_data = SaveData(config)

        while not self.resources.finished:
            try:
                data_list = self.resources.results_queue.get(timeout=timeout)
            except (OSError, ValueError, Empty):
                self.log.debug(f'results_queue empty, continue.')
                continue
            try:
                save_data(data_list)
                self.resources.add_num_saved_images(len(data_list))
            except Exception as err:
                self.log.exception(err)

    @staticmethod
    def get_method_list():
        available = multiprocessing.cpu_count() - 3
        methods = ['collect_paths'] + ['save_data'] + available * ['process_images']
        return methods


class FastModelPrediction(object):
    def __init__(self, resources: FastServerResources, config: AppConfig):
        self.log = logging.getLogger(__name__)
        self.resources = resources
        self.detector = FeatureDetector(config)

    @torch.no_grad()
    def run(self, timeout=0.5):
        while not self.resources.finished:
            data_list = []

            for i in range(self.resources.max_batch):
                try:
                    data = self.resources.images_queue.get(timeout=timeout)
                    data_list.append(data)
                except (OSError, ValueError, Empty):
                    self.log.info(f'Timeout waiting for data, run batch with {len(data_list)} images.')
                    break
            if not data_list:
                self.log.info(f'Data list is empty, continue waiting for new data.')
                continue
            try:
                data_list = self.detector(data_list)
                self.resources.results_queue.put(data_list)
            except Exception as err:
                self.log.exception(err)

            self.log.debug(f'Added num_predicted_images: {len(data_list)}')

        self.log.info('model run is finished!')
