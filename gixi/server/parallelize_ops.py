import sys
from typing import List, Type
import logging
import threading
from contextlib import contextmanager
from queue import Empty

import multiprocessing
from multiprocessing import Queue, Process

from gixi.server.log_config import set_workers_log


class SharedResources(object):
    def __init__(self, manager):
        self.stop_event = manager.Event()
        self.error_event = manager.Event()
        self.message_queue = manager.Queue()

    def close(self):
        pass

    def stop_on_error(self) -> None:
        self.error_event.set()
        self.stop_event.set()

    @property
    def error_occurred(self) -> bool:
        return self.error_event.is_set()

    @property
    def is_stopped(self) -> bool:
        return self.stop_event.is_set()

    def stop(self) -> None:
        self.stop_event.set()

    def wait(self):
        return self.stop_event.wait()


class Workers(object):
    LOG_LEVEL: int = logging.INFO

    def __init__(self):
        self.worker = None
        self.resources = None
        self.log = None
        self.method_name = None

    def _init_logger(self, logger_queue):
        set_workers_log(logger_queue, self.LOG_LEVEL)

    def init(self, worker: int, logger_queue: Queue, resources: SharedResources):
        self.worker = worker
        self.resources = resources
        self._init_logger(logger_queue)
        self.log = logging.getLogger('server')

    def on_start(self, **kwargs):
        pass

    def on_stop(self, **kwargs):
        pass

    def __call__(self, worker: int, logger_queue: Queue, resources: SharedResources, kwargs: dict):
        self.init(worker, logger_queue, resources)
        try:
            self.method_name = resources.message_queue.get_nowait()
        except Empty:
            self.log.warning(f'No methods left for the process.')
            return

        method = getattr(self, self.method_name, self.unknown_method)

        self.log.debug(f'Starting process for {self.method_name}')

        try:
            self.on_start(**kwargs)
            method(**kwargs)
            self.on_stop(**kwargs)
        except Exception as err:
            self.log.exception(err)
            self.resources.stop_on_error()

    def unknown_method(self, **kwargs):
        self.log.error('Unknown method called!')


@contextmanager
def run_pool(workers: Type[Workers],
             resources: SharedResources,
             worker_methods: List[str],
             **kwargs):
    with _set_logger_queue() as logger_queue:
        for method in worker_methods:
            resources.message_queue.put_nowait(method)
        processes = [
            Process(target=workers(),
                    args=(worker, logger_queue, resources, kwargs))
            for worker in range(len(worker_methods))
        ]

        sys.excepthook = _terminate_excepthook

        for p in processes:
            p.start()

        yield

        resources.stop_event.wait()

        if resources.error_occurred:
            terminate()

        while processes:
            processes.pop().join()

        resources.close()


@contextmanager
def _set_logger_queue():
    logger_queue = Queue()
    listener = threading.Thread(target=_logger_thread, args=(logger_queue,))
    listener.start()
    yield logger_queue

    logger_queue.put(None)

    if listener.is_alive():
        listener.join()


def _logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def _terminate_excepthook(exc_type, exc_value, exc_traceback):
    logger = logging.getLogger(__name__)
    logger.critical(f'Error occurred, terminate all the processes.', exc_info=(exc_type, exc_value, exc_traceback))

    terminate(logger=logger)
    sys.exit(-1)


def terminate(*, logger=None):
    logger = logger or logging.getLogger(__name__)

    for p in multiprocessing.active_children():
        logger.info(f'Kill Process(name={p.name}, pid={p.pid})')
        p.terminate()
    sys.exit(-1)
