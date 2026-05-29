from typing import Dict, Any, Optional

class ContextAssembler:
    def __init__(self, memory_store=None):
        self.memory_store = memory_store

    def assemble(self, user_request: str, project_id: Optional[int] = None, limit: int = 5) -> Dict[str, Any]:
        context = {"request": user_request, "memories": []}
        if self.memory_store and project_id is not None:
            memories = self.memory_store.list(project_id)
            ordered = sorted(memories, key=lambda item: item.get("created_at", ""), reverse=True)
            context["memories"] = ordered[:limit]
        return context
