import json
import logging

logger = logging.getLogger("tsg")


def _to_json(message: str, **kwargs):
    return json.dumps({"message": message, **kwargs})


def log_info(message: str, **kwargs):
    logger.info(_to_json(message, **kwargs))


def log_error(message: str, **kwargs):
    logger.error(_to_json(message, **kwargs))
