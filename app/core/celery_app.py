from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from urllib.parse import urlparse

# Parse Redis URL to avoid connection issues with Railway Redis
def parse_redis_url(redis_url):
    if not redis_url:
        return redis_url
    
    try:
        parsed = urlparse(redis_url)
        # Reconstruct URL with explicit parameters for better compatibility
        return f"redis://:{parsed.password}@{parsed.hostname}:{parsed.port or 6379}/0"
    except Exception:
        # Fallback to original URL if parsing fails
        return redis_url

# Use parsed Redis URL for better Railway compatibility
redis_broker_url = parse_redis_url(settings.REDIS_CONN_STRING)

celery_app = Celery(
    'g2i_api_proxy',
    broker=redis_broker_url,
    backend=redis_broker_url,
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

# Redis connection settings for better stability
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.broker_connection_retry = True
celery_app.conf.broker_connection_max_retries = 10
celery_app.conf.broker_transport_options = {
    'visibility_timeout': 3600,  # 1 hour
    'fanout_prefix': True,
    'fanout_patterns': True,
    'socket_timeout': 10.0,
    'socket_connect_timeout': 10.0,
    'connection_pool_kwargs': {
        'decode_responses': False,
    }
}

# Result backend settings
celery_app.conf.result_backend_transport_options = {
    'socket_timeout': 10.0,
    'socket_connect_timeout': 10.0,
    'decode_responses': False,
}

# Worker settings to handle connection loss
celery_app.conf.worker_cancel_long_running_tasks_on_connection_loss = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_max_tasks_per_child = 1000

# Task settings
celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True

# Ensure tasks are registered
import app.services.devskiller_tasks 