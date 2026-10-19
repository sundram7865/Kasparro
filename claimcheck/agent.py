"""The claim extraction and classification agent (max three model turns per answer)."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict, ValidationError

from . import config, errors
from .data import Catalogue
from .facts_tool import FactTool
from .providers.base import Provider
from .schemas import AgentInput, Claim, Label
from .segment import Sentence, split_sentences
from .validation import ClaimValidationError, make_claim_id, trim_reason, validate_claims


def load_prompt(version: str) -> str:
    if version not in config.AGENT_VERSIONS:
        raise ValueError(f"unknown agent version {version!r}")
    return (config.PROMPTS_DIR / f"{version}.md").read_text(encoding="utf-8")


def prompt_version(version: str) -> str:
    digest = hashlib.sha256(load_prompt(version).encode("utf-8")).hexdigest()[:12]
    return f"{version}-{digest}"


def render_user_message(inp: AgentInput, sentences: list[Sentence]) -> str:
    lines = [
        f"answer_id: {inp.answer_id}",
        f"primary brand_id: {inp.brand_id}",
        f"question: {' '.join(inp.question.split())}",
        "",
        "<answer_sentences>",
        *(f"{s.sentence_id}: {' '.join(s.text.split())}" for s in sentences),
        "</answer_sentences>",
    ]
    return "\n".join(lines)


class _ModelClaim(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sentence_id: str
    label: Label
    fact_ids: list[str]
    reason: str


class _ModelOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer_id: str | None = None
    claims: list[_ModelClaim]


@dataclass
class AgentResult:
    answer_id: str
    status: str  # "ok" | "error"
    claims: list[Claim] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    latency_ms: int = 0
    model_turns: int = 0
    tool_calls: list[dict] = field(default_factory=list)
    usage: list[dict] = field(default_factory=list)
    exchange: list[dict] = field(default_factory=list)
    trace_ref: str | None = None


def _strip_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else ""
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped.strip()


def parse_final_output(
    content: str | None,
    inp: AgentInput,
    sentences: list[Sentence],
    catalogue: Catalogue,
) -> list[Claim]:
    """Turn the model's JSON (sentence IDs + labels) into validated, offset-exact claims."""
    if not content or not content.strip():
        raise errors.AgentError(errors.INVALID_OUTPUT, "model returned an empty final message")
    try:
        payload = json.loads(_strip_fence(content))
    except json.JSONDecodeError as exc:
        raise errors.AgentError(errors.INVALID_OUTPUT, f"final message is not JSON: {exc.msg}") from exc
    try:
        output = _ModelOutput.model_validate(payload)
    except ValidationError as exc:
        first = exc.errors()[0]
        loc = ".".join(str(p) for p in first.get("loc", ()))
        raise errors.AgentError(errors.INVALID_OUTPUT, f"schema violation at {loc}: {first.get('msg')}") from exc
    if output.answer_id is not None and output.answer_id != inp.answer_id:
        raise errors.AgentError(errors.INVALID_OUTPUT, "output answer_id does not match input")

    by_id = {s.sentence_id: s for s in sentences}
    seen: set[str] = set()
    claims: list[Claim] = []
    known = catalogue.fact_ids
    for item in output.claims:
        sentence = by_id.get(item.sentence_id)
        if sentence is None:
            raise errors.AgentError(errors.INVALID_OUTPUT, f"unknown sentence_id {item.sentence_id[:20]!r}")
        if item.sentence_id in seen:
            raise errors.AgentError(errors.INVALID_OUTPUT, f"duplicate sentence_id {item.sentence_id}")
        seen.add(item.sentence_id)
        invented = [fid for fid in item.fact_ids if fid not in known]
        if invented:
            raise errors.AgentError(errors.INVALID_OUTPUT, f"invented fact_ids {invented[:3]}")
        claims.append(
            Claim(
                claim_id=make_claim_id(inp.answer_id, sentence.start, sentence.end),
                start_char=sentence.start,
                end_char=sentence.end,
                quote=inp.ai_answer[sentence.start:sentence.end],
                label=item.label,
                fact_ids=list(dict.fromkeys(item.fact_ids)),
                reason=trim_reason(item.reason),
            )
        )
    claims.sort(key=lambda c: c.start_char)
    try:
        return validate_claims(inp.answer_id, inp.ai_answer, claims, known)
    except ClaimValidationError as exc:
        raise errors.AgentError(errors.INVALID_OUTPUT, str(exc)) from exc


def run_agent(
    inp: AgentInput,
    version: str,
    provider: Provider,
    catalogue: Catalogue,
    *,
    timeout_seconds: float,
    max_turns: int = config.MAX_MODEL_TURNS,
) -> AgentResult:
    """Run one answer. Never raises for answer-level failures: they become status="error"."""
    started = time.perf_counter()
    result = AgentResult(answer_id=inp.answer_id, status="error")
    tool = FactTool(catalogue)
    sentences = split_sentences(inp.ai_answer)
    messages: list[dict] = [
        {"role": "system", "content": load_prompt(version)},
        {"role": "user", "content": render_user_message(inp, sentences)},
    ]
    result.exchange.extend(messages)
    facts_fetched = False
    try:
        for turn in range(1, max_turns + 1):
            if turn == 1:
                tool_choice = "required"  # the first turn must look facts up
            elif turn == max_turns:
                tool_choice = "none"  # the last turn must answer
            else:
                tool_choice = "auto"
            try:
                model_turn = provider.complete(
                    messages, [tool.schema()], tool_choice=tool_choice, timeout=timeout_seconds
                )
            except errors.ProviderTimeout as exc:
                raise errors.AgentError(errors.PROVIDER_TIMEOUT, str(exc)) from exc
            except errors.ProviderError as exc:
                raise errors.AgentError(errors.PROVIDER_ERROR, str(exc)) from exc
            result.model_turns = turn
            if model_turn.usage:
                result.usage.append(model_turn.usage)
            result.exchange.append(model_turn.assistant_message)

            if model_turn.tool_calls:
                if turn == max_turns:
                    raise errors.AgentError(
                        errors.TURN_LIMIT_EXCEEDED, f"model still requested tools on turn {turn} of {max_turns}"
                    )
                messages.append(model_turn.assistant_message)
                for call in model_turn.tool_calls:
                    output = tool.execute(call.name, call.arguments)
                    result.tool_calls.append({"turn": turn, "name": call.name, "brand_id": output["brand_id"]})
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": json.dumps(output, separators=(",", ":")),
                    }
                    messages.append(tool_message)
                    result.exchange.append(tool_message)
                facts_fetched = True
                continue

            if not facts_fetched:
                raise errors.AgentError(errors.NO_TOOL_CALL, "model answered without requesting get_brand_facts")
            result.claims = parse_final_output(model_turn.content, inp, sentences, catalogue)
            result.status = "ok"
            break
        else:  # pragma: no cover - loop always breaks or raises
            raise errors.AgentError(errors.TURN_LIMIT_EXCEEDED, "no final answer within the turn limit")
    except errors.AgentError as exc:
        result.status = "error"
        result.claims = []
        result.error_type = exc.error_type
        result.error_message = exc.message
    finally:
        result.latency_ms = int((time.perf_counter() - started) * 1000)
    return result
