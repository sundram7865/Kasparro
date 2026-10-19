import pytest

from claimcheck.schemas import Claim
from claimcheck.validation import ClaimValidationError, make_claim_id, validate_claims


def _claim(answer_id, text, start, end, label="supported", fact_ids=None, reason="Because.", claim_id=None, quote=None):
    return Claim(
        claim_id=claim_id or make_claim_id(answer_id, start, end),
        start_char=start,
        end_char=end,
        quote=text[start:end] if quote is None else quote,
        label=label,
        fact_ids=fact_ids or [],
        reason=reason,
    )


@pytest.fixture()
def a01(answers_by_id):
    return answers_by_id["A01"].ai_answer


def test_valid_claims_pass(a01, catalogue):
    claims = [
        _claim("A01", a01, 306, 460, fact_ids=["cleartrail.mini.price_2026", "cleartrail.plus.price_2026"]),
        _claim("A01", a01, 461, 647, label="contradicted", fact_ids=["cleartrail.mini.warranty_india"]),
    ]
    assert validate_claims("A01", a01, claims, catalogue.fact_ids) == claims


def test_empty_claim_list_is_structurally_valid(a01, catalogue):
    assert validate_claims("A01", a01, [], catalogue.fact_ids) == []


@pytest.mark.parametrize("start,end", [(-1, 10), (10, 10), (20, 10), (2400, 99999)])
def test_invalid_offsets_rejected(a01, catalogue, start, end):
    claim = Claim(claim_id=f"A01:{start}:{end}", start_char=start, end_char=end, quote="x",
                  label="unknown", fact_ids=[], reason="r")
    with pytest.raises(ClaimValidationError, match="outside answer"):
        validate_claims("A01", a01, [claim], catalogue.fact_ids)


def test_quote_must_equal_source_slice(a01, catalogue):
    bad = _claim("A01", a01, 306, 460, quote="For the current India catalogue, ClearTrail Mini is cheaper.")
    with pytest.raises(ClaimValidationError, match="quote does not equal"):
        validate_claims("A01", a01, [bad], catalogue.fact_ids)


def test_quote_with_surrounding_whitespace_rejected(a01, catalogue):
    # 647..649 is the paragraph break before the next sentence
    claim = _claim("A01", a01, 461, 649)
    with pytest.raises(ClaimValidationError, match="whitespace"):
        validate_claims("A01", a01, [claim], catalogue.fact_ids)


def test_duplicate_ids_rejected(a01, catalogue):
    c = _claim("A01", a01, 306, 460)
    with pytest.raises(ClaimValidationError, match="duplicate claim_id"):
        validate_claims("A01", a01, [c, c], catalogue.fact_ids)


def test_overlapping_spans_rejected(a01, catalogue):
    first = _claim("A01", a01, 306, 460)
    overlapping = _claim("A01", a01, 400, 647)
    with pytest.raises(ClaimValidationError, match="overlaps"):
        validate_claims("A01", a01, [first, overlapping], catalogue.fact_ids)


def test_out_of_order_claims_rejected(a01, catalogue):
    with pytest.raises(ClaimValidationError, match="increasing start_char"):
        validate_claims("A01", a01, [_claim("A01", a01, 461, 647), _claim("A01", a01, 306, 460)], catalogue.fact_ids)


def test_claim_id_must_be_derived_from_span(a01, catalogue):
    with pytest.raises(ClaimValidationError, match="claim_id must be"):
        validate_claims("A01", a01, [_claim("A01", a01, 306, 460, claim_id="A01:1:2")], catalogue.fact_ids)


def test_unknown_fact_ids_rejected(a01, catalogue):
    with pytest.raises(ClaimValidationError, match="unknown fact_ids"):
        validate_claims("A01", a01, [_claim("A01", a01, 306, 460, fact_ids=["cleartrail.mini.colour"])],
                        catalogue.fact_ids)


def test_unsupported_label_rejected_by_schema():
    with pytest.raises(ValueError):
        Claim(claim_id="A01:0:1", start_char=0, end_char=1, quote="S", label="true", fact_ids=[], reason="")


def test_reason_longer_than_two_sentences_rejected(a01, catalogue):
    claim = _claim("A01", a01, 306, 460, reason="One. Two. Three.")
    with pytest.raises(ClaimValidationError, match="two sentences"):
        validate_claims("A01", a01, [claim], catalogue.fact_ids)
