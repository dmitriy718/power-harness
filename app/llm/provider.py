import os
import requests
from typing import Any, Dict, List, Optional

from ..config import settings
from ..observability.logging import get_logger

logger = get_logger("llm.provider")

ModelTask = str

DEFAULT_MODEL_MAP = {
    "main": "MAIN_MODEL",
    "coding": "CODING_MODEL",
    "summarization": "SUMMARIZATION_MODEL",
    "embeddings": "EMBEDDING_MODEL",
    "tool": "TOOL_MODEL",
    "memory": "MEMORY_MODEL",
}

class ProviderError(Exception):
    pass


def _env_model(task_type: str, prefix: str, default: Optional[str] = None) -> Optional[str]:
    key = DEFAULT_MODEL_MAP.get(task_type, None)
    if key is None:
        return default
    model = os.getenv(f"{prefix}_{key}") or os.getenv(key)
    return model or default


class BaseProvider:
    def __init__(self):
        self.provider = settings.provider.lower()
        self.ollama_base_url = settings.ollama_base_url
        self.openai_api_key = settings.openai_api_key
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", self.openai_base_url)
        self.custom_base_url = os.getenv("CUSTOM_BASE_URL")

    def get_model(self, task_type: str) -> Optional[str]:
        if self.provider == "ollama":
            model = _env_model(task_type, "OLLAMA", settings.ollama_model)
        elif self.provider == "openai":
            model = _env_model(task_type, "OPENAI", settings.openai_model)
        elif self.provider == "openrouter":
            model = _env_model(task_type, "OPENROUTER", settings.openai_model)
        elif self.provider == "custom":
            model = _env_model(task_type, "CUSTOM", settings.openai_model)
        else:
            model = _env_model(task_type, "OPENAI", settings.openai_model)

        if model is None and settings.dry_run:
            logger.warning("No model configured for %s; using dry-run placeholder model", task_type)
            return "dry-run"
        return model

    def _normalize_messages(self, messages: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for msg_group in messages:
            for msg in msg_group:
                if isinstance(msg.get("content"), list):
                    text = "\n".join(str(i) for i in msg["content"])
                else:
                    text = str(msg.get("content", ""))
                out.append({"role": msg.get("type", "user"), "content": text})
        return out

    def request_chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
        if self.provider == "ollama":
            return self._ollama_chat(messages, model, **kwargs)
        if self.provider == "openai":
            return self._openai_chat(messages, model, **kwargs)
        if self.provider == "openrouter":
            return self._openai_chat(messages, model, base_url=self.openrouter_base_url, api_key=os.getenv("OPENROUTER_API_KEY"), **kwargs)
        if self.provider == "custom":
            return self._openai_chat(messages, model, base_url=self.custom_base_url or self.openai_base_url, api_key=os.getenv("CUSTOM_API_KEY"), **kwargs)
        return self._openai_chat(messages, model, **kwargs)

    def request_embeddings(self, texts: List[str], model: str, **kwargs) -> List[List[float]]:
        if self.provider == "ollama":
            return self._ollama_embeddings(texts, model, **kwargs)
        if self.provider in ["openai", "openrouter", "custom"]:
            base_url = self.openai_base_url
            api_key = self.openai_api_key
            if self.provider == "openrouter":
                base_url = self.openrouter_base_url
                api_key = os.getenv("OPENROUTER_API_KEY")
            if self.provider == "custom":
                base_url = self.custom_base_url or self.openai_base_url
                api_key = os.getenv("CUSTOM_API_KEY")
            return self._openai_embeddings(texts, model, base_url=base_url, api_key=api_key, **kwargs)
        raise ProviderError(f"Unsupported provider: {self.provider}")

    def _ollama_chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
        if not self.ollama_base_url:
            if settings.dry_run:
                logger.warning("Ollama not configured, returning dry-run chat response")
                return f"[dry-run] simulated response for {model}"
            raise ProviderError("OLLAMA_BASE_URL is required for Ollama provider")
        url = f"{self.ollama_base_url.rstrip('/')}/chat/completions"
        payload = {"model": model, "messages": messages, **kwargs}
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise ProviderError(f"Ollama chat failed: {resp.status_code} {resp.text}")
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise ProviderError("Ollama returned no choices")
        return choices[0].get("message", {}).get("content", "")

    def _ollama_embeddings(self, texts: List[str], model: str, **kwargs) -> List[List[float]]:
        if not self.ollama_base_url:
            if settings.dry_run:
                logger.warning("Ollama not configured, returning dry-run embeddings")
                return [[0.0] for _ in texts]
            raise ProviderError("OLLAMA_BASE_URL is required for Ollama provider")
        url = f"{self.ollama_base_url.rstrip('/')}/embeddings"
        payload = {"model": model, "input": texts, **kwargs}
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise ProviderError(f"Ollama embeddings failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return [item.get("embedding", []) for item in data.get("data", [])]

    def _openai_chat(self, messages: List[Dict[str, Any]], model: str, base_url: Optional[str] = None, api_key: Optional[str] = None, **kwargs) -> str:
        base_url = base_url or self.openai_base_url
        api_key = api_key or self.openai_api_key
        if not api_key:
            if settings.dry_run:
                logger.warning("OpenAI not configured, returning dry-run chat response")
                return f"[dry-run] simulated response for {model}"
            raise ProviderError("OPENAI_API_KEY is required for OpenAI-compatible provider")
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages, **kwargs}
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise ProviderError(f"OpenAI chat failed: {resp.status_code} {resp.text}")
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise ProviderError("OpenAI returned no choices")
        return choices[0].get("message", {}).get("content", "")

    def _openai_embeddings(self, texts: List[str], model: str, base_url: Optional[str] = None, api_key: Optional[str] = None, **kwargs) -> List[List[float]]:
        base_url = base_url or self.openai_base_url
        api_key = api_key or self.openai_api_key
        if not api_key:
            if settings.dry_run:
                logger.warning("OpenAI not configured, returning dry-run embeddings")
                return [[0.0] for _ in texts]
            raise ProviderError("API key is required for embeddings")
        url = f"{base_url.rstrip('/')}/embeddings"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "input": texts, **kwargs}
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise ProviderError(f"OpenAI embeddings failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return [item.get("embedding", []) for item in data.get("data", [])]

    def generate(self, prompt: str, model_type: str = "main") -> str:
        model = self.get_model(model_type)
        if not model:
            raise ProviderError(f"No model configured for {model_type}")
        messages = [{"type": "system", "content": "You are Nova Agent, a safe, reliable, and developer-focused AI assistant."}, {"type": "user", "content": prompt}]
        return self.request_chat(messages, model)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        model = self.get_model("embeddings")
        if not model:
            raise ProviderError("No embedding model configured")
        return self.request_embeddings(texts, model)


def get_provider() -> BaseProvider:
    provider = BaseProvider()
    logger.debug("Using provider: %s", provider.provider)
    return provider
