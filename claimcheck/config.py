"""Versions, paths and runtime settings (read from the environment / .env)."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "artifacts"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

ANSWERS_CSV = DATA_DIR / "answers.csv"
FACTS_CSV = DATA_DIR / "brand_facts.csv"
GOLD_CSV = DATA_DIR / "development_gold.csv"

DATASET_VERSION = "long-brand-answers-50-v4"
FACT_VERSION = "speaker-catalogue-v4"
EVALUATOR_VERSION = "sentence-spans-and-labels-v4"
AGENT_VERSIONS = ("v1", "v2")
SPLITS = ("development", "check")
LABELS = ("supported", "contradicted", "unknown")
MAX_MODEL_TURNS = 3

load_dotenv(ROOT / ".env")

# Every provider is reached through the OpenAI-compatible chat-completions tool-calling API.
PROVIDERS: dict[str, dict[str, str | None]] = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.5-flash",
    },
    "openai": {"base_url": None, "key_env": "OPENAI_API_KEY", "default_model": "gpt-4.1-mini"},
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "default_model": "openai/gpt-oss-120b",
    },
}


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    temperature: float
    timeout_seconds: float
    max_output_tokens: int
    max_model_turns: int
    max_retries: int
    min_request_interval_seconds: float
    reasoning_effort: str | None

    def public(self) -> dict:
        """Settings that are safe to store in run metadata (no secrets live here)."""
        return asdict(self)


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def load_settings() -> Settings:
    provider = _env("LLM_PROVIDER", "gemini").lower()
    if provider not in PROVIDERS:
        raise ValueError(f"LLM_PROVIDER must be one of {sorted(PROVIDERS)}")
    reasoning = _env("LLM_REASONING_EFFORT", "")
    return Settings(
        provider=provider,
        model=_env("LLM_MODEL", str(PROVIDERS[provider]["default_model"])),
        temperature=float(_env("LLM_TEMPERATURE", "0")),
        timeout_seconds=float(_env("PROVIDER_TIMEOUT_SECONDS", "120")),
        max_output_tokens=int(_env("LLM_MAX_OUTPUT_TOKENS", "16384")),
        max_model_turns=MAX_MODEL_TURNS,
        max_retries=int(_env("PROVIDER_MAX_RETRIES", "4")),
        min_request_interval_seconds=float(_env("MIN_REQUEST_INTERVAL_SECONDS", "0")),
        reasoning_effort=reasoning or None,
    )


def api_key_for(provider: str) -> str | None:
    return os.getenv(str(PROVIDERS[provider]["key_env"])) or None


def database_url() -> str | None:
    return os.getenv("DATABASE_URL") or None
