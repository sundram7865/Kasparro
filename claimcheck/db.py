"""PostgreSQL persistence for runs, answer outcomes and predicted claims (psycopg 3)."""
from __future__ import annotations

from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def connect(database_url: str) -> psycopg.Connection:
    # autocommit: each `with conn.transaction()` block is its own committed transaction.
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=10, autocommit=True)


def init_schema(database_url: str) -> None:
    with connect(database_url) as conn:
        conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


class RunStore:
    """Small repository over one connection; every write commits immediately so a
    crashed run keeps its partial evidence."""

    def __init__(self, database_url: str):
        self.conn = connect(database_url)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- writes -----------------------------------------------------------------
    def create_run(self, meta: dict) -> None:
        with self.conn.transaction():
            self.conn.execute(
                """
                INSERT INTO runs (run_id, split, agent_version, prompt_version, dataset_version,
                                  evaluator_version, fact_version, provider, model, settings,
                                  source_revision, file_hashes, status, started_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'running', %s)
                """,
                (
                    meta["run_id"], meta["split"], meta["agent_version"], meta["prompt_version"],
                    meta["dataset_version"], meta["evaluator_version"], meta["fact_version"],
                    meta["provider"], meta["model"], Jsonb(meta["settings"]), meta.get("source_revision"),
                    Jsonb(meta["file_hashes"]), meta["started_at"],
                ),
            )

    def save_answer(self, run_id: str, position: int, brand_id: str, result) -> None:
        """Insert one terminal answer row and its accepted claims atomically."""
        with self.conn.transaction():
            self.conn.execute(
                """
                INSERT INTO answer_results (run_id, answer_id, position, brand_id, status, error_type,
                                            error_message, claim_count, latency_ms, model_turns,
                                            tool_calls, usage, trace_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id, result.answer_id, position, brand_id, result.status, result.error_type,
                    result.error_message, len(result.claims), result.latency_ms, result.model_turns,
                    Jsonb(result.tool_calls), Jsonb(result.usage), getattr(result, "trace_ref", None),
                ),
            )
            if result.claims:
                with self.conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO claim_results (run_id, answer_id, claim_id, start_char, end_char,
                                                   quote, label, fact_ids, reason)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            (run_id, result.answer_id, c.claim_id, c.start_char, c.end_char, c.quote,
                             c.label, Jsonb(c.fact_ids), c.reason)
                            for c in result.claims
                        ],
                    )

    def finish_run(self, run_id: str, counts: dict, metrics: dict | None, scoring: dict | None,
                   matches: list[dict] | None, finished_at) -> None:
        with self.conn.transaction():
            if matches is not None:
                with self.conn.cursor() as cur:
                    # Development only: mark every stored claim, then fill in exact-span matches.
                    cur.execute(
                        "UPDATE claim_results SET matched_gold = FALSE WHERE run_id = %s", (run_id,)
                    )
                    cur.executemany(
                        """
                        UPDATE claim_results
                           SET matched_gold = TRUE, expected_label = %s, label_correct = %s
                         WHERE run_id = %s AND claim_id = %s
                        """,
                        [(m["expected_label"], m["correct"], run_id, m["claim_id"]) for m in matches],
                    )
            self.conn.execute(
                """
                UPDATE runs SET status = 'completed', counts = %s, metrics = %s, scoring = %s,
                                finished_at = %s
                 WHERE run_id = %s
                """,
                (Jsonb(counts), Jsonb(metrics) if metrics is not None else None,
                 Jsonb(scoring) if scoring is not None else None, finished_at, run_id),
            )

    def fail_run(self, run_id: str, error: str, finished_at) -> None:
        with self.conn.transaction():
            self.conn.execute(
                "UPDATE runs SET status = 'failed', error = %s, finished_at = %s WHERE run_id = %s",
                (error, finished_at, run_id),
            )

    # -- reads ------------------------------------------------------------------
    def get_run(self, run_id: UUID | str) -> dict | None:
        run = self.conn.execute(
            """
            SELECT run_id, split, agent_version, prompt_version, dataset_version, evaluator_version,
                   fact_version, provider, model, settings, source_revision, file_hashes, status,
                   counts, metrics, scoring, error, started_at, finished_at
              FROM runs WHERE run_id = %s
            """,
            (str(run_id),),
        ).fetchone()
        if run is None:
            return None
        rows = self.conn.execute(
            """
            SELECT a.answer_id, a.position, a.brand_id, a.status, a.error_type, a.error_message,
                   a.claim_count, a.latency_ms, a.model_turns, a.tool_calls, a.trace_ref,
                   c.claim_id, c.start_char, c.end_char, c.quote, c.label, c.fact_ids, c.reason,
                   c.matched_gold, c.expected_label, c.label_correct
              FROM answer_results a
              LEFT JOIN claim_results c ON c.run_id = a.run_id AND c.answer_id = a.answer_id
             WHERE a.run_id = %s
             ORDER BY a.position, a.answer_id, c.start_char NULLS FIRST, c.end_char
            """,
            (str(run_id),),
        ).fetchall()
        answers: dict[str, dict] = {}
        for row in rows:
            answer = answers.get(row["answer_id"])
            if answer is None:
                answer = {
                    key: row[key]
                    for key in ("answer_id", "position", "brand_id", "status", "error_type", "error_message",
                                "claim_count", "latency_ms", "model_turns", "tool_calls", "trace_ref")
                }
                answer["claims"] = []
                answers[row["answer_id"]] = answer
            if row["claim_id"] is not None:
                answer["claims"].append(
                    {key: row[key] for key in ("claim_id", "start_char", "end_char", "quote", "label", "fact_ids",
                                               "reason", "matched_gold", "expected_label", "label_correct")}
                )
        run["run_id"] = str(run["run_id"])
        run["answers"] = list(answers.values())
        return run
