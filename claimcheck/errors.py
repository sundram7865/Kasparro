"""Answer-level error types. An error means: no accepted predictions for that answer."""
from __future__ import annotations

import re

# error_type values used across the agent, runner, database and API.
PROVIDER_ERROR = "provider_error"
PROVIDER_TIMEOUT = "provider_timeout"
INVALID_OUTPUT = "invalid_output"
ILLEGAL_TOOL = "illegal_tool"
UNKNOWN_BRAND = "unknown_brand"
TOOL_ARGUMENT_ERROR = "tool_argument_error"
TURN_LIMIT_EXCEEDED = "turn_limit_exceeded"
NO_TOOL_CALL = "no_tool_call"

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|authorization|bearer|token)\s*[:=]?\s*\S+"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"sk-[0-9A-Za-z_\-]{16,}"),
    re.compile(r"gsk_[0-9A-Za-z]{16,}"),
]


def sanitize(message: str, limit: int = 300) -> str:
    """Strip anything that looks like a credential and bound the length."""
    text = " ".join(str(message).split())
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text[:limit]


class AgentError(Exception):
    """A terminal, answer-level failure with a sanitized type and message."""

    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = sanitize(message)
        super().__init__(f"{error_type}: {self.message}")


class ProviderError(Exception):
    """Raised by provider adapters for non-timeout request failures."""


class ProviderTimeout(ProviderError):
    """Raised by provider adapters when a request exceeds its timeout."""
