from fastapi.testclient import TestClient
from app.main import app
from app.tasks.queue import celery_app
import time

client = TestClient(app)


def test_long_running_task_and_resume():
    # run tasks synchronously in the test process
    celery_app.conf.task_always_eager = True

    # create task via API
    resp = client.post("/tasks", json={"spec": {"steps": 1}, "project_id": 42, "user_id": 99})
    assert resp.status_code == 200
    task_id = resp.json().get("task_id")
    assert isinstance(task_id, str)

    # wait a moment for eager task to complete
    time.sleep(0.1)

    # check logs contain lifecycle events
    logs = client.get(f"/tasks/{task_id}/logs").json()
    event_types = [e.get("event_type") for e in logs.get("events", [])]
    assert "task_created" in event_types
    assert "task_started" in event_types
    assert "task_completed" in event_types

    # trigger resume (should re-enqueue and run)
    resume_resp = client.post(f"/tasks/{task_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json().get("status") == "resumed"

    # wait for resumed run
    time.sleep(0.1)

    logs2 = client.get(f"/tasks/{task_id}/logs").json()
    event_types2 = [e.get("event_type") for e in logs2.get("events", [])]
    assert "task_resumed" in event_types2
    # ensure we have at least two completed events (original + resumed)
    assert event_types2.count("task_completed") >= 2
