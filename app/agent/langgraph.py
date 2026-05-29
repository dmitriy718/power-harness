import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from langgraph_sdk import get_sync_client

from ..observability.logging import get_logger

logger = get_logger("agent.langgraph")

@dataclass
class LangGraphEvent:
    type: str
    payload: Dict[str, Any]


class LangGraphAdapter:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("LANGGRAPH_URL")
        self.client = None
        self.enabled = bool(self.base_url)
        if self.enabled:
            self.client = get_sync_client(url=self.base_url)
            logger.debug("LangGraph enabled at %s", self.base_url)
        else:
            logger.debug("LangGraph disabled; no LANGGRAPH_URL configured")

    def create_event(self, event_type: str, payload: Dict[str, Any]) -> LangGraphEvent:
        event = LangGraphEvent(type=event_type, payload=payload)
        logger.debug("LangGraph event: %s", event)
        return event

    def record(self, name: str, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        metadata = metadata or {}
        event = self.create_event(name, {"prompt": prompt, "metadata": metadata})
        logger.info("LangGraph recording event %s", event.type)

    def close(self) -> None:
        if self.client:
            self.client.close()
