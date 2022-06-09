import logging
import multiprocessing
from time import perf_counter
from functools import lru_cache

from queue import Empty

import torch
from multiprocessing import Manager

from .basicserver import BasicServer, AppConfig

from .image_path_gen import ImagePathGen
from .save_data import SaveData
from ..server_operations import ProcessImages, FeatureDetector
from ..parallelize_ops import Workers, SharedResources, run_pool
from gixi.server.time_record import TimeRecorder


class MultiProcessServer(BasicServer):
    def __init__(self, config: AppConfig):
        super().__init__(config)
        FastServer.LOG_LEVEL = config.log_config.log_level

        self.log = logging.getLogger(__name__)
        self.resources = FastServerResources(config)
        self.methods = self.get_method_list()
        self.model = FastModelPrediction(self.resources, config)
        self.log.info('Started multiprocessing server')

    def get_method_list(self):
        available = multiprocessing.cpu_count()
        if self.config.cluster_config.max_cores > 0:
            available = min(available, self.config.cluster_config.max_cores)
        assert available > 2, f'Not enough available cpu cores!'
        methods = ['collect_paths'] + ['save_data'] + (available - 2) * ['process_images']

        return methods

    def run(self):
        with run_pool(
                FastServer,
                self.resources,
                self.methods,
                config=self.config.asdict()
        ):
            self.model.run()
            self.log.info(str(self.save_time_records()))

    def get_time_recorder(self) -> TimeRecorder:
        return self.model.time_recorder + self.resources.get_time_recorder()


class FastServerResources(SharedResources):
    def __init__(self, config: AppConfig):
        manager = Manager()
        super().__init__(manager)

        self.timeout = config.cluster_config.timeout * 0.9  # finish the job nicely before the job is terminated
        self.start_time = perf_counter()
        self._num_found_images = manager.Value('i', 0)
        self._num_saved_images = manager.Value('i', 0)
        self._lock_num_found_images = manager.Lock()
        self._lock_num_predicted_images = manager.Lock()

        self.max_batch = config.parallel.max_batch

        self._record_file_path = config.log_config.record_filename
        self._record_time = config.log_config.record_time

        self.paths_queue = manager.Queue()
        self.stats_queue = manager.Queue()
        self.images_queue = manager.Queue(self.max_batch)
        self.results_queue = manager.Queue(self.max_batch)
        self.time_records = manager.Queue()

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
        return self.is_timeout or self.error_occurred or (
                self.is_stopped and
                self.num_found_images == self.num_saved_images and
                self.results_queue.empty()
        )

    @lru_cache()
    def get_time_recorder(self):
        record = TimeRecorder('total')
        while not self.time_records.empty():
            record.add_records(self.time_records.get())
        return record


class FastServer(Workers):
    resources: FastServerResources
    time_recorder: TimeRecorder

    def on_start(self, **kwargs):
        config = AppConfig.from_dict(kwargs['config'])

        self.time_recorder = TimeRecorder(self.method_name, no_record=not config.log_config.record_time)

    def on_stop(self, **kwargs):
        self.resources.time_records.put(self.time_recorder.records.copy())

    def collect_paths(self, **kwargs):
        config = AppConfig.from_dict(kwargs['config'])

        image_path_gen = ImagePathGen(config)

        for paths in image_path_gen:
            self.resources.paths_queue.put(paths)

        self.resources.add_num_found_images(image_path_gen.num_image_batches)
        self.time_recorder += image_path_gen.time_recorder

        self.log.debug(f'num_found_image = {self.resources.num_found_images}')
        self.log.debug(f'Found {image_path_gen.num_processed_imgs} images.')

        self.resources.stop()

    def process_images(self, timeout=0.01, **kwargs):
        config = AppConfig.from_dict(kwargs['config'])
        process = ProcessImages(config)

        while not self.resources.finished:
            self.time_recorder.start_record('get_img_paths')
            try:
                img_paths = self.resources.paths_queue.get(timeout=timeout)
                self.time_recorder.end_record()
            except (OSError, ValueError, Empty):
                self.log.debug(f'paths_queue empty, continue.')
                self.time_recorder.end_record('timeout')
                continue

            self.log.debug(f'Processing {str(img_paths)}.')

            self.time_recorder.start_record('process_imgs')
            data = process(img_paths)
            if data:
                self.time_recorder.end_record()
                self.log.debug(f'Put result to images_queue.')
                self.resources.images_queue.put(data)
            else:
                self.time_recorder.end_record('empty_data')
                self.log.debug(f'num_found_images = {self.resources.num_found_images}')
                self.resources.add_num_found_images(-1)

        self.time_recorder += process.time_recorder

    def save_data(self, timeout=0.1, **kwargs):
        config = AppConfig.from_dict(kwargs['config'])
        save_data = SaveData(config)

        while not self.resources.finished:
            self.time_recorder.start_record('wait_data_list')

            try:
                data_list = self.resources.results_queue.get(timeout=timeout)
                self.time_recorder.end_record()
            except (OSError, ValueError, Empty):
                self.time_recorder.end_record('timeout')

                self.log.debug(f'results_queue empty, continue.')
                continue
            try:
                save_data(data_list)
                self.resources.add_num_saved_images(len(data_list))
            except Exception as err:
                self.log.exception(err)

        self.time_recorder += save_data.time_recorder


class FastModelPrediction(object):
    def __init__(self, resources: FastServerResources, config: AppConfig):
        self.log = logging.getLogger(__name__)
        self.resources = resources
        self.detector = FeatureDetector(config)
        self.time_recorder = TimeRecorder('detection', no_record=not config.log_config.record_time)

    @torch.no_grad()
    def run(self, timeout=0.5):
        while not self.resources.finished:
            data_list = []

            for i in range(self.resources.max_batch):
                self.time_recorder.start_record('get_image')
                try:
                    data = self.resources.images_queue.get(timeout=timeout)
                    self.time_recorder.end_record()
                    data_list.append(data)
                except (OSError, ValueError, Empty):
                    self.log.debug(f'Timeout waiting for data, run batch with {len(data_list)} images.')
                    self.time_recorder.end_record('timeout')
                    break
            if not data_list:
                self.log.debug(f'Data list is empty, continue waiting for new data.')
                continue
            try:
                with self.time_recorder('detect'):
                    data_list = self.detector(data_list)
                self.resources.results_queue.put(data_list)
            except Exception as err:
                self.log.exception(err)
                return

            self.log.debug(f'Added num_predicted_images: {len(data_list)}')

        self.log.info('Detection process is finished.')
