import json
import logging
from typing import Optional


def build_logger() -> logging.Logger:
    logger = logging.getLogger("voice_agent")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_request(logger: logging.Logger, endpoint: str, trace_id: str, session_id: Optional[str], lang: Optional[str]):
    payload = {
        "event": "request",
        "endpoint": endpoint,
        "trace_id": trace_id,
        "session_id": session_id,
        "lang": lang,
    }
    logger.info(json.dumps(payload))
