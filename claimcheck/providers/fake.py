"""Deterministic fake providers for controlled tests (never used for live runs)."""
from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable

from ..errors import ProviderError, ProviderTimeout
from .base import ModelTurn, ToolCall


def tool_turn(*calls: tuple[str, dict | str]) -> ModelTurn:
    tool_calls = [
        ToolCall(id=f"call_{i}", name=name, arguments=args if isinstance(args, str) else json.dumps(args))
        for i, (name, args) in enumerate(calls)
    ]
    message = {
        "role": "assistant",
        "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": tc.arguments}}
            for tc in tool_calls
        ],
    }
    return ModelTurn(content=None, tool_calls=tool_calls, assistant_message=message, finish_reason="tool_calls")


def text_turn(content: str) -> ModelTurn:
    return ModelTurn(
        content=content,
        tool_calls=[],
        assistant_message={"role": "assistant", "content": content},
        finish_reason="stop",
    )


class ScriptedProvider:
    """Returns pre-scripted turns in order; items may be ModelTurn or an Exception to raise."""

    name = "fake"
    model = "scripted"

    def __init__(self, script: list):
        self.script = list(script)
        self.requests: list[dict] = []

    def complete(self, messages, tools, *, tool_choice, timeout):
        self.requests.append(
            {"messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools), "tool_choice": tool_choice}
        )
        if not self.script:
            raise ProviderError("fake script exhausted")
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


_SENTENCE_LINE = re.compile(r"^(S\d+): (.*)$", re.M)
_FIELD = re.compile(r"^(answer_id|primary brand_id): (.+)$", re.M)


class RuleBasedProvider:
    """Stateless fake that reacts to the real prompt: fetch facts, then label sentences.

    `decide(answer_id, sentence_id, text)` returns a label or None (not a claim).
    `failures` maps answer_id -> exception to raise or "invalid" for malformed output.
    """

    name = "fake"
    model = "rule-based"

    def __init__(self, decide: Callable[[str, str, str], str | None], failures: dict | None = None):
        self.decide = decide
        self.failures = failures or {}
        self.requests: list[dict] = []

    def complete(self, messages, tools, *, tool_choice, timeout):
        self.requests.append({"messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools)})
        user = next(m["content"] for m in messages if m["role"] == "user")
        fields = dict(_FIELD.findall(user))
        answer_id = fields["answer_id"]
        failure = self.failures.get(answer_id)
        if isinstance(failure, Exception):
            raise failure
        if not any(m["role"] == "tool" for m in messages):
            return tool_turn(("get_brand_facts", {"brand_id": fields["primary brand_id"]}))
        if failure == "invalid":
            return text_turn("this is not json")
        claims = []
        for sid, text in _SENTENCE_LINE.findall(user):
            label = self.decide(answer_id, sid, text)
            if label is not None:
                claims.append({"sentence_id": sid, "label": label, "fact_ids": [], "reason": "Fake decision."})
        return text_turn(json.dumps({"answer_id": answer_id, "claims": claims}))


def timeout_error() -> ProviderTimeout:
    return ProviderTimeout("provider request exceeded 1s")
