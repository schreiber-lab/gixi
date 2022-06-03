from argparse import ArgumentParser
from time import perf_counter
import logging

from .servers import run_server
from .app_config import AppConfig


def run(config_file: str = None):
    start = perf_counter()
    config_file = config_file or parse_args()
    app_config = AppConfig.from_config(config_file)
    run_server(app_config)
    logging.getLogger(__name__).warning(f'Total time (sec): {(perf_counter() - start)}')


def parse_args() -> str:
    parser = ArgumentParser(description='Start simple maxwell server on a cluster node')
    parser.add_argument('config_file', type=str, help='Config file name')

    args = parser.parse_args()

    return args.config_file
