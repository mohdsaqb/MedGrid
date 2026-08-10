"""
Structured (JSON) application logging.

Every log line is one JSON object - machine-parseable, so a real deployment
can ship these to a log aggregator (CloudWatch, Datadog, etc.) and query/
filter/alert on fields, instead of grepping free-text strings.

HARD RULE, enforced by convention throughout this file and everywhere
logger calls are added: never log a password, a hashed password, a JWT,
or SECRET_KEY. Log identifying context (email, ids, paths) - never secrets.
"""

import json
import logging
from datetime import datetime, timezone

# Fields every LogRecord already carries - used to find the EXTRA fields a
# caller added via logger.info(..., extra={...}), which we want to fold
# into the JSON output.
_STANDARD_FIELDS = set(
    logging.LogRecord(name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None).__dict__.keys()
) | {"message"}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_FIELDS:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(environment: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    # DEBUG locally so you see everything while developing; INFO in
    # anything else, so production logs aren't drowned in noise.
    root.setLevel(logging.DEBUG if environment == "development" else logging.INFO)

    # Quiet down noisy third-party loggers that aren't useful at INFO.
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
