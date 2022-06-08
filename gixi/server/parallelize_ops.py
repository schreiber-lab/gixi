from typing import List, Type
import logging
import threading
from contextlib import contextmanager
from multiprocessing import Queue, Process

from gixi.server.log_config import set_workers_log


class SharedResources(object):
    def __init__(self, manager):
        self.stop_event = manager.Event()
        self.message_queue = manager.Queue()

    def close(self):
        pass

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

    def _init_logger(self, logger_queue):
        set_workers_log(logger_queue, self.LOG_LEVEL)

    def init(self, worker: int, logger_queue: Queue, resources: SharedResources):
        self.worker = worker
        self.resources = resources
        self._init_logger(logger_queue)
        self.log = logging.getLogger('server')

    def __call__(self, worker: int, logger_queue: Queue, resources: SharedResources, kwargs: dict):
        self.init(worker, logger_queue, resources)
        method_name = resources.message_queue.get_nowait()
        method = getattr(self, method_name, self.unknown_method)
        self.log.info(f'Starting method {method_name} ... ')
        method(**kwargs)

    def unknown_method(self, **kwargs):
        self.log.error('Unknown method called!')


@contextmanager
def run_pool(workers: Type[Workers],
             resources: SharedResources,
             worker_methods: List[str], **kwargs):
    with _set_logger_queue() as logger_queue:
        for method in worker_methods:
            resources.message_queue.put_nowait(method)
        processes = [
            Process(target=workers(),
                    args=(worker, logger_queue, resources, kwargs))
            for worker in range(len(worker_methods))
        ]

        for p in processes:
            p.start()

        yield

        resources.stop_event.wait()

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
    listener.join()


def _logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)
