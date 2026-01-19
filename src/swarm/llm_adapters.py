from __future__ import annotations
import os
import requests
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class LLMResponse:
    text: str
    raw: Dict[str, Any]

class BaseLLM:
    def chat(self, messages: List[Dict[str, str]], model: str, temperature: float, max_tokens: int, timeout_seconds: int) -> LLMResponse:
        raise NotImplementedError

class OpenAIChatCompletionsLLM(BaseLLM):
    """Minimal OpenAI adapter using an OpenAI-compatible /v1/chat/completions endpoint.

    Credentials:
      - Reads OPENAI_API_KEY from environment.
    Endpoint:
      - Uses OPENAI_BASE_URL if set; otherwise https://api.openai.com
    """
    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")

    def chat(self, messages: List[Dict[str, str]], model: str, temperature: float, max_tokens: int, timeout_seconds: int) -> LLMResponse:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return LLMResponse(text=text, raw=data)

def get_llm(provider: str) -> BaseLLM:
    provider = (provider or "").lower().strip()
    if provider == "openai":
        return OpenAIChatCompletionsLLM()
    raise ValueError(f"Unknown provider: {provider}. Implement it in llm_adapters.py")
