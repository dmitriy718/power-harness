from typing import Optional

from .context import ContextAssembler
from ..agent.langgraph import LangGraphAdapter
from ..llm.langchain_adapter import make_chat_model
from ..memory.sqlite_store import SQLiteMemoryStore
from ..observability.logging import get_logger
from langchain_core.messages import AIMessage

logger = get_logger("agent.graph")

class NovaAgent:
    def __init__(self):
        self.memory_store = SQLiteMemoryStore()
        self.langgraph = LangGraphAdapter()
        self.chat_model = make_chat_model("main")
        self.context_assembler = ContextAssembler(memory_store=self.memory_store)

    def assemble_context(self, project_id: Optional[int], user_prompt: str) -> str:
        context = self.context_assembler.assemble(user_prompt, project_id=project_id, limit=5)
        memory_text = "\n".join([f"- {item['content']}" for item in context["memories"]])
        prompt = (
            "You are Nova Agent, a safe, reliable, and developer-focused AI assistant. "
            "Use the project context and memory to answer succinctly.\n\n"
        )
        if memory_text:
            prompt += f"Project memory:\n{memory_text}\n\n"
        prompt += f"User request:\n{user_prompt}\n\nAnswer:"
        return prompt

    def respond(self, user_prompt: str, project_id: Optional[int] = None) -> str:
        self.langgraph.create_event("prompt_received", {"project_id": project_id, "prompt": user_prompt})
        context_prompt = self.assemble_context(project_id, user_prompt)
        result = self.chat_model._generate([AIMessage(content=context_prompt)])
        text = result.generations[0].text
        self.memory_store.save_memory(project_id or 0, "dialogue", user_prompt, source="user")
        self.memory_store.save_memory(project_id or 0, "dialogue", text, source="assistant")
        self.langgraph.create_event("response_generated", {"project_id": project_id, "response": text})
        return text

    def summarize(self, text: str) -> str:
        summarization = make_chat_model("summarization")
        result = summarization._generate([AIMessage(content=text)])
        return result.generations[0].text
