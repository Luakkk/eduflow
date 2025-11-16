import logging
from rest_framework.views import exception_handler
from django.utils.timezone import now

error_logger = logging.getLogger("app.error")


def rfc7807_exception_handler(exc, context):
    """
    Custom exception handler that produces RFC7807 Problem Details responses
    and logs all handled/unhandled errors in structured JSON format.
    """
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "id", None)

    if response is None:
        # Unhandled exceptions — let Django handle the traceback,
        # but still log them with request_id.
        error_logger.error(
            "Unhandled exception",
            exc_info=True,
            extra={"request_id": request_id}
        )
        return None

    # Log all handled application-level exceptions
    error_logger.error(
        f"Handled {response.status_code}",
        exc_info=getattr(response, "exception", False),
        extra={"request_id": request_id}
    )

    detail = response.data
    if isinstance(detail, list):
        detail = {"errors": detail}

    problem = {
        "type": f"https://httpstatuses.com/{response.status_code}",
        "title": response.status_text,
        "status": response.status_code,
        "detail": detail,
        "instance": request.build_absolute_uri() if request else "",
        "timestamp": now().isoformat(),
        "request_id": request_id,
    }

    response.data = problem
    return response
