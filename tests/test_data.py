import csv
from datetime import date
from pathlib import Path

import pytest

from claimcheck import config
from claimcheck.data import (
    ANSWER_COLUMNS,
    DataError,
    dataset_hashes,
    load_answers,
    load_facts,
    parse_value,
)


def test_issued_files_parse_with_expected_counts(answers, catalogue, gold):
    assert len(answers) == 50
    assert sum(a.split == "development" for a in answers) == 40
    assert sum(a.split == "check" for a in answers) == 10
    assert [a.answer_id for a in answers if a.split == "check"] == [f"A{i}" for i in range(41, 51)]
    assert len(catalogue.facts) == 132
    assert len(gold) == 376
    assert catalogue.brands == ["cleartrail", "cloudnote", "stonewave"]


def test_quoted_commas_and_embedded_newlines_round_trip(tmp_path: Path):
    tricky = 'Price is INR 1,299, "quoted", and more.\n\nSecond paragraph,\r\nwith CRLF.  Trailing  spaces '
    path = tmp_path / "answers.csv"
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(ANSWER_COLUMNS)
        writer.writerow(["X01", "development", "cleartrail", "Q, with comma?", tricky])
        writer.writerow(["X02", "check", "cloudnote", "Q2", "Single line."])
    loaded = load_answers(path)
    assert len(loaded) == 2  # a line-based split would have produced more records
    assert loaded[0].ai_answer == tricky  # byte-for-byte, whitespace untouched
    assert loaded[0].question == "Q, with comma?"


def test_ai_answer_preserved_exactly_for_gold_offsets(answers_by_id, gold):
    for g in gold:
        assert answers_by_id[g.answer_id].ai_answer[g.start_char:g.end_char] == g.quote
    a01 = answers_by_id["A01"].ai_answer
    assert "\n\n" in a01 and "\r" not in a01
    assert a01.startswith("Start with the exact model name")


def test_boolean_values_are_parsed_not_truthy_strings(catalogue):
    assert parse_value("false", "boolean") is False
    assert parse_value("true", "boolean") is True
    with pytest.raises(DataError):
        parse_value("yes", "boolean")
    fact = catalogue.by_id["cleartrail.mini.immersion_allowed"]
    assert fact.value is False and fact.value_type == "boolean"
    assert catalogue.by_id["cloudnote.studio.wifi"].value is True


def test_numbers_strings_and_blank_optional_fields(catalogue):
    assert parse_value("1299", "number") == 1299 and isinstance(parse_value("1299", "number"), int)
    assert parse_value("1.5", "number") == 1.5
    bt = catalogue.by_id["cleartrail.mini.bluetooth_version"]
    assert bt.value == "5.3" and isinstance(bt.value, str)
    assert bt.unit is None and bt.condition is None  # blank means not applicable
    price = catalogue.by_id["stonewave.max.price_2026"]
    assert price.value == 3499 and price.unit == "INR"
    with pytest.raises(DataError):
        parse_value("1", "integer")


def test_validity_dates_are_inclusive(catalogue):
    p26 = catalogue.by_id["cleartrail.mini.price_2026"]
    p25 = catalogue.by_id["cleartrail.mini.price_2025"]
    assert p26.is_valid_on(date(2026, 10, 1)) and p26.is_valid_on(date(2026, 12, 31))
    assert not p26.is_valid_on(date(2027, 1, 1))
    assert p25.is_valid_on(date(2025, 12, 31)) and not p25.is_valid_on(date(2026, 1, 1))


def test_wrong_header_is_rejected(tmp_path: Path):
    path = tmp_path / "facts.csv"
    path.write_text("fact_id,brand_id\nx,y\n", encoding="utf-8")
    with pytest.raises(DataError):
        load_facts(path)


def test_dataset_hashes_match_recorded_checksums():
    recorded = {}
    for line in (config.DATA_DIR / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split()
        recorded[Path(name).name] = digest
    assert dataset_hashes() == recorded
