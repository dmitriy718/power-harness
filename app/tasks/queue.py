import os
from celery import Celery
from ..config import settings

BROKER = os.environ.get("REDIS_URL", settings.redis_url)
BACKEND = BROKER

celery_app = Celery("nova_agent", broker=BROKER, backend=BACKEND)
celery_app.conf.task_routes = {"app.tasks.worker.run_task": {"queue": "nova"}}
