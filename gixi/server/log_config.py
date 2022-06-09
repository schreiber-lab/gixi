import logging
import logging.config
from logging.handlers import QueueHandler

__all__ = ['set_log_config', 'set_workers_log']


def get_log_config(level) -> dict:
    return {
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
                'level': level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'server': {
                'level': level,
                'formatter': 'server',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            '': {
                'handlers': ['standard'],
                'level': level,
                'propagate': False,
            },
            '__main__': {
                'handlers': ['standard'],
                'level': level,
                'propagate': False,
            },
            'server': {
                'handlers': ['server'],
                'level': level,
                'propagate': False,
            },
        }
    }


def set_workers_log(logger_queue, level):
    log_config = get_log_config(level)
    standard_fmt = log_config['formatters']['standard']
    standard_fmt['fmt'] = standard_fmt.pop('format')
    fmt = logging.Formatter(**standard_fmt)

    qh = QueueHandler(logger_queue)
    qh.setFormatter(fmt)
    root = logging.getLogger('server')
    root.setLevel(level)
    root.addHandler(qh)


def set_log_config(level: int = logging.INFO):
    conf_dict = get_log_config(level)
    if level == logging.DEBUG:
        conf_dict['formatters']['standard'] = conf_dict['formatters']['standard_debug']

    logging.config.dictConfig(conf_dict)
    logging.getLogger(__name__).debug('log config is set')
