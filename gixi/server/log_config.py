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

    handlers = {
        'console': {
            'formatter': fmt,
            'level': level,
            'class': 'logging.StreamHandler',
        },
        'file': {
            'formatter': fmt,
            'level': level,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': filename,
            'mode': 'w',
        },
    }

    if not filename:
        handlers.pop('file')

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
                'format': '%(levelname)s %(asctime)s.%(msecs)03d : %(message)s',
                'datefmt': "%H:%M:%S",
            },
        },
        'handlers': handlers,
        'loggers': {
            '': {
                'handlers': list(handlers.keys()),
                'level': level,
                'propagate': False,
            },
            '__main__': {
                'handlers': list(handlers.keys()),
                'level': level,
                'propagate': False,
            },
        }
    }


def set_log_config(level: int = logging.INFO, filename: str = None):
    log_config = _get_log_config(level, filename=filename)
    logging.config.dictConfig(log_config)
    logging.getLogger(__name__).debug(f'log config is set with level={level} and filename={filename}.')
