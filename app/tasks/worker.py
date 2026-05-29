import time
import uuid
from .queue import celery_app
from ..observability.logging import get_logger
from ..storage.db import update_task_status, add_task_event

logger = get_logger("tasks.worker")


@celery_app.task(bind=True)
def run_task(self, spec: dict):
    # use Celery task id as the canonical uuid
    task_id = str(self.request.id or uuid.uuid4())
    logger.info("Starting task %s spec=%s", task_id, spec)
    try:
        update_task_status(task_id, "running")
        add_task_event(task_id, "task_started", {"spec": spec})
    except Exception as exc:
        logger.exception("failed to mark running")
    # simple simulated long-running work with checkpoints
    steps = int(spec.get("steps", 3)) if isinstance(spec, dict) else 3
    for i in range(steps):
        logger.info("task %s step %s/%s", task_id, i + 1, steps)
        add_task_event(task_id, "task_step", {"step": i + 1, "steps": steps})
        time.sleep(1)
        # here we'd write checkpoints to DB or storage
    logger.info("task %s completed", task_id)
    try:
        update_task_status(task_id, "completed")
        add_task_event(task_id, "task_completed", {"result": "success"})
    except Exception as exc:
        logger.exception("failed to mark completed")
    return {"task_id": task_id, "status": "completed"}


if __name__ == "__main__":
    logger.info("Worker module loaded. Start a Celery worker to execute tasks.")
