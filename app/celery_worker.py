import os

from celery import Celery
from dotenv import load_dotenv


load_dotenv()


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


celery_app = Celery(
    "order_management_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"],
)


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)