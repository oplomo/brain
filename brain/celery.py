from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for 'celery'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brain.settings")

app = Celery("brain")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Celery Beat schedule for running the task daily at 23:59 UTC
app.conf.beat_schedule = {
    "update-fixtures-daily": {
        "task": "backend.tasks.run_fixtures_update",  # Task path in square app
        "schedule": crontab(minute="30", hour="*/2", day_of_week="*"),
    },
    "update-fix-every-4-minutes": {
        "task": "backend.tasks.update_matches_task",
        "schedule": crontab(minute="*/4"),  # Every 4 minutes
    },
}
