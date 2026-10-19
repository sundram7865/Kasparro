"""Sequential evaluation runs shared by the CLI and the API.

Order of operations (gold isolation): run the agent on every scheduled answer and
persist each outcome -> only then load development gold and score.
"""
from __future__ import annotations

import subprocess
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from . import config
from .agent import AgentResult, prompt_version, run_agent
from .data import Answer, Catalogue, dataset_hashes, load_gold
from .schemas import AgentInput
from .scoring import AnswerOutcome, score_split


def source_revision() -> str | None:
    try:
        rev = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=config.ROOT, capture_output=True, text=True, timeout=10
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=config.ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if not rev:
        return None
    return f"{rev}{'-dirty' if dirty else ''}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_metadata(agent_version: str, split: str, provider, settings: config.Settings,
                   answer_ids: list[str], subset: bool) -> dict:
    run_settings = settings.public()
    run_settings["provider"] = provider.name
    run_settings["model"] = provider.model
    run_settings["sequential"] = True
    if subset:
        run_settings["answer_subset"] = answer_ids
    return {
        "run_id": str(uuid.uuid4()),
        "split": split,
        "agent_version": agent_version,
        "prompt_version": prompt_version(agent_version),
        "dataset_version": config.DATASET_VERSION,
        "evaluator_version": config.EVALUATOR_VERSION,
        "fact_version": config.FACT_VERSION,
        "provider": provider.name,
        "model": provider.model,
        "settings": run_settings,
        "source_revision": source_revision(),
        "file_hashes": dataset_hashes(),
        "started_at": _now(),
    }


def _answer_record(answer: Answer, result: AgentResult) -> dict:
    return {
        "answer_id": answer.answer_id,
        "brand_id": answer.brand_id,
        "status": result.status,
        "error_type": result.error_type,
        "error_message": result.error_message,
        "latency_ms": result.latency_ms,
        "model_turns": result.model_turns,
        "tool_calls": result.tool_calls,
        "usage": result.usage,
        "claims": [c.model_dump() for c in result.claims],
    }


def execute_run(
    *,
    agent_version: str,
    split: str,
    provider,
    settings: config.Settings,
    catalogue: Catalogue,
    answers: list[Answer],
    store=None,
    answer_ids: list[str] | None = None,
    progress: Callable[[str], None] | None = None,
) -> tuple[dict, dict[str, list[dict]]]:
    """Run one split sequentially. Returns (report, exchanges_by_answer_id)."""
    if agent_version not in config.AGENT_VERSIONS:
        raise ValueError(f"agent_version must be one of {config.AGENT_VERSIONS}")
    if split not in config.SPLITS:
        raise ValueError(f"split must be one of {config.SPLITS}")
    scheduled = sorted((a for a in answers if a.split == split), key=lambda a: a.answer_id)
    if answer_ids:
        wanted = set(answer_ids)
        scheduled = [a for a in scheduled if a.answer_id in wanted]
    scheduled_ids = [a.answer_id for a in scheduled]
    meta = build_metadata(agent_version, split, provider, settings, scheduled_ids, bool(answer_ids))
    say = progress or (lambda _msg: None)

    records: list[dict] = []
    outcomes: list[AnswerOutcome] = []
    exchanges: dict[str, list[dict]] = {}
    if store is not None:
        store.create_run(meta)
    try:
        for position, answer in enumerate(scheduled, start=1):
            inp = AgentInput(
                answer_id=answer.answer_id,
                brand_id=answer.brand_id,
                question=answer.question,
                ai_answer=answer.ai_answer,
            )
            result = run_agent(
                inp, agent_version, provider, catalogue,
                timeout_seconds=settings.timeout_seconds, max_turns=settings.max_model_turns,
            )
            result.trace_ref = f"{meta['run_id']}/{answer.answer_id}"
            if store is not None:
                store.save_answer(meta["run_id"], position, answer.brand_id, result)
            records.append(_answer_record(answer, result))
            outcomes.append(
                AnswerOutcome(answer.answer_id, result.status, result.claims, result.error_type, result.error_message)
            )
            exchanges[answer.answer_id] = result.exchange
            status = f"{len(result.claims)} claims" if result.status == "ok" else f"ERROR {result.error_type}"
            say(f"[{position}/{len(scheduled)}] {answer.answer_id}: {status} ({result.latency_ms} ms)")

        # Predictions are saved; only now may development gold be joined.
        gold = load_gold() if split == "development" else None
        texts = {a.answer_id: a.ai_answer for a in scheduled}
        score = score_split(texts, scheduled_ids, outcomes, gold)
    except BaseException as exc:
        finished = _now()
        if store is not None:
            try:
                store.fail_run(meta["run_id"], f"{type(exc).__name__}: {str(exc)[:300]}", finished)
            except Exception:  # pragma: no cover - best effort while already failing
                pass
        partial = {"run": {**meta, "status": "failed", "finished_at": finished, "error": repr(exc)[:300]},
                   "answers": records}
        exc.partial_report = partial  # type: ignore[attr-defined]
        raise

    finished = _now()
    matches = score["details"]["matches"] if score["details"] else None
    scoring_ids = None
    if score["details"]:
        d = score["details"]
        scoring_ids = {
            "missed_gold_ids": [m["gold_claim_id"] for m in d["missed_gold"]],
            "unmatched_prediction_ids": [u["claim_id"] for u in d["unmatched_predictions"]],
            "wrong_label_ids": [w["claim_id"] for w in d["wrong_label"]],
            "answer_error_ids": [e["answer_id"] for e in score["answer_errors"]],
        }
    if store is not None:
        store.finish_run(meta["run_id"], score["counts"], score["metrics"], scoring_ids, matches, finished)
    report = {
        "run": {**meta, "status": "completed", "finished_at": finished,
                "duration_seconds": round((finished - meta["started_at"]).total_seconds(), 1)},
        "counts": score["counts"],
        "metrics": score["metrics"],
        "errors_by_type": score["errors_by_type"],
        "answer_errors": score["answer_errors"],
        "scoring": score["details"],
        "answers": records,
    }
    return report, exchanges
