import logging
from typing import Any, Dict, Optional

DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "formatter": "default",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "app": {"handlers": ["console"], "level": "INFO"},
        "uvicorn": {"handlers": ["console"], "level": "INFO"},
        "fastapi": {"handlers": ["console"], "level": "INFO"},
    },
    "root": {"level": "INFO", "handlers": ["console"], "propagate": True},
}


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name, configured according to application settings.
    """
    return logging.getLogger(name)