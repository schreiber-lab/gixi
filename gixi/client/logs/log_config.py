import logging.config


__all__ = [
    'set_log_config',
]


_LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(module)s:%(funcName)s %(name)s: %(message)s'
        },
        'gui': {
            'format': '%(levelname)s %(asctime)s %(message)s',
            'datefmt': "%H:%M:%S",

        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'qt': {
            'level': 'INFO',
            'formatter': 'gui',
            'class': 'gixi.client.logs.log_handler.QtLogHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'qt'],
            'level': 'DEBUG',
            'propagate': True
        },
        '__main__': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        },
    }
}


def set_log_config():
    logging.config.dictConfig(_LOG_CONFIG)
