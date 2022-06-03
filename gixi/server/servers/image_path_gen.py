from typing import Tuple
from time import perf_counter, sleep
from pathlib import Path

from ..app_config import AppConfig


class ImagePathGen(object):
    def __init__(self, config: AppConfig):
        self.config = config
        self.sum_images = config.general.sum_images
        self.src_folder = config.src_path
        self.is_real_time = config.general.real_time
        self.timeout = config.general.timeout
        self.sleep_time = config.general.sleep_time if not config.parallel.parallel_computation else 0
        self._num_processed_imgs = 0

    @property
    def num_processed_imgs(self) -> int:
        return self._num_processed_imgs

    def get_batch(self, wait_for_full_batch: int = True) -> Tuple[Path, ...]:
        paths = sorted(list(filter(lambda p: 'dark' not in p.name, self.src_folder.rglob('*.tif'))))
        unprocessed_paths = paths[self._num_processed_imgs:]
        path_batch = unprocessed_paths[:self.sum_images]

        if len(path_batch) < self.sum_images and wait_for_full_batch:
            return ()
        else:
            self._num_processed_imgs += len(path_batch)
            return tuple(path_batch)

    def __iter__(self):
        last_update = perf_counter()

        while True:
            paths = self.get_batch()

            if len(paths) == self.sum_images:
                yield paths
                last_update = perf_counter()
                continue
            elif not self.is_real_time or perf_counter() - last_update > self.timeout:
                break

            sleep(self.sleep_time)

        paths = self.get_batch(wait_for_full_batch=False)

        if paths:
            yield paths
