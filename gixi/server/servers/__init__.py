import logging

from .single_threaded_server import SingleThreadedServer
from .multi_threaded_server import MultiThreadedServer
from .basicserver import BasicServer

from ..app_config import AppConfig


def run_server(app_config: AppConfig):
    logging.getLogger(__name__).info(f'Start server from config: {app_config}.')

    if app_config.parallel.parallel_computation:
        server = MultiThreadedServer(app_config)
    else:
        server = SingleThreadedServer(app_config)

    server.run()
