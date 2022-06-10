import logging
import logging.config

__all__ = [
    'set_log_config',
]


def _get_log_config(level, filename: str = None) -> dict:
    if level in (logging.DEBUG, 'DEBUG'):
        fmt = 'debug'
    else:
        fmt = 'standard'

    if filename:
        handlers = ['file', 'console']
    else:
        handlers = ['console']

    return {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'debug': {
                'format': '%(levelname)s %(asctime)s.%(msecs)03d %(filename)s:%(lineno)s'
                          ' %(funcName)s(%(process)s): %(message)s',
                'datefmt': "%H:%M:%S",
            },
            'standard': {
                'format': '%(asctime)s.%(msecs)03d : %(message)s',
                'datefmt': "%H:%M:%S",
            },
        },
        'handlers': {
            'console': {
                'formatter': fmt,
                'level': level,
                'class': 'logging.StreamHandler',
            },
            'file': {
                'formatter': fmt,
                'level': level,
                'class': 'logging.FileHandler',
                'filename': filename,
                'mode': 'w',
            },
        },
        'loggers': {
            '': {
                'handlers': handlers,
                'level': level,
                'propagate': False,
            },
            '__main__': {
                'handlers': handlers,
                'level': level,
                'propagate': False,
            },
        }
    }


def set_log_config(level: int = logging.INFO, filename: str = None):
    logging.config.dictConfig(_get_log_config(level, filename=filename))
    logging.getLogger(__name__).debug(f'log config is set with level={level} and filename={filename}.')
