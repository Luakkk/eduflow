
import logging

from celery import shared_task
from django.core.cache import cache

from courses.models import Enrollment

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_enrollment_email(self, enrollment_id: int):
    """
    Отправка письма после записи на курс.
    Сделана идемпотентной: один и тот же enrollment_id не обрабатывается дважды в течение часа.
    """
    key = f"task:send_email:{enrollment_id}"

    # cache.add вернет False, если ключ уже существует
    if not cache.add(key, "1", timeout=3600):
        logger.info("send_enrollment_email skipped, already processed: %s", enrollment_id)
        return

    try:
        enrollment = Enrollment.objects.select_related("course", "student").get(id=enrollment_id)
    except Enrollment.DoesNotExist:
        logger.warning("Enrollment %s does not exist", enrollment_id)
        return

    # тут могла бы быть реальная отправка email (SMTP, SendGrid и т.п.)
    logger.info(
        "Sending enrollment email: student=%s, course=%s",
        enrollment.student_id,
        enrollment.course_id,
    )


@shared_task
def generate_daily_report():
    """
    Ежедневный отчет: количество курсов и записей.
    Для диплома достаточно логировать.
    """
    from courses.models import Course, Enrollment  # импорт внутри, чтобы не ловить циклы

    courses_count = Course.objects.count()
    enrollments_count = Enrollment.objects.count()

    logger.info(
        "Daily report: total_courses=%s, total_enrollments=%s",
        courses_count,
        enrollments_count,
    )


@shared_task
def cleanup_abandoned_enrollments():
    """
    Пример фоновой задачи очистки "висячих" записей.
    Сейчас просто логируем как пример.
    Если введёшь статус draft — можно будет реально удалять.
    """
    logger.info("cleanup_abandoned_enrollments started (no-op for now)")