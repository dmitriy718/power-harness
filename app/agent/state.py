from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class TaskState:
    task_id: str
    status: str = "queued"
    plan: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)

    def checkpoint(self, note: str):
        self.logs.append(note)

