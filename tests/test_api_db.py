"""API validation, PostgreSQL persistence and joined retrieval (real database, fake provider)."""
import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from claimcheck import config
from claimcheck.api import create_app
from claimcheck.db import RunStore
from claimcheck.errors import ProviderError
from claimcheck.providers.fake import RuleBasedProvider, ScriptedProvider, text_turn, timeout_error, tool_turn

MODEL_WORDS = ("ClearTrail", "CloudNote", "StoneWave")


def decide(answer_id, _sid, text):
    """Gold-free fake policy: product sentences are claims; A05 returns a valid empty list."""
    if answer_id == "A05":
        return None
    if any(w in text for w in MODEL_WORDS) and not text.startswith("Keep the exact model"):
        return "contradicted" if " not " in text else "supported"
    return None


@pytest.fixture()
def app(test_db_url):
    return create_app(
        provider_factory=lambda: RuleBasedProvider(decide, failures={"A03": ProviderError("HTTP 503: overloaded"),
                                                                     "A42": "invalid"}),
        store_factory=lambda: RunStore(test_db_url),
        settings=config.load_settings(),
    )


@pytest.fixture()
def client(app):
    return TestClient(app)


def _classify_body(answers_by_id, **overrides):
    a = answers_by_id["A01"]
    body = {"answer_id": a.answer_id, "brand_id": a.brand_id, "question": a.question,
            "ai_answer": a.ai_answer, "agent_version": "v1"}
    body.update(overrides)
    return body


# --- POST /classify ----------------------------------------------------------------------

def test_classify_success(client, answers_by_id):
    response = client.post("/classify", json=_classify_body(answers_by_id))
    assert response.status_code == 200
    body = response.json()
    assert body["answer_id"] == "A01" and body["claims"]
    text = answers_by_id["A01"].ai_answer
    for claim in body["claims"]:
        assert text[claim["start_char"]:claim["end_char"]] == claim["quote"]
        assert claim["claim_id"] == f"A01:{claim['start_char']}:{claim['end_char']}"


@pytest.mark.parametrize("field", ["claims", "gold", "expected_label", "gold_spans", "labels"])
def test_classify_rejects_gold_or_claim_list_inputs(client, answers_by_id, field):
    response = client.post("/classify", json=_classify_body(answers_by_id, **{field: []}))
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["type"] == "validation_error" and field in error["fields"]
    assert answers_by_id["A01"].ai_answer[:40] not in response.text  # input is not echoed


@pytest.mark.parametrize("override", [{"agent_version": "v3"}, {"ai_answer": ""}, {"answer_id": None}])
def test_classify_invalid_request(client, answers_by_id, override):
    assert client.post("/classify", json=_classify_body(answers_by_id, **override)).status_code == 422


def test_classify_unknown_primary_brand_404(client, answers_by_id):
    response = client.post("/classify", json=_classify_body(answers_by_id, brand_id="rivalsound"))
    assert response.status_code == 404 and response.json()["error"]["type"] == "unknown_brand"


@pytest.mark.parametrize(
    "script, status, error_type",
    [
        ([tool_turn(("get_brand_facts", {"brand_id": "cleartrail"})), text_turn("nope")], 502, "invalid_output"),
        ([tool_turn(("run_shell", {"brand_id": "cleartrail"}))], 502, "illegal_tool"),
        ([ProviderError("HTTP 500: boom")], 502, "provider_error"),
        ([timeout_error()], 504, "provider_timeout"),
    ],
)
def test_classify_provider_and_output_failures(app, client, answers_by_id, script, status, error_type):
    app.state.provider_factory = lambda: ScriptedProvider(list(script))
    response = client.post("/classify", json=_classify_body(answers_by_id))
    assert response.status_code == status
    assert response.json() == {"error": {"type": error_type, "message": response.json()["error"]["message"]}}


# --- evaluation runs + persistence ----------------------------------------------------------

def test_development_run_persists_and_retrieves_joined(client, test_db_url):
    response = client.post("/evaluation-runs", json={"agent_version": "v1", "split": "development"})
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["status"] == "completed" and created["split"] == "development"
    counts = created["counts"]
    assert counts["scheduled_answers"] == 40 and counts["error_answers"] == 1 and counts["empty_answers"] == 1
    assert counts["G"] == 376 and counts["P"] > 0
    assert created["metrics"]["joint"]["f1"] is not None
    assert created["errors_by_type"] == {"provider_error": 1}

    fetched = client.get(f"/evaluation-runs/{created['run_id']}")
    assert fetched.status_code == 200
    run = fetched.json()
    assert run["run_id"] == created["run_id"] and run["status"] == "completed"
    assert run["metrics"] == created["metrics"] and run["counts"] == created["counts"]
    assert run["file_hashes"] and run["prompt_version"].startswith("v1-")
    assert run["settings"]["provider"] == "fake"
    ids = [a["answer_id"] for a in run["answers"]]
    assert ids == [f"A{i:02d}" for i in range(1, 41)]  # one terminal row per scheduled answer, stable order
    by_id = {a["answer_id"]: a for a in run["answers"]}
    assert by_id["A03"]["status"] == "error" and by_id["A03"]["error_type"] == "provider_error"
    assert by_id["A03"]["claims"] == []
    assert by_id["A05"]["status"] == "ok" and by_id["A05"]["claims"] == []  # valid empty output kept
    total = 0
    for answer in run["answers"]:
        starts = [c["start_char"] for c in answer["claims"]]
        assert starts == sorted(starts)
        assert answer["claim_count"] == len(answer["claims"])
        total += len(answer["claims"])
        for c in answer["claims"]:
            assert c["matched_gold"] is not None  # development rows carry their match
            if c["matched_gold"]:
                assert c["expected_label"] in ("supported", "contradicted", "unknown")
    assert total == counts["P"]
    matched = sum(c["matched_gold"] for a in run["answers"] for c in a["claims"])
    correct = sum(bool(c["label_correct"]) for a in run["answers"] for c in a["claims"])
    assert (matched, correct) == (counts["M"], counts["C"])
    assert run["scoring"]["answer_error_ids"] == ["A03"]


def test_check_run_keeps_quality_null(client):
    response = client.post("/evaluation-runs", json={"agent_version": "v2", "split": "check"})
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["metrics"] is None
    assert created["counts"]["G"] is None and created["counts"]["M"] is None and created["counts"]["C"] is None
    assert created["counts"]["scheduled_answers"] == 10 and created["counts"]["error_answers"] == 1  # A42 invalid
    run = client.get(f"/evaluation-runs/{created['run_id']}").json()
    assert run["metrics"] is None and run["scoring"] is None
    assert all(c["matched_gold"] is None and c["expected_label"] is None
               for a in run["answers"] for c in a["claims"])
    a42 = next(a for a in run["answers"] if a["answer_id"] == "A42")
    assert a42["status"] == "error" and a42["error_type"] == "invalid_output"


def test_evaluation_run_validation(client):
    assert client.post("/evaluation-runs", json={"agent_version": "v1", "split": "final"}).status_code == 422
    assert client.post("/evaluation-runs", json={"agent_version": "v9", "split": "check"}).status_code == 422
    body = {"agent_version": "v1", "split": "check", "gold": []}
    assert client.post("/evaluation-runs", json=body).status_code == 422


def test_get_run_missing_and_invalid_uuid(client):
    missing = client.get(f"/evaluation-runs/{uuid.uuid4()}")
    assert missing.status_code == 404 and missing.json()["error"]["type"] == "run_not_found"
    assert client.get("/evaluation-runs/not-a-uuid").status_code == 422


def test_infrastructure_failure_marks_run_failed_and_keeps_partial_evidence(app, client, test_db_url):
    class FlakyStore(RunStore):
        def save_answer(self, run_id, position, brand_id, result):
            if position == 3:
                raise psycopg.OperationalError("simulated database outage")
            super().save_answer(run_id, position, brand_id, result)

    app.state.store_factory = lambda: FlakyStore(test_db_url)
    response = client.post("/evaluation-runs", json={"agent_version": "v1", "split": "check"})
    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "failed" and body["error"]["type"] == "run_failed"
    app.state.store_factory = lambda: RunStore(test_db_url)
    run = client.get(f"/evaluation-runs/{body['run_id']}").json()
    assert run["status"] == "failed" and run["error"]
    assert [a["answer_id"] for a in run["answers"]] == ["A41", "A42"]  # partial evidence preserved


# --- database constraints ------------------------------------------------------------------

def test_database_constraints(test_db_url):
    run_id = str(uuid.uuid4())
    with psycopg.connect(test_db_url, autocommit=True) as conn:
        conn.execute(
            """INSERT INTO runs (run_id, split, agent_version, prompt_version, dataset_version, evaluator_version,
                                 fact_version, provider, model, settings, file_hashes, status)
               VALUES (%s, 'check', 'v1', 'p', 'd', 'e', 'f', 'fake', 'm', %s, %s, 'running')""",
            (run_id, Jsonb({}), Jsonb({})),
        )
        insert_answer = """INSERT INTO answer_results (run_id, answer_id, position, brand_id, status)
                           VALUES (%s, 'A41', 1, 'stonewave', 'ok')"""
        conn.execute(insert_answer, (run_id,))
        with pytest.raises(psycopg.errors.UniqueViolation):
            conn.execute(insert_answer, (run_id,))
        insert_claim = """INSERT INTO claim_results (run_id, answer_id, claim_id, start_char, end_char, quote,
                                                    label, fact_ids, reason)
                          VALUES (%s, %s, %s, 10, 20, 'q', 'unknown', %s, 'r')"""
        conn.execute(insert_claim, (run_id, "A41", "A41:10:20", Jsonb([])))
        with pytest.raises(psycopg.errors.UniqueViolation):
            conn.execute(insert_claim, (run_id, "A41", "A41:10:20b", Jsonb([])))
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            conn.execute(insert_claim, (run_id, "A99", "A99:10:20", Jsonb([])))
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                """INSERT INTO claim_results (run_id, answer_id, claim_id, start_char, end_char, quote, label,
                                              fact_ids, reason)
                   VALUES (%s, 'A41', 'x', 30, 40, 'q', 'maybe', %s, 'r')""",
                (run_id, Jsonb([])),
            )
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                """INSERT INTO answer_results (run_id, answer_id, position, brand_id, status)
                   VALUES (%s, 'A42', 2, 'cleartrail', 'error')""",  # error rows must carry an error_type
                (run_id,),
            )
        rows = conn.execute("SELECT count(*) FROM claim_results WHERE run_id = %s", (run_id,)).fetchone()
        assert rows[0] == 1
