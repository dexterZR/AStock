import logging.config
import os

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        },
    },
    "loggers": {
        "app": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "app.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "motor": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
