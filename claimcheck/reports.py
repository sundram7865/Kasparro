"""Local run reports (JSON + Markdown), sanitized exchanges and v1/v2 comparison."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import config


def _default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"not serializable: {type(value).__name__}")


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=_default) + "\n", encoding="utf-8")


def _fmt(value) -> str:
    return "null" if value is None else (f"{value:.4f}" if isinstance(value, float) else str(value))


def render_markdown(report: dict) -> str:
    run, counts, metrics = report["run"], report["counts"], report["metrics"]
    lines = [
        f"# Run report: {run['agent_version']} / {run['split']}",
        "",
        f"- run_id: `{run['run_id']}`",
        f"- status: **{run['status']}**",
        f"- provider / model: `{run['provider']}` / `{run['model']}`",
        f"- prompt_version: `{run['prompt_version']}`",
        f"- dataset / fact / evaluator: `{run['dataset_version']}` / `{run['fact_version']}` / `{run['evaluator_version']}`",
        f"- source_revision: `{run.get('source_revision')}`",
        f"- started / finished: {_fmt(run['started_at'])} / {_fmt(run.get('finished_at'))}"
        f" ({run.get('duration_seconds', 'n/a')} s)",
        f"- settings: `{json.dumps(run['settings'], default=_default)}`",
        f"- file hashes (sha256): `{json.dumps(run['file_hashes'])}`",
        "",
        "## Counts",
        "",
        "| scheduled | ok | errors | empty | G | P | M | C |",
        "|---|---|---|---|---|---|---|---|",
        f"| {counts['scheduled_answers']} | {counts['ok_answers']} | {counts['error_answers']} | "
        f"{counts['empty_answers']} | {_fmt(counts['G'])} | {counts['P']} | {_fmt(counts['M'])} | {_fmt(counts['C'])} |",
        "",
        f"Predicted label counts: `{json.dumps(counts['predicted_label_counts'])}`",
        "",
        "## Metrics",
        "",
    ]
    if metrics is None:
        lines += [
            "Quality metrics are **null**: this split has no labels available to the harness "
            "(final-check labels are held privately by the reviewers).",
            "",
        ]
    else:
        ex, jt = metrics["extraction"], metrics["joint"]
        lines += [
            "| | precision | recall | F1 |",
            "|---|---|---|---|",
            f"| extraction (span match) | {_fmt(ex['precision'])} | {_fmt(ex['recall'])} | {_fmt(ex['f1'])} |",
            f"| **joint (span + label)** | {_fmt(jt['precision'])} | {_fmt(jt['recall'])} | **{_fmt(jt['f1'])}** |",
            "",
            f"Gold claim coverage C/G: **{_fmt(metrics['gold_claim_coverage'])}**",
            "",
        ]
    lines += ["## Answer errors", ""]
    if report["answer_errors"]:
        lines += ["| answer | type | message |", "|---|---|---|"]
        lines += [f"| {e['answer_id']} | {e['error_type']} | {e['error_message']} |" for e in report["answer_errors"]]
    else:
        lines.append("None.")
    lines.append("")
    scoring = report.get("scoring")
    if scoring:
        cm = scoring["confusion_matrix_expected_by_predicted"]
        lines += [
            "## Confusion matrix (matched claims, rows = expected, columns = predicted)",
            "",
            "| expected \\ predicted | " + " | ".join(config.LABELS) + " |",
            "|---|" + "---|" * len(config.LABELS),
        ]
        lines += [f"| {e} | " + " | ".join(str(cm[e][p]) for p in config.LABELS) + " |" for e in config.LABELS]
        lines += ["", "## Joint recall by difficulty tag", "", "| tag | correct | gold |", "|---|---|---|"]
        lines += [f"| {t} | {v['correct']} | {v['gold']} |" for t, v in scoring["joint_recall_by_difficulty_tag"].items()]
        lines += ["", f"## Wrong-label matches ({len(scoring['wrong_label'])})", ""]
        if scoring["wrong_label"]:
            lines += ["| claim_id | expected | predicted | tags |", "|---|---|---|---|"]
            lines += [
                f"| {w['claim_id']} | {w['expected_label']} | {w['predicted_label']} | {', '.join(w['difficulty_tags'])} |"
                for w in scoring["wrong_label"]
            ]
        lines += ["", f"## Missed gold claims ({len(scoring['missed_gold'])})", ""]
        if scoring["missed_gold"]:
            lines += ["| gold claim_id | expected | answer error | quote |", "|---|---|---|---|"]
            lines += [
                f"| {m['gold_claim_id']} | {m['expected_label']} | {m['answer_error']} | {m['quote'][:90]}... |"
                for m in scoring["missed_gold"]
            ]
        lines += ["", f"## Unmatched (extra) predictions ({len(scoring['unmatched_predictions'])})", ""]
        if scoring["unmatched_predictions"]:
            lines += ["| claim_id | label | quote |", "|---|---|---|"]
            lines += [f"| {u['claim_id']} | {u['label']} | {u['quote'][:90]}... |" for u in scoring["unmatched_predictions"]]
        lines.append("")
    lines += ["## Per-answer outcomes", "", "| answer | status | claims | turns | latency ms | tools |",
              "|---|---|---|---|---|---|"]
    for a in report["answers"]:
        tools = ",".join(f"{t['name']}({t['brand_id']})" for t in a["tool_calls"])
        lines.append(f"| {a['answer_id']} | {a['status']} | {len(a['claims'])} | {a['model_turns']} | "
                     f"{a['latency_ms']} | {tools} |")
    lines.append("")
    lines.append("Full predictions (spans, quotes, labels, fact_ids, reasons) are in `report.json`.")
    return "\n".join(lines) + "\n"


def write_run_artifacts(out_dir: Path, report: dict, exchanges: dict[str, list[dict]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "report.json", report)
    (out_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
    for answer_id, exchange in exchanges.items():
        write_json(out_dir / "exchanges" / f"{answer_id}.json", exchange)


def _wrong_or_missed(report: dict) -> dict[str, str]:
    """gold_claim_id -> outcome ('correct' | 'wrong:<label>' | 'missed') for a development report."""
    outcome = {}
    for m in report["scoring"]["matches"]:
        outcome[m["gold_claim_id"]] = "correct" if m["correct"] else f"wrong:{m['predicted_label']}"
    for m in report["scoring"]["missed_gold"]:
        outcome[m["gold_claim_id"]] = "missed"
    return outcome


def compare_reports(base: dict, candidate: dict) -> dict:
    for key in ("split", "dataset_version", "evaluator_version", "fact_version", "file_hashes", "provider", "model"):
        if base["run"][key] != candidate["run"][key]:
            raise ValueError(f"runs are not comparable: {key} differs")
    result = {
        "base": {"run_id": base["run"]["run_id"], "agent_version": base["run"]["agent_version"],
                 "counts": base["counts"], "metrics": base["metrics"]},
        "candidate": {"run_id": candidate["run"]["run_id"], "agent_version": candidate["run"]["agent_version"],
                      "counts": candidate["counts"], "metrics": candidate["metrics"]},
    }
    if base["metrics"] is None or candidate["metrics"] is None:
        result["fixed"] = result["regressed"] = result["changed_wrong"] = None
        return result
    b, c = _wrong_or_missed(base), _wrong_or_missed(candidate)
    expected = {m["gold_claim_id"]: m["expected_label"] for m in base["scoring"]["matches"]}
    expected.update({m["gold_claim_id"]: m["expected_label"] for m in base["scoring"]["missed_gold"]})
    rows = lambda pred: sorted(  # noqa: E731
        ({"gold_claim_id": g, "expected": expected[g], "base": b[g], "candidate": c[g]} for g in b if pred(b[g], c[g])),
        key=lambda r: r["gold_claim_id"],
    )
    result["fixed"] = rows(lambda x, y: x != "correct" and y == "correct")
    result["regressed"] = rows(lambda x, y: x == "correct" and y != "correct")
    result["changed_wrong"] = rows(lambda x, y: x != "correct" and y != "correct" and x != y)
    result["extra_predictions"] = {
        "base": len(base["scoring"]["unmatched_predictions"]),
        "candidate": len(candidate["scoring"]["unmatched_predictions"]),
    }
    return result


def render_comparison(cmp: dict) -> str:
    lines = ["# v1 vs v2 comparison (identical inputs, evaluator, provider, model and settings)", ""]
    b, c = cmp["base"], cmp["candidate"]
    lines += [f"- base: {b['agent_version']} run `{b['run_id']}`", f"- candidate: {c['agent_version']} run `{c['run_id']}`", ""]
    if b["metrics"] is None:
        lines += ["Check split: quality metrics are null for both runs (private labels).", "",
                  "| | base | candidate |", "|---|---|---|"]
        for key in ("P", "error_answers", "empty_answers"):
            lines.append(f"| {key} | {b['counts'][key]} | {c['counts'][key]} |")
        return "\n".join(lines) + "\n"
    lines += ["| metric | base | candidate | delta |", "|---|---|---|---|"]
    for group in ("extraction", "joint"):
        for name in ("precision", "recall", "f1"):
            x, y = b["metrics"][group][name], c["metrics"][group][name]
            lines.append(f"| {group} {name} | {x:.4f} | {y:.4f} | {y - x:+.4f} |")
    x, y = b["metrics"]["gold_claim_coverage"], c["metrics"]["gold_claim_coverage"]
    lines.append(f"| gold claim coverage C/G | {x:.4f} | {y:.4f} | {y - x:+.4f} |")
    for key in ("G", "P", "M", "C", "error_answers"):
        lines.append(f"| {key} | {b['counts'][key]} | {c['counts'][key]} | {c['counts'][key] - b['counts'][key]:+d} |")
    lines.append(f"| extra (unmatched) predictions | {cmp['extra_predictions']['base']} | "
                 f"{cmp['extra_predictions']['candidate']} | "
                 f"{cmp['extra_predictions']['candidate'] - cmp['extra_predictions']['base']:+d} |")
    for title, key in (("Fixed (wrong/missed in base, correct in candidate)", "fixed"),
                       ("Regressions (correct in base, wrong/missed in candidate)", "regressed"),
                       ("Still wrong but changed", "changed_wrong")):
        lines += ["", f"## {title}: {len(cmp[key])}", ""]
        if cmp[key]:
            lines += ["| gold claim | expected | base | candidate |", "|---|---|---|---|"]
            lines += [f"| {r['gold_claim_id']} | {r['expected']} | {r['base']} | {r['candidate']} |" for r in cmp[key]]
    return "\n".join(lines) + "\n"
