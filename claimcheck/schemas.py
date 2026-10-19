"""Pydantic models for agent input/output and the API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Label = Literal["supported", "contradicted", "unknown"]
AgentVersion = Literal["v1", "v2"]
Split = Literal["development", "check"]


class AgentInput(BaseModel):
    """Exactly the fields the agent may see. Gold, claims and labels are rejected."""

    model_config = ConfigDict(extra="forbid")

    answer_id: str = Field(min_length=1, max_length=64)
    brand_id: str = Field(min_length=1, max_length=64)
    question: str = Field(max_length=5000)
    ai_answer: str = Field(min_length=1, max_length=50000)


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    start_char: int
    end_char: int
    quote: str
    label: Label
    fact_ids: list[str]
    reason: str


class AgentOutput(BaseModel):
    answer_id: str
    claims: list[Claim]


class ClassifyRequest(AgentInput):
    agent_version: AgentVersion


class EvaluationRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_version: AgentVersion
    split: Split
