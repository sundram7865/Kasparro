"""Provider-neutral types for one model turn."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass
class ModelTurn:
    content: str | None
    tool_calls: list[ToolCall]
    # The assistant message exactly as it must be replayed in the next request
    # (keeps provider extras such as Gemini thought signatures).
    assistant_message: dict
    finish_reason: str | None = None
    usage: dict = field(default_factory=dict)


class Provider(Protocol):
    name: str
    model: str

    def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        tool_choice: str,
        timeout: float,
    ) -> ModelTurn:
        """Run one model turn. Raises ProviderTimeout or ProviderError on failure."""
        ...
