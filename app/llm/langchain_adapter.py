from typing import Any, Dict, List, Optional

from pydantic import PrivateAttr
from langchain.chat_models.base import BaseChatModel
from langchain.embeddings.base import Embeddings
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs.chat_generation import ChatGeneration
from langchain_core.outputs.chat_result import ChatResult

from .provider import BaseProvider, get_provider


def _flatten_message_text(messages: List[List[Dict[str, Any]]]) -> str:
    parts: List[str] = []
    for group in messages:
        for message in group:
            role = message.get("type", message.get("role", "user"))
            content = message.get("content", "")
            if isinstance(content, list):
                content = "\n".join(str(item) for item in content)
            parts.append(f"{role}: {content}")
    return "\n".join(parts)


class NovaChatModel(BaseChatModel):
    _provider: BaseProvider = PrivateAttr()
    _model_type: str = PrivateAttr()
    _model: str = PrivateAttr()

    def __init__(self, provider: Optional[BaseProvider] = None, model_type: str = "main", **kwargs: Any):
        super().__init__(**kwargs)
        provider = provider or get_provider()
        object.__setattr__(self, "_provider", provider)
        object.__setattr__(self, "_model_type", model_type)
        model = self._provider.get_model(model_type)
        if not model:
            raise ValueError(f"No model configured for {model_type}")
        object.__setattr__(self, "_model", model)

    @property
    def _llm_type(self) -> str:
        return "nova"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt_text = _flatten_message_text(
            [[{"type": getattr(msg, 'type', getattr(msg, 'role', 'user')), "content": getattr(msg, 'content', '')} for msg in messages]]
        )
        result = self._provider.request_chat(
            [
                {"type": "system", "content": "You are Nova Agent, a safe, reliable, and developer-focused AI assistant."},
                {"type": "user", "content": prompt_text},
            ],
            self._model,
            stop=stop,
            **kwargs,
        )
        message = AIMessage(content=result)
        generation = ChatGeneration(text=result, message=message)
        return ChatResult(generations=[generation], llm_output={"model": self._model, "provider": self._provider.provider})


class NovaEmbeddings(Embeddings):
    _provider: BaseProvider = PrivateAttr()
    _model: str = PrivateAttr()

    def __init__(self, provider: Optional[BaseProvider] = None, model_type: str = "embeddings", **kwargs: Any):
        super().__init__(**kwargs)
        provider = provider or get_provider()
        object.__setattr__(self, "_provider", provider)
        object.__setattr__(self, "_model", self._provider.get_model(model_type))

    def embed_documents(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        return self._provider.request_embeddings(texts, self._model, **kwargs)

    def embed_query(self, text: str, **kwargs: Any) -> List[float]:
        embeddings = self._provider.request_embeddings([text], self._model, **kwargs)
        return embeddings[0] if embeddings else []


def make_chat_model(model_type: str = "main") -> NovaChatModel:
    return NovaChatModel(model_type=model_type)


def make_embeddings(model_type: str = "embeddings") -> NovaEmbeddings:
    return NovaEmbeddings(model_type=model_type)
