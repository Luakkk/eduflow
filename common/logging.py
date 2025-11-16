import json, logging, time, uuid
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

class JsonFormatter(logging.Formatter):
    SENSITIVE_KEYS = {"password", "token", "access", "refresh", "authorization"}

    def format(self, record):
        base = {
            "timestamp": now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "request_id"):
            base["request_id"] = record.request_id

        # Sanitize and attach extra fields if present
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            sanitized = {}
            for key, value in extra.items():
                if isinstance(key, str) and key.lower() in self.SENSITIVE_KEYS:
                    sanitized[key] = "***"
                else:
                    sanitized[key] = value
            base["extra"] = sanitized
        elif extra is not None:
            base["extra"] = extra

        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False)


class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.id = str(uuid.uuid4())
        request.start_ts = time.time()
    def process_response(self, request, response):
        try:
            duration_ms = int((time.time() - request.start_ts) * 1000)
            response["X-Request-ID"] = getattr(request, "id", "-")
            response["X-Response-Time-ms"] = str(duration_ms)
        except Exception:
            pass
        return response

def json_logging_config(debug: bool = False):
    level = "DEBUG" if debug else "INFO"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {"console": {"class": "logging.StreamHandler","formatter": "json","level": level}},
        "loggers": {
            "django.request": {"handlers": ["console"], "level": level, "propagate": False},
            "django": {"handlers": ["console"], "level": level, "propagate": False},
            "app.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "app.error": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        },
        "root": {"handlers": ["console"], "level": level},
    }
