"""Thin FastAPI service: POST /classify, POST /evaluation-runs, GET /evaluation-runs/{id}."""
from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import config, errors
from .agent import run_agent
from .data import Catalogue, load_answers, load_facts
from .db import RunStore
from .runner import execute_run
from .schemas import AgentInput, ClassifyRequest, EvaluationRunRequest


def error_response(status_code: int, error_type: str, message: str, fields: list[str] | None = None,
                   **extra) -> JSONResponse:
    error = {"type": error_type, "message": errors.sanitize(message)}
    if fields is not None:
        error["fields"] = fields
    return JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error, **extra}))


def _default_store_factory() -> RunStore:
    url = config.database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return RunStore(url)


def create_app(
    provider_factory: Callable[[], object] | None = None,
    store_factory: Callable[[], RunStore] | None = None,
    settings: config.Settings | None = None,
) -> FastAPI:
    settings = settings or config.load_settings()
    app = FastAPI(title="ClaimCheck", version="1.0.0")
    app.state.settings = settings
    app.state.catalogue = Catalogue(load_facts())
    app.state.answers = load_answers()

    def _live_provider():
        from .providers import build_provider

        return build_provider(settings)

    app.state.provider_factory = provider_factory or _live_provider
    app.state.store_factory = store_factory or _default_store_factory

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = sorted({".".join(str(p) for p in e.get("loc", ()) if p != "body") or "body" for e in exc.errors()})
        forbidden = sorted({".".join(str(p) for p in e.get("loc", ()) if p != "body")
                            for e in exc.errors() if e.get("type") == "extra_forbidden"})
        message = "request validation failed"
        if forbidden:
            message = "fields not accepted by this endpoint (gold, claim lists and labels are never inputs)"
        # Input values are deliberately not echoed back.
        return error_response(422, "validation_error", message, fields=fields)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "fact_version": config.FACT_VERSION, "dataset_version": config.DATASET_VERSION}

    @app.post("/classify")
    def classify(request: ClassifyRequest):
        catalogue: Catalogue = app.state.catalogue
        if request.brand_id not in catalogue.by_brand:
            return error_response(404, "unknown_brand", f"primary brand {request.brand_id[:40]!r} is not in the catalogue")
        try:
            provider = app.state.provider_factory()
        except RuntimeError as exc:
            return error_response(503, "provider_not_configured", str(exc))
        inp = AgentInput(**request.model_dump(exclude={"agent_version"}))
        result = run_agent(
            inp, request.agent_version, provider, catalogue,
            timeout_seconds=settings.timeout_seconds, max_turns=settings.max_model_turns,
        )
        if result.status != "ok":
            status_code = 504 if result.error_type == errors.PROVIDER_TIMEOUT else 502
            return error_response(status_code, result.error_type or "agent_error", result.error_message or "")
        return {
            "answer_id": inp.answer_id,
            "agent_version": request.agent_version,
            "claims": [c.model_dump() for c in result.claims],
            "model_turns": result.model_turns,
            "tool_calls": result.tool_calls,
            "latency_ms": result.latency_ms,
        }

    @app.post("/evaluation-runs", status_code=201)
    def create_evaluation_run(request: EvaluationRunRequest):
        try:
            store = app.state.store_factory()
        except Exception as exc:  # noqa: BLE001 - surfaced as a sanitized 503
            return error_response(503, "database_unavailable", str(exc))
        try:
            provider = app.state.provider_factory()
        except RuntimeError as exc:
            store.close()
            return error_response(503, "provider_not_configured", str(exc))
        try:
            report, _ = execute_run(
                agent_version=request.agent_version, split=request.split, provider=provider,
                settings=settings, catalogue=app.state.catalogue, answers=app.state.answers, store=store,
            )
        except Exception as exc:  # noqa: BLE001 - infrastructure failure: run is marked failed
            partial = getattr(exc, "partial_report", {}) or {}
            run_id = (partial.get("run") or {}).get("run_id")
            return error_response(500, "run_failed", f"{type(exc).__name__}", run_id=run_id, status="failed")
        finally:
            store.close()
        return {
            "run_id": report["run"]["run_id"],
            "status": report["run"]["status"],
            "agent_version": request.agent_version,
            "split": request.split,
            "counts": report["counts"],
            "metrics": report["metrics"],
            "errors_by_type": report["errors_by_type"],
        }

    @app.get("/evaluation-runs/{run_id}")
    def get_evaluation_run(run_id: UUID):
        try:
            store = app.state.store_factory()
        except Exception as exc:  # noqa: BLE001
            return error_response(503, "database_unavailable", str(exc))
        try:
            run = store.get_run(run_id)
        finally:
            store.close()
        if run is None:
            return error_response(404, "run_not_found", f"no evaluation run {run_id}")
        return jsonable_encoder(run)

    return app


def get_app() -> FastAPI:
    """uvicorn factory: `uvicorn claimcheck.api:get_app --factory`."""
    return create_app()
