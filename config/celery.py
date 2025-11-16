# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# берём настройки, начинающиеся с CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# автоматический поиск tasks.py во всех установленных приложениях
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")