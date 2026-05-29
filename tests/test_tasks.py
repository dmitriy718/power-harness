from fastapi.testclient import TestClient
from app.main import app
from app.tasks.queue import celery_app
import json

client = TestClient(app)


def test_task_creation_and_event_logging():
    celery_app.conf.task_always_eager = True
    response = client.post(
        "/tasks",
        json={"spec": {"steps": 1}, "project_id": 7, "user_id": 8},
    )
    assert response.status_code == 200
    task_id = response.json().get("task_id")
    assert isinstance(task_id, str)

    state_response = client.get(f"/tasks/{task_id}")
    assert state_response.status_code == 200
    assert state_response.json().get("state") in {"SUCCESS", "COMPLETED", "QUEUED", "RUNNING", "queued"}

    logs_response = client.get(f"/tasks/{task_id}/logs")
    assert logs_response.status_code == 200
    logs = logs_response.json()
    assert isinstance(logs.get("events"), list)
    event_types = {event.get("event_type") for event in logs.get("events", [])}
    assert "task_created" in event_types
    assert "task_started" in event_types
    assert "task_completed" in event_types
    created_event = next(event for event in logs["events"] if event.get("event_type") == "task_created")
    assert json.loads(created_event.get("payload") or "{}").get("project_id") == 7
