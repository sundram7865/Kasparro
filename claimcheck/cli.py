"""Command line entry points.

  python -m claimcheck.cli verify-data
  python -m claimcheck.cli init-db
  python -m claimcheck.cli run --agent-version v1 --split development
  python -m claimcheck.cli compare artifacts/runs/v1_development/report.json artifacts/runs/v2_development/report.json
  python -m claimcheck.cli rescore artifacts/runs/v1_development/report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config
from .data import Catalogue, dataset_hashes, load_answers, load_facts, load_gold
from .reports import compare_reports, render_comparison, write_json, write_run_artifacts


def cmd_verify_data(_args) -> int:
    answers, facts, gold = load_answers(), load_facts(), load_gold()
    texts = {a.answer_id: a.ai_answer for a in answers}
    mismatched = [g.claim_id for g in gold if texts[g.answer_id][g.start_char:g.end_char] != g.quote]
    print(f"answers={len(answers)} (development={sum(a.split == 'development' for a in answers)}, "
          f"check={sum(a.split == 'check' for a in answers)}) facts={len(facts)} gold={len(gold)}")
    print(f"gold quotes equal to ai_answer[start:end]: {len(gold) - len(mismatched)}/{len(gold)}")
    for name, digest in dataset_hashes().items():
        print(f"sha256 {digest}  data/{name}")
    return 1 if mismatched else 0


def cmd_init_db(_args) -> int:
    from .db import init_schema

    url = config.database_url()
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    init_schema(url)
    print("schema ready")
    return 0


def cmd_run(args) -> int:
    from .providers import build_provider
    from .runner import execute_run

    settings = config.load_settings()
    provider = build_provider(settings)
    catalogue = Catalogue(load_facts())
    answers = load_answers()
    subset = [a.strip() for a in args.answers.split(",")] if args.answers else None
    store = None
    if not args.no_db:
        from .db import RunStore, init_schema

        url = config.database_url()
        if not url:
            print("DATABASE_URL is not set (use --no-db to skip persistence)", file=sys.stderr)
            return 2
        init_schema(url)
        store = RunStore(url)
    default_dir = config.ARTIFACTS_DIR / ("scratch" if subset else "runs") / f"{args.agent_version}_{args.split}"
    out_dir = Path(args.out) if args.out else default_dir
    print(f"run {args.agent_version}/{args.split} provider={provider.name} model={provider.model} -> {out_dir}")
    try:
        report, exchanges = execute_run(
            agent_version=args.agent_version, split=args.split, provider=provider, settings=settings,
            catalogue=catalogue, answers=answers, store=store, answer_ids=subset, progress=print,
        )
    except BaseException as exc:
        partial = getattr(exc, "partial_report", None)
        if partial is not None:
            write_json(out_dir / "partial_report.json", partial)
            print(f"run failed; partial evidence saved to {out_dir / 'partial_report.json'}", file=sys.stderr)
        raise
    finally:
        if store is not None:
            store.close()
    write_run_artifacts(out_dir, report, exchanges)
    print(json.dumps({"run_id": report["run"]["run_id"], "counts": report["counts"], "metrics": report["metrics"]},
                     indent=2))
    return 0


def cmd_compare(args) -> int:
    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    cmp = compare_reports(base, candidate)
    text = render_comparison(cmp)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        write_json(out.with_suffix(".json"), cmp)
    print(text)
    return 0


def cmd_rescore(args) -> int:
    """Recompute quality from a saved report's predictions (deterministic harness check)."""
    from .schemas import Claim
    from .scoring import AnswerOutcome, score_split

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    answers = {a.answer_id: a for a in load_answers()}
    outcomes = [
        AnswerOutcome(r["answer_id"], r["status"], [Claim(**c) for c in r["claims"]], r["error_type"], r["error_message"])
        for r in report["answers"]
    ]
    scheduled = [r["answer_id"] for r in report["answers"]]
    gold = load_gold() if report["run"]["split"] == "development" else None
    score = score_split({a: answers[a].ai_answer for a in scheduled}, scheduled, outcomes, gold)
    print(json.dumps({"counts": score["counts"], "metrics": score["metrics"]}, indent=2))
    same = score["metrics"] == report["metrics"] and score["counts"] == report["counts"]
    print("matches saved report:", same)
    return 0 if same else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="claimcheck")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-data").set_defaults(func=cmd_verify_data)
    sub.add_parser("init-db").set_defaults(func=cmd_init_db)
    run = sub.add_parser("run")
    run.add_argument("--agent-version", choices=config.AGENT_VERSIONS, required=True)
    run.add_argument("--split", choices=config.SPLITS, required=True)
    run.add_argument("--answers", help="comma-separated subset (debug runs only; saved under artifacts/scratch)")
    run.add_argument("--out", help="output directory for report.json / report.md / exchanges")
    run.add_argument("--no-db", action="store_true", help="do not persist to PostgreSQL")
    run.set_defaults(func=cmd_run)
    compare = sub.add_parser("compare")
    compare.add_argument("base")
    compare.add_argument("candidate")
    compare.add_argument("--out")
    compare.set_defaults(func=cmd_compare)
    rescore = sub.add_parser("rescore")
    rescore.add_argument("report")
    rescore.set_defaults(func=cmd_rescore)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
