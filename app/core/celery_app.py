from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'g2i_api_proxy',
    broker=settings.REDIS_CONN_STRING,
    backend=settings.REDIS_CONN_STRING,
)

# Ensure tasks are registered
import app.services.devskiller_tasks

# Ensure tasks are registered
import app.services.devskiller_tasks 