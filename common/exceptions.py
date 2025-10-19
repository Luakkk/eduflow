import logging
from rest_framework.views import exception_handler
from django.utils.timezone import now

error_logger = logging.getLogger("app.error")

def rfc7807_exception_handler(exc, context):
    resp = exception_handler(exc, context)
    req = context.get("request")
    rid = getattr(req, "id", None)

    if resp is None:
        # Непойманные исключения — пусть Django залогирует, DRF вернет стандартный 500.
        error_logger.error("Unhandled exception", exc_info=True, extra={"request_id": rid})
        return None

    # Логируем ошибки прикладного уровня
    error_logger.error(
        f"Handled {resp.status_code}",
        exc_info=getattr(resp, "exception", False),
        extra={"request_id": rid}
    )

    detail = resp.data
    if isinstance(detail, list):
        detail = {"errors": detail}

    problem = {
        "type": f"https://httpstatuses.com/{resp.status_code}",
        "title": resp.status_text,
        "status": resp.status_code,
        "detail": detail,
        "instance": req.build_absolute_uri() if req else "",
        "timestamp": now().isoformat(),
        "request_id": rid,
    }
    resp.data = problem
    return resp
