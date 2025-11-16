import logging
import time
from django.utils.deprecation import MiddlewareMixin

access_logger = logging.getLogger("app.access")


class AccessLogMiddleware(MiddlewareMixin):
    """
    Logs each HTTP request in a structured JSON format (via JsonFormatter).

    Captured fields:
    - method
    - path
    - status
    - user_id
    - duration_ms
    - request_id (added by RequestIDMiddleware)
    """

    def process_request(self, request):
        # Fallback: if for some reason start_ts was not set by RequestIDMiddleware,
        # we initialize it here.
        if not hasattr(request, "start_ts"):
            request.start_ts = time.time()

    def process_response(self, request, response):
        request_id = getattr(request, "id", "-")
        user = getattr(request, "user", None)
        user_id = (
            getattr(user, "id", None)
            if user is not None and getattr(user, "is_authenticated", False)
            else None
        )

        duration_ms = None
        start_ts = getattr(request, "start_ts", None)
        if start_ts is not None:
            duration_ms = int((time.time() - start_ts) * 1000)

        access_logger.info(
            f"{request.method} {request.get_full_path()} -> {response.status_code}",
            extra={
                "request_id": request_id,
                "extra": {
                    "method": request.method,
                    "path": request.get_full_path(),
                    "status": response.status_code,
                    "user_id": user_id,
                    "duration_ms": duration_ms,
                },
            },
        )
        return response
