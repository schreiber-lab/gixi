import logging
import logging.config
from logging.handlers import QueueHandler

__all__ = ['set_log_config', 'set_workers_log']

_LOG_CONFIG: dict = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'server': {
            'format': '%(message)s',
        },
        'standard_debug': {
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
        'standard': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'server': {
            'level': 'INFO',
            'formatter': 'server',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['standard'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '__main__': {
            'handlers': ['standard'],
            'level': 'INFO',
            'propagate': False,
        },
        'server': {
            'handlers': ['server'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}


def set_workers_log(logger_queue, level):
    standard_fmt = dict(_LOG_CONFIG['formatters']['standard'])
    standard_fmt['fmt'] = standard_fmt.pop('format')
    fmt = logging.Formatter(**standard_fmt)

    qh = QueueHandler(logger_queue)
    qh.setFormatter(fmt)
    root = logging.getLogger('server')
    root.setLevel(level)
    root.addHandler(qh)


def set_log_config():
    logging.config.dictConfig(_LOG_CONFIG)
    logging.getLogger(__name__).debug('log config is set')
