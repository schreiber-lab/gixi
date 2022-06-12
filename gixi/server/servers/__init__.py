import logging

from gixi.server.log_config import set_log_config
from gixi.server.app_config import AppConfig

from .single_process_server import SingleProcessServer
from .multi_process_server import MultiProcessServer
from .basicserver import BasicServer


def run_server(app_config: AppConfig):
    set_log_config(app_config.log_config.logging_level, app_config.log_filename)
    logging.getLogger(__name__).info(f'Starting server from config: {app_config.job_config.config_path}.')

    if app_config.parallel.parallel_computation:
        server = MultiProcessServer(app_config)
    else:
        server = SingleProcessServer(app_config)

    server.run()
