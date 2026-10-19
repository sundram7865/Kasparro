"""Live provider over the OpenAI-compatible chat-completions API.

Works for Gemini (generativelanguage.googleapis.com/v1beta/openai), OpenAI and Groq.
"""
from __future__ import annotations

import random
import time

import openai
from openai import OpenAI

from .. import config
from ..errors import ProviderError, ProviderTimeout, sanitize
from .base import ModelTurn, ToolCall

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class OpenAICompatProvider:
    def __init__(self, settings: config.Settings, api_key: str):
        self.settings = settings
        self.name = settings.provider
        self.model = settings.model
        base_url = config.PROVIDERS[settings.provider]["base_url"]
        # SDK retries are disabled so every attempt is visible and bounded here.
        self.client = OpenAI(api_key=api_key, base_url=base_url, max_retries=0)
        self._last_request = 0.0

    def _throttle(self) -> None:
        wait = self.settings.min_request_interval_seconds - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def complete(self, messages, tools, *, tool_choice: str, timeout: float) -> ModelTurn:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_output_tokens,
            "timeout": timeout,
        }
        if self.settings.reasoning_effort:
            kwargs["reasoning_effort"] = self.settings.reasoning_effort
        attempt = 0
        while True:
            self._throttle()
            try:
                response = self.client.chat.completions.create(**kwargs)
                break
            except openai.APITimeoutError as exc:
                # A timed-out request is never retried: it becomes an answer-level timeout.
                raise ProviderTimeout(f"provider request exceeded {timeout:.0f}s") from exc
            except openai.APIStatusError as exc:
                status = exc.status_code
                if status in RETRYABLE_STATUS and attempt < self.settings.max_retries:
                    attempt += 1
                    time.sleep(_backoff_seconds(exc, attempt))
                    continue
                raise ProviderError(f"HTTP {status}: {sanitize(_status_message(exc), 200)}") from exc
            except openai.APIConnectionError as exc:
                if attempt < self.settings.max_retries:
                    attempt += 1
                    time.sleep(_backoff_seconds(None, attempt))
                    continue
                raise ProviderError(f"connection error: {sanitize(str(exc), 200)}") from exc
            except openai.OpenAIError as exc:
                raise ProviderError(f"{type(exc).__name__}: {sanitize(str(exc), 200)}") from exc

        if not response.choices:
            raise ProviderError("provider returned no choices")
        choice = response.choices[0]
        message = choice.message
        tool_calls = [
            ToolCall(id=tc.id or f"call_{i}", name=tc.function.name, arguments=tc.function.arguments or "")
            for i, tc in enumerate(message.tool_calls or [])
        ]
        assistant_message = message.model_dump(exclude_none=True)
        assistant_message["role"] = "assistant"
        for i, tc in enumerate(assistant_message.get("tool_calls") or []):
            tc.setdefault("id", tool_calls[i].id)
        usage = response.usage.model_dump(exclude_none=True) if response.usage else {}
        return ModelTurn(
            content=message.content,
            tool_calls=tool_calls,
            assistant_message=assistant_message,
            finish_reason=choice.finish_reason,
            usage=usage,
        )


def _status_message(exc: openai.APIStatusError) -> str:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error", body)
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
    if isinstance(body, list) and body and isinstance(body[0], dict):
        err = body[0].get("error", {})
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
    return exc.message


def _backoff_seconds(exc: openai.APIStatusError | None, attempt: int) -> float:
    retry_after = None
    if exc is not None and exc.response is not None:
        retry_after = exc.response.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), 90.0)
        except ValueError:
            pass
    return min(5.0 * (2 ** (attempt - 1)), 60.0) + random.uniform(0, 1)
