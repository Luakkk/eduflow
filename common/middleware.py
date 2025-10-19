import logging
from django.utils.deprecation import MiddlewareMixin

access_logger = logging.getLogger("app.access")

class AccessLogMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        rid = getattr(request, "id", "-")
        user = getattr(request, "user", None)
        uid = getattr(user, "id", None) if user and user.is_authenticated else None

        access_logger.info(
            f"{request.method} {request.get_full_path()} -> {response.status_code}",
            extra={"request_id": rid, "extra": {
                "method": request.method,
                "path": request.get_full_path(),
                "status": response.status_code,
                "user_id": uid,
            }},
        )
        return response
