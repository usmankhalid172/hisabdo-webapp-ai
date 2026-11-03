import json
import logging
import sys
import time


SAFE_FIELDS = {
    "event",
    "request_id",
    "method",
    "status_code",
    "duration_ms",
    "intent",
    "outcome",
    "source",
    "source_ids",
    "provider_name",
    "tokens_used",
    "retrieval_duration_ms",
    "provider_duration_ms",
    "error_category",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
        }

        for key in SAFE_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("hisabdo.ai")
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = configure_logging()


def timed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


