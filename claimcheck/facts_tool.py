"""The read-only get_brand_facts tool: schema for the model and a validating executor."""
from __future__ import annotations

import json
from typing import Any

from . import config, errors
from .data import Catalogue

TOOL_NAME = "get_brand_facts"


class FactTool:
    def __init__(self, catalogue: Catalogue):
        self.catalogue = catalogue

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": TOOL_NAME,
                "description": (
                    "Return every catalogue fact row for one brand (all of its models, current and "
                    "historical rows). This catalogue is the only factual authority."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "brand_id": {
                            "type": "string",
                            "enum": self.catalogue.brands,
                            "description": "Catalogue brand identifier, e.g. the primary brand_id.",
                        }
                    },
                    "required": ["brand_id"],
                },
            },
        }

    def execute(self, name: str, raw_arguments: str | dict | None) -> dict[str, Any]:
        """Validate the tool name and arguments, then perform the read-only lookup.

        Raises AgentError for an illegal tool, malformed arguments or an unknown brand.
        Nothing from the answer text is ever executed: only this one lookup exists.
        """
        if name != TOOL_NAME:
            raise errors.AgentError(errors.ILLEGAL_TOOL, f"model requested unknown tool {name[:60]!r}")
        if isinstance(raw_arguments, dict):
            arguments = raw_arguments
        else:
            try:
                arguments = json.loads(raw_arguments or "{}")
            except json.JSONDecodeError as exc:
                raise errors.AgentError(errors.TOOL_ARGUMENT_ERROR, f"tool arguments are not JSON: {exc}") from exc
        if not isinstance(arguments, dict) or set(arguments) != {"brand_id"}:
            raise errors.AgentError(errors.TOOL_ARGUMENT_ERROR, "tool arguments must be exactly {brand_id}")
        brand_id = arguments["brand_id"]
        if not isinstance(brand_id, str) or brand_id not in self.catalogue.by_brand:
            raise errors.AgentError(errors.UNKNOWN_BRAND, f"model requested unknown brand {str(brand_id)[:60]!r}")
        rows = [fact.to_tool_row() for fact in self.catalogue.facts_for_brand(brand_id)]
        return {"fact_version": config.FACT_VERSION, "brand_id": brand_id, "facts": rows}
