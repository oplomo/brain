
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for 'celery'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brain.settings")
br="redis://default:dswio7Vkn7NGhmOOC24HnZEmVKFIlbT2@redis-10456.c285.us-west-2-2.ec2.redns.redis-cloud.com:10456"
app = Celery("brain", broker=br)
# app = Celery("brain")

# Load task modules from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Ensure Celery discovers tasks in installed Django apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Use Redis from Upstash (Render environment variable)
app.conf.broker_url = os.getenv("REDIS_URL")
app.conf.result_backend = os.getenv("REDIS_URL")

# Celery Beat Schedule
app.conf.beat_schedule = {
    "update-fixtures-daily": {
        "task": "backend.tasks.run_fixtures_update",
        "schedule": crontab(minute="30", hour="*/2", day_of_week="*"),
    },
    "update-fix-every-4-minutes": {
        "task": "backend.tasks.update_matches_task",
        "schedule": crontab(minute="*/20"),
    },
}
