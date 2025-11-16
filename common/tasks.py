import logging

from celery import shared_task
from django.core.cache import cache

from courses.models import Enrollment

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_enrollment_email(self, enrollment_id: int):
    """
    Send a notification after a student enrolls into a course.

    Idempotent: the same enrollment_id will not be processed twice within one hour.
    """
    cache_key = f"task:send_email:{enrollment_id}"

    # cache.add returns False if the key already exists
    if not cache.add(cache_key, "1", timeout=3600):
        logger.info(
            "send_enrollment_email skipped, already processed: %s",
            enrollment_id,
        )
        return

    try:
        enrollment = (
            Enrollment.objects
            .select_related("course", "student")
            .get(id=enrollment_id)
        )
    except Enrollment.DoesNotExist:
        logger.warning("Enrollment %s does not exist", enrollment_id)
        return

    # Demo implementation: just log instead of sending a real email
    logger.info(
        "Sending enrollment email (demo): student_id=%s, course_id=%s",
        enrollment.student_id,
        enrollment.course_id,
    )


@shared_task
def generate_daily_report():
    """
    Demo daily report: logs total number of courses and enrollments.
    """
    from courses.models import Course, Enrollment  # imported here to avoid circular imports

    courses_count = Course.objects.count()
    enrollments_count = Enrollment.objects.count()

    logger.info(
        "Daily report (demo): total_courses=%s, total_enrollments=%s",
        courses_count,
        enrollments_count,
    )


@shared_task
def cleanup_abandoned_enrollments():
    """
    Demo cleanup task for abandoned enrollments.

    Currently a no-op that only logs its execution.
    """
    logger.info("cleanup_abandoned_enrollments started (demo, no-op)")
