"""Structural validation of predicted claims against the exact source text."""
from __future__ import annotations

import re
from collections.abc import Iterable

from . import config
from .schemas import Claim

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class ClaimValidationError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems[:5]))


def count_sentences(text: str) -> int:
    return len([part for part in _SENTENCE_END.split(text.strip()) if part])


def trim_reason(text: str, max_sentences: int = 2, max_chars: int = 600) -> str:
    """Keep at most two sentences of model-written reason text."""
    parts = [part for part in _SENTENCE_END.split(" ".join(str(text).split())) if part]
    return " ".join(parts[:max_sentences])[:max_chars]


def make_claim_id(answer_id: str, start: int, end: int) -> str:
    return f"{answer_id}:{start}:{end}"


def validate_claims(
    answer_id: str,
    ai_answer: str,
    claims: Iterable[Claim],
    known_fact_ids: set[str],
) -> list[Claim]:
    """Check bounds, quote equality, IDs, labels, fact IDs, ordering and overlaps.

    Returns the claims unchanged when valid; raises ClaimValidationError otherwise.
    """
    claims = list(claims)
    problems: list[str] = []
    seen_ids: set[str] = set()
    previous_end = -1
    previous_start = -1
    for claim in claims:
        tag = claim.claim_id
        s, e = claim.start_char, claim.end_char
        if not (0 <= s < e <= len(ai_answer)):
            problems.append(f"{tag}: span [{s}, {e}) outside answer of length {len(ai_answer)}")
            continue
        if claim.quote != ai_answer[s:e]:
            problems.append(f"{tag}: quote does not equal ai_answer[{s}:{e}]")
        if claim.quote != claim.quote.strip() or not claim.quote:
            problems.append(f"{tag}: quote has leading/trailing whitespace or is empty")
        if claim.claim_id != make_claim_id(answer_id, s, e):
            problems.append(f"{tag}: claim_id must be {make_claim_id(answer_id, s, e)}")
        if claim.claim_id in seen_ids:
            problems.append(f"{tag}: duplicate claim_id")
        seen_ids.add(claim.claim_id)
        if claim.label not in config.LABELS:
            problems.append(f"{tag}: unsupported label {claim.label!r}")
        unknown = [fid for fid in claim.fact_ids if fid not in known_fact_ids]
        if unknown:
            problems.append(f"{tag}: unknown fact_ids {unknown[:3]}")
        if len(set(claim.fact_ids)) != len(claim.fact_ids):
            problems.append(f"{tag}: repeated fact_ids")
        if count_sentences(claim.reason) > 2:
            problems.append(f"{tag}: reason longer than two sentences")
        if s <= previous_start:
            problems.append(f"{tag}: claims not in increasing start_char order")
        elif s < previous_end:
            problems.append(f"{tag}: span overlaps the previous claim")
        previous_start, previous_end = s, max(previous_end, e)
    if problems:
        raise ClaimValidationError(problems)
    return claims
