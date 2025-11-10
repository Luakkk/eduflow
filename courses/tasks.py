from celery import shared_task
import time

@shared_task
def simulate_long_task(course_id):
    print(f"⏳ Начало фоновой задачи для курса {course_id}")
    time.sleep(5)
    print(f"✅ Задача для курса {course_id} завершена")
    return f"Курс {course_id} успешно обработан"
