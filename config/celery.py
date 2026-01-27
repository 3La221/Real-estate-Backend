"""
Celery configuration for Django project.
"""
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')


app.config_from_object('django.conf:settings', namespace='CELERY')


app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):

    print(f'Request: {self.request!r}')


# Periodic tasks configuration (optional examples)
app.conf.beat_schedule = {
    # Example: Run every day at midnight
    'cleanup-expired-sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=0, minute=0),
    },
    # Example: Run every 30 minutes
    # 'send-notification-reminders': {
    #     'task': 'apps.notifications.tasks.send_reminders',
    #     'schedule': crontab(minute='*/30'),
    # },
}
