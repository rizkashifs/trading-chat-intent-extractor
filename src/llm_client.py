from __future__ import annotations

import os
from dataclasses import dataclass

from .prompting import SYSTEM_PROMPT, build_user_prompt
from .windowing import MessageWindow


@dataclass(frozen=True)
class LlmResponse:
    content: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


class LlmExtractor:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.model = model or os.getenv("LLM_MODEL") or "Sonnet 4.6"

    def extract_window(self, window: MessageWindow, client_ids: list[str] | None = None) -> LlmResponse:
        if not self.api_key:
            raise ValueError("Set LLM_API_KEY or OPENAI_API_KEY")
        if not self.base_url:
            raise ValueError("Set LLM_BASE_URL for the OpenAI-compatible LLM gateway")

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(window, client_ids=client_ids)},
            ],
            temperature=0,
        )
        usage = response.usage
        return LlmResponse(
            content=response.choices[0].message.content or "",
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )
