from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "docproc",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.document_processing"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30*60, # 30 minutes
    task_soft_time_limit=25*60, # 25 minutes
)