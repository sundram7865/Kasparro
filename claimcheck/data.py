"""CSV loading with a real parser, exact text preservation and typed fact values."""
from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import config

ANSWER_COLUMNS = ["answer_id", "split", "brand_id", "question", "ai_answer"]
FACT_COLUMNS = [
    "fact_id", "brand_id", "model_id", "field", "value", "value_type",
    "unit", "condition", "valid_from", "valid_to",
]
GOLD_COLUMNS = [
    "answer_id", "claim_id", "start_char", "end_char", "quote", "expected_label",
    "evidence_fact_ids", "explanation", "difficulty_tags",
]

FactValue = int | float | bool | str


class DataError(ValueError):
    pass


@dataclass(frozen=True)
class Answer:
    answer_id: str
    split: str
    brand_id: str
    question: str
    ai_answer: str


@dataclass(frozen=True)
class Fact:
    fact_id: str
    brand_id: str
    model_id: str
    field: str
    value: FactValue
    value_type: str
    unit: str | None
    condition: str | None
    valid_from: date
    valid_to: date

    def is_valid_on(self, day: date) -> bool:
        return self.valid_from <= day <= self.valid_to  # inclusive endpoints

    def to_tool_row(self) -> dict:
        return {
            "fact_id": self.fact_id,
            "model_id": self.model_id,
            "field": self.field,
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "condition": self.condition,
            "valid_from": self.valid_from.isoformat(),
            "valid_to": self.valid_to.isoformat(),
        }


@dataclass(frozen=True)
class GoldClaim:
    answer_id: str
    claim_id: str
    start_char: int
    end_char: int
    quote: str
    expected_label: str
    evidence_fact_ids: tuple[str, ...]
    explanation: str
    difficulty_tags: tuple[str, ...]


def _read_rows(path: Path, expected_columns: list[str]) -> list[dict[str, str]]:
    # newline="" lets the csv module keep embedded line breaks inside quoted fields;
    # utf-8-sig tolerates an optional BOM without touching field contents.
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_columns:
            raise DataError(f"{path.name}: expected columns {expected_columns}, got {reader.fieldnames}")
        rows = list(reader)
    for index, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            raise DataError(f"{path.name}: malformed record near line {index}")
    return rows


def parse_value(raw: str, value_type: str) -> FactValue:
    if value_type == "number":
        if re.fullmatch(r"-?\d+", raw):
            return int(raw)
        return float(raw)
    if value_type == "boolean":
        lowered = raw.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise DataError(f"boolean value must be true or false, got {raw!r}")
    if value_type == "string":
        return raw
    raise DataError(f"unknown value_type {value_type!r}")


def _optional(raw: str) -> str | None:
    return raw if raw.strip() else None


def load_answers(path: Path = config.ANSWERS_CSV) -> list[Answer]:
    answers = [Answer(**row) for row in _read_rows(path, ANSWER_COLUMNS)]
    ids = [a.answer_id for a in answers]
    if len(ids) != len(set(ids)):
        raise DataError("duplicate answer_id in answers.csv")
    for answer in answers:
        if answer.split not in config.SPLITS:
            raise DataError(f"{answer.answer_id}: unknown split {answer.split!r}")
    return answers


def load_facts(path: Path = config.FACTS_CSV) -> list[Fact]:
    facts = []
    for row in _read_rows(path, FACT_COLUMNS):
        facts.append(
            Fact(
                fact_id=row["fact_id"],
                brand_id=row["brand_id"],
                model_id=row["model_id"],
                field=row["field"],
                value=parse_value(row["value"], row["value_type"]),
                value_type=row["value_type"],
                unit=_optional(row["unit"]),
                condition=_optional(row["condition"]),
                valid_from=date.fromisoformat(row["valid_from"]),
                valid_to=date.fromisoformat(row["valid_to"]),
            )
        )
    ids = [f.fact_id for f in facts]
    if len(ids) != len(set(ids)):
        raise DataError("duplicate fact_id in brand_facts.csv")
    return facts


def load_gold(path: Path = config.GOLD_CSV) -> list[GoldClaim]:
    gold = []
    for row in _read_rows(path, GOLD_COLUMNS):
        gold.append(
            GoldClaim(
                answer_id=row["answer_id"],
                claim_id=row["claim_id"],
                start_char=int(row["start_char"]),
                end_char=int(row["end_char"]),
                quote=row["quote"],
                expected_label=row["expected_label"],
                evidence_fact_ids=tuple(x for x in row["evidence_fact_ids"].split("|") if x),
                explanation=row["explanation"],
                difficulty_tags=tuple(x for x in row["difficulty_tags"].split("|") if x),
            )
        )
    return gold


class Catalogue:
    """Read-only view of the fact catalogue."""

    def __init__(self, facts: list[Fact]):
        self.facts = list(facts)
        self.by_id = {f.fact_id: f for f in self.facts}
        self.by_brand: dict[str, list[Fact]] = {}
        for fact in self.facts:
            self.by_brand.setdefault(fact.brand_id, []).append(fact)

    @property
    def brands(self) -> list[str]:
        return sorted(self.by_brand)

    @property
    def fact_ids(self) -> set[str]:
        return set(self.by_id)

    def facts_for_brand(self, brand_id: str) -> list[Fact]:
        return list(self.by_brand.get(brand_id, []))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dataset_hashes() -> dict[str, str]:
    return {p.name: sha256_file(p) for p in (config.ANSWERS_CSV, config.FACTS_CSV, config.GOLD_CSV)}
