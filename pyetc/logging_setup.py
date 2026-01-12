import logging
import logging.config

_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(name)s:%(lineno)s %(funcName)s:%(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

logger = logging.getLogger(__name__)
logging.config.dictConfig(_LOGGING)


def setup():
    logger.info("Setup OK.")
