from typing import Any, Dict, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: Optional[int]
    project_id: Optional[int]
    thread_id: Optional[str]
    message: str
    context: Optional[Dict[str, Any]] = None

class TaskCreate(BaseModel):
    user_id: Optional[int]
    project_id: Optional[int]
    spec: Dict[str, Any]

class TaskStatus(BaseModel):
    task_id: str
    status: str

class MemoryItem(BaseModel):
    id: Optional[int]
    project_id: Optional[int]
    kind: str
    content: str
    score: Optional[float]

