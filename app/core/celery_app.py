from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    'g2i_api_proxy',
    broker=settings.REDIS_CONN_STRING,
    backend=settings.REDIS_CONN_STRING,
)

# Configure Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'update-devskiller-cookies': {
        'task': 'app.services.devskiller_tasks.update_cookies_task',
        'schedule': crontab(minute=0, hour='*/12'),  # Every 12 hours
    },
}

# Configure task time limits to prevent stuck tasks
celery_app.conf.task_time_limit = 300  # 5 minutes hard limit
celery_app.conf.task_soft_time_limit = 240  # 4 minutes soft limit

# Ensure tasks are registered
import app.services.devskiller_tasks 