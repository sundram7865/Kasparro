"""Deterministic harness scoring: exact span matching, extraction and joint P/R/F1.

Matching key is (answer_id, start_char, end_char) after the prediction's quote has
been validated against the source text. No fuzzy matching and no LLM judge.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import config
from .data import GoldClaim
from .schemas import Claim


class ScoringError(ValueError):
    pass


@dataclass
class AnswerOutcome:
    answer_id: str
    status: str  # "ok" | "error"
    claims: list[Claim] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def prf(hits: int, predicted: int, gold: int) -> dict[str, float]:
    return {
        "precision": _ratio(hits, predicted),
        "recall": _ratio(hits, gold),
        "f1": _ratio(2 * hits, predicted + gold),
    }


def check_outcomes(scheduled_ids: list[str], outcomes: list[AnswerOutcome]) -> None:
    """Every scheduled answer must have exactly one terminal outcome, and nothing else."""
    counts = Counter(o.answer_id for o in outcomes)
    duplicated = sorted(a for a, n in counts.items() if n > 1)
    missing = sorted(set(scheduled_ids) - set(counts))
    unexpected = sorted(set(counts) - set(scheduled_ids))
    if len(set(scheduled_ids)) != len(scheduled_ids):
        raise ScoringError("scheduled answer IDs contain duplicates")
    if duplicated or missing or unexpected:
        raise ScoringError(
            f"answer outcomes invalid: duplicated={duplicated} missing={missing} unexpected={unexpected}"
        )
    for outcome in outcomes:
        if outcome.status not in ("ok", "error"):
            raise ScoringError(f"{outcome.answer_id}: unknown status {outcome.status!r}")
        if outcome.status == "error" and outcome.claims:
            raise ScoringError(f"{outcome.answer_id}: an error outcome cannot carry accepted claims")


def score_split(
    answer_texts: dict[str, str],
    scheduled_ids: list[str],
    outcomes: list[AnswerOutcome],
    gold: list[GoldClaim] | None,
) -> dict:
    """Score one run. `gold=None` means a check split: quality stays null."""
    check_outcomes(scheduled_ids, outcomes)
    by_answer = {o.answer_id: o for o in outcomes}
    predictions = [(o.answer_id, c) for a in scheduled_ids for o in [by_answer[a]] for c in o.claims]
    error_outcomes = [o for o in (by_answer[a] for a in scheduled_ids) if o.status == "error"]
    counts = {
        "scheduled_answers": len(scheduled_ids),
        "ok_answers": len(scheduled_ids) - len(error_outcomes),
        "error_answers": len(error_outcomes),
        "empty_answers": sum(1 for a in scheduled_ids if by_answer[a].status == "ok" and not by_answer[a].claims),
        "P": len(predictions),
        "predicted_label_counts": dict(Counter(c.label for _, c in predictions)),
    }
    errors_by_type = dict(Counter(o.error_type or "unknown_error" for o in error_outcomes))
    answer_errors = [
        {"answer_id": o.answer_id, "error_type": o.error_type, "error_message": o.error_message}
        for o in error_outcomes
    ]
    if gold is None or not scheduled_ids:
        counts.update({"G": None, "M": None, "C": None})
        return {
            "counts": counts,
            "metrics": None,
            "errors_by_type": errors_by_type,
            "answer_errors": answer_errors,
            "details": None,
        }

    scheduled = set(scheduled_ids)
    gold_in_split = [g for g in gold if g.answer_id in scheduled]
    gold_by_key: dict[tuple[str, int, int], GoldClaim] = {}
    for g in gold_in_split:
        if answer_texts[g.answer_id][g.start_char:g.end_char] != g.quote:
            raise ScoringError(f"gold {g.claim_id}: quote does not match the answer text")
        key = (g.answer_id, g.start_char, g.end_char)
        if key in gold_by_key:
            raise ScoringError(f"gold span duplicated: {g.claim_id}")
        gold_by_key[key] = g

    matched_gold: set[str] = set()
    matches: list[dict] = []
    unmatched_predictions: list[dict] = []
    invalid_quote_ids: list[str] = []
    for answer_id, claim in predictions:
        text = answer_texts[answer_id]
        if text[claim.start_char:claim.end_char] != claim.quote:
            invalid_quote_ids.append(claim.claim_id)
            unmatched_predictions.append({"claim_id": claim.claim_id, "label": claim.label, "quote": claim.quote})
            continue
        g = gold_by_key.get((answer_id, claim.start_char, claim.end_char))
        if g is None or g.claim_id in matched_gold:
            unmatched_predictions.append({"claim_id": claim.claim_id, "label": claim.label, "quote": claim.quote})
            continue
        matched_gold.add(g.claim_id)
        matches.append(
            {
                "claim_id": claim.claim_id,
                "gold_claim_id": g.claim_id,
                "expected_label": g.expected_label,
                "predicted_label": claim.label,
                "correct": claim.label == g.expected_label,
                "difficulty_tags": list(g.difficulty_tags),
            }
        )

    G, P, M = len(gold_in_split), len(predictions), len(matches)
    C = sum(1 for m in matches if m["correct"])
    counts.update({"G": G, "M": M, "C": C})
    errored = {o.answer_id for o in error_outcomes}
    missed = [
        {
            "gold_claim_id": g.claim_id,
            "expected_label": g.expected_label,
            "answer_error": g.answer_id in errored,
            "quote": g.quote,
        }
        for g in gold_in_split
        if g.claim_id not in matched_gold
    ]
    wrong_label = [m for m in matches if not m["correct"]]

    confusion: dict[str, dict[str, int]] = {e: {p: 0 for p in config.LABELS} for e in config.LABELS}
    for m in matches:
        confusion[m["expected_label"]][m["predicted_label"]] += 1

    correct_ids = {m["gold_claim_id"] for m in matches if m["correct"]}
    tag_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    label_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for g in gold_in_split:
        hit = int(g.claim_id in correct_ids)
        label_totals[g.expected_label][0] += hit
        label_totals[g.expected_label][1] += 1
        for tag in g.difficulty_tags:
            tag_totals[tag][0] += hit
            tag_totals[tag][1] += 1

    per_answer = []
    for answer_id in scheduled_ids:
        outcome = by_answer[answer_id]
        g_ids = [g.claim_id for g in gold_in_split if g.answer_id == answer_id]
        per_answer.append(
            {
                "answer_id": answer_id,
                "status": outcome.status,
                "gold": len(g_ids),
                "predicted": len(outcome.claims),
                "matched": sum(1 for gid in g_ids if gid in matched_gold),
                "correct": sum(1 for gid in g_ids if gid in correct_ids),
            }
        )

    metrics = {
        "extraction": prf(M, P, G),
        "joint": prf(C, P, G),
        "gold_claim_coverage": _ratio(C, G),
    }
    details = {
        "missed_gold": missed,
        "unmatched_predictions": unmatched_predictions,
        "invalid_quote_prediction_ids": invalid_quote_ids,
        "wrong_label": wrong_label,
        "matches": matches,
        "confusion_matrix_expected_by_predicted": confusion,
        "joint_recall_by_expected_label": {k: {"correct": v[0], "gold": v[1]} for k, v in sorted(label_totals.items())},
        "joint_recall_by_difficulty_tag": {k: {"correct": v[0], "gold": v[1]} for k, v in sorted(tag_totals.items())},
        "per_answer": per_answer,
    }
    return {
        "counts": counts,
        "metrics": metrics,
        "errors_by_type": errors_by_type,
        "answer_errors": answer_errors,
        "details": details,
    }
