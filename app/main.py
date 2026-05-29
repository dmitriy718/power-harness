from contextlib import asynccontextmanager
import sqlite3
import uuid as _uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .observability.logging import get_logger
from .storage.db import DB_PATH, init_db, insert_task, get_task, update_task_status, add_tool_call, add_task_event
from .tools import registry as tools_registry
from .memory import sqlite_store
from .tasks.worker import run_task
from .tasks.queue import celery_app
from .agent.graph import NovaAgent

logger = get_logger()

@asynccontextmanager
def lifespan(app: FastAPI):
    logger.info("Initializing DB")
    init_db()
    yield

app = FastAPI(title="Nova Agent Runtime", lifespan=lifespan)

agent = NovaAgent()


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/metrics")
async def metrics():
    return JSONResponse({"uptime": 0})


@app.post("/chat")
async def chat(payload: Dict[str, Any]):
    project_id = payload.get("project_id")
    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="message required")
    try:
        reply = agent.respond(message, project_id=project_id)
    except Exception as exc:
        logger.exception("Agent response failed")
        raise HTTPException(status_code=500, detail=str(exc))
    return {"reply": reply, "echo": message}


@app.post("/tasks")
async def create_task(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    spec = payload.get("spec") or payload
    uid = str(_uuid.uuid4())
    project_id = payload.get("project_id") or 0
    user_id = payload.get("user_id") or 0
    # persist task
    insert_task(uid, project_id, user_id, "queued", str(spec))
    add_task_event(uid, "task_created", {"spec": spec, "project_id": project_id, "user_id": user_id})
    # enqueue worker task
    try:
        run_task.apply_async(args=(spec,), task_id=uid)
        update_task_status(uid, "queued")
    except Exception as exc:
        logger.exception("Failed to enqueue task")
        update_task_status(uid, "failed")
        add_task_event(uid, "task_enqueue_failed", {"error": "enqueue failed"})
        raise HTTPException(status_code=500, detail=str(exc))
    return {"task_id": uid, "status": "queued"}


@app.get("/tasks/{task_id}")
async def read_task(task_id: str):
    t = get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task not found")
    # attempt to get celery state
    try:
        res = celery_app.AsyncResult(task_id)
        state = res.state
    except Exception as exc:
        logger.exception("Failed to retrieve Celery state")
        state = t.get("status")
    return {"task": t, "state": state}


@app.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    t = get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task not found")
    # simple resume strategy: enqueue a new task with same spec
    spec = t.get("spec")
    try:
        run_task.apply_async(args=(spec,), task_id=task_id)
        update_task_status(task_id, "resumed")
        add_task_event(task_id, "task_resumed", {"spec": spec})
    except Exception as exc:
        logger.exception("Failed to resume task")
        update_task_status(task_id, "failed")
        add_task_event(task_id, "task_resume_failed", {"error": "resume failed"})
        raise HTTPException(status_code=500, detail=str(exc))
    return {"task_id": task_id, "status": "resumed"}


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    try:
        celery_app.control.revoke(task_id, terminate=True)
        add_task_event(task_id, "task_cancelled", {"revoked": True})
    except Exception as exc:
        logger.exception("Revoke failed")
        add_task_event(task_id, "task_cancel_failed", {"error": str(exc)})
    update_task_status(task_id, "cancelled")
    return {"task_id": task_id, "status": "cancelled"}


@app.get("/tasks/{task_id}/logs")
async def task_logs(task_id: str):
    t = get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task not found")
    # fetch tool_calls and events
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT tc.* FROM tool_calls tc JOIN tasks t ON tc.task_id = t.id WHERE t.uuid = ? ORDER BY tc.id ASC", (task_id,))
    calls = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM task_events WHERE task_id = (SELECT id FROM tasks WHERE uuid = ?) ORDER BY id ASC", (task_id,))
    events = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"tool_calls": calls, "events": events}


@app.post("/memory/save")
async def memory_save(payload: Dict[str, Any]):
    project_id = payload.get("project_id") or 0
    kind = payload.get("kind") or "episodic"
    content = payload.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content required")
    mid = sqlite_store.SQLiteMemoryStore().save_memory(project_id, kind, content)
    return {"id": mid}


@app.post("/memory/search")
async def memory_search(payload: Dict[str, Any]):
    q = payload.get("q") or payload.get("query")
    if not q:
        raise HTTPException(status_code=400, detail="query required")
    res = sqlite_store.SQLiteMemoryStore().search(q)
    return {"results": res}


@app.get("/memory/list")
async def memory_list(project_id: Optional[int] = None):
    res = sqlite_store.SQLiteMemoryStore().list(project_id)
    return {"results": res}


@app.delete("/memory/{memory_id}")
async def memory_delete(memory_id: int):
    sqlite_store.SQLiteMemoryStore().delete(memory_id)
    return {"ok": True}


@app.post("/tools/run")
async def tools_run(payload: Dict[str, Any]):
    name = payload.get("name")
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    approval = payload.get("approval", False)
    task_uuid = payload.get("task_id")
    if not name:
        raise HTTPException(status_code=400, detail="tool name required")
    try:
        out = tools_registry.run(name, *args, approval=approval, **kwargs)
        # audit
        try:
            if task_uuid:
                add_tool_call(task_uuid, name, str({"args": args, "kwargs": kwargs}), str(out))
        except Exception as exc:
            logger.exception("audit write failed")
        return {"ok": True, "output": out}
    except KeyError:
        raise HTTPException(status_code=404, detail="tool not found")
    except PermissionError as e:
        logger.warning("tool approval required: %s", name)
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as exc:
        logger.exception("tool run failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tools/list")
async def tools_list():
    return {"tools": list(tools_registry.tools.keys())}


@app.post("/workflow")
async def workflow(payload: Dict[str, Any]):
    prompt = payload.get("prompt")
    project_id = payload.get("project_id")
    tool_name = payload.get("tool")
    tool_args = payload.get("tool_args", [])
    tool_kwargs = payload.get("tool_kwargs", {})
    approval = payload.get("approval", False)
    task_uuid = payload.get("task_id")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt required")
    if task_uuid:
        add_task_event(task_uuid, "workflow_started", {"prompt": prompt, "tool": tool_name, "project_id": project_id})
    tool_result = None
    if tool_name:
        try:
            tool_result = tools_registry.run(tool_name, *tool_args, approval=approval, **tool_kwargs)
            if task_uuid:
                add_tool_call(task_uuid, tool_name, str({"args": tool_args, "kwargs": tool_kwargs}), str(tool_result))
                add_task_event(task_uuid, "tool_executed", {"tool": tool_name, "result": str(tool_result)})
        except KeyError:
            raise HTTPException(status_code=404, detail="tool not found")
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as exc:
            logger.exception("workflow tool failed")
            raise HTTPException(status_code=500, detail=str(exc))
    try:
        reply = agent.respond(prompt, project_id=project_id)
    except Exception as exc:
        logger.exception("Workflow response failed")
        raise HTTPException(status_code=500, detail=str(exc))
    if task_uuid:
        add_task_event(task_uuid, "workflow_completed", {"reply": reply})
    return {"reply": reply, "tool_result": tool_result}


@app.post("/embeddings/index")
async def embeddings_index(payload: Dict[str, Any]):
    collection = payload.get("collection")
    texts = payload.get("texts")
    ids = payload.get("ids")
    project_id = payload.get("project_id")
    if not collection or not texts:
        raise HTTPException(status_code=400, detail="collection and texts required")
    try:
        from .memory.embeddings_pipeline import index_texts

        ok = index_texts(collection, texts, ids=ids, project_id=project_id)
        return {"ok": bool(ok)}
    except Exception as exc:
        logger.exception("embeddings index failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/embeddings/query")
async def embeddings_query(payload: Dict[str, Any]):
    collection = payload.get("collection")
    query = payload.get("query")
    top_k = int(payload.get("top_k", 5))
    if not collection or not query:
        raise HTTPException(status_code=400, detail="collection and query required")
    try:
        from .memory.embeddings_pipeline import query_similar

        res = query_similar(collection, query, top_k=top_k)
        return {"results": res}
    except Exception as exc:
        logger.exception("embeddings query failed")
        raise HTTPException(status_code=500, detail=str(exc))

