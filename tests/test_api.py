from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_memory_save_and_search_api():
    # save
    r = client.post("/memory/save", json={"project_id": 1, "kind": "episodic", "content": "Remember the blue widget design."})
    assert r.status_code == 200
    mid = r.json().get("id")
    assert isinstance(mid, int)
    # search
    r2 = client.post("/memory/search", json={"q": "blue widget"})
    assert r2.status_code == 200
    assert isinstance(r2.json().get("results"), list)


def test_tools_list():
    r = client.get("/tools/list")
    assert r.status_code == 200
    assert isinstance(r.json().get("tools"), list)


def test_workflow_endpoint_can_run_tool_and_generate_reply():
    response = client.post(
        "/workflow",
        json={
            "prompt": "List the repository files and summarize the result.",
            "project_id": 1,
            "tool": "list_files",
            "tool_args": ["."],
            "approval": True,
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert "reply" in result
    assert "tool_result" in result
    assert isinstance(result["tool_result"], list)
