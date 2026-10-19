import pytest

from claimcheck.data import GoldClaim
from claimcheck.schemas import Claim
from claimcheck.scoring import AnswerOutcome, ScoringError, score_split
from claimcheck.segment import split_sentences
from claimcheck.validation import make_claim_id

TEXT_A = "Alpha costs 10. Beta costs 20. Gamma costs 30. Buy what you like."
TEXT_B = "Delta weighs 5 kg. Epsilon weighs 6 kg. Compare carefully."
TEXTS = {"X1": TEXT_A, "X2": TEXT_B}


def _spans(text):
    return [(s.start, s.end) for s in split_sentences(text)]


def _gold(answer_id, index, label):
    s, e = _spans(TEXTS[answer_id])[index]
    return GoldClaim(answer_id, make_claim_id(answer_id, s, e), s, e, TEXTS[answer_id][s:e], label, (), "", ("tag",))


def _pred(answer_id, index, label, start_shift=0):
    s, e = _spans(TEXTS[answer_id])[index]
    s += start_shift
    return Claim(claim_id=make_claim_id(answer_id, s, e), start_char=s, end_char=e,
                 quote=TEXTS[answer_id][s:e], label=label, fact_ids=[], reason="r")


GOLD = [
    _gold("X1", 0, "supported"),
    _gold("X1", 1, "contradicted"),
    _gold("X1", 2, "unknown"),
    _gold("X2", 0, "supported"),
    _gold("X2", 1, "unknown"),
]
SCHEDULED = ["X1", "X2"]


def perfect_outcomes():
    return [
        AnswerOutcome("X1", "ok", [_pred("X1", 0, "supported"), _pred("X1", 1, "contradicted"), _pred("X1", 2, "unknown")]),
        AnswerOutcome("X2", "ok", [_pred("X2", 0, "supported"), _pred("X2", 1, "unknown")]),
    ]


def test_perfect_output():
    score = score_split(TEXTS, SCHEDULED, perfect_outcomes(), GOLD)
    assert (score["counts"]["G"], score["counts"]["P"], score["counts"]["M"], score["counts"]["C"]) == (5, 5, 5, 5)
    assert score["metrics"]["extraction"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert score["metrics"]["joint"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert score["details"]["missed_gold"] == [] and score["details"]["unmatched_predictions"] == []


def test_missed_claims_lower_recall():
    outcomes = perfect_outcomes()
    outcomes[0].claims = outcomes[0].claims[:1]  # misses two X1 claims
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert (score["counts"]["P"], score["counts"]["M"], score["counts"]["C"]) == (3, 3, 3)
    assert score["metrics"]["extraction"]["precision"] == 1.0
    assert score["metrics"]["extraction"]["recall"] == pytest.approx(0.6)
    assert score["metrics"]["joint"]["f1"] == pytest.approx(2 * 3 / (3 + 5))
    assert {m["gold_claim_id"] for m in score["details"]["missed_gold"]} == {GOLD[1].claim_id, GOLD[2].claim_id}


def test_extra_advice_prediction_lowers_precision():
    outcomes = perfect_outcomes()
    outcomes[0].claims.append(_pred("X1", 3, "unknown"))  # "Buy what you like." is advice
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert (score["counts"]["P"], score["counts"]["M"]) == (6, 5)
    assert score["metrics"]["extraction"]["precision"] == pytest.approx(5 / 6)
    assert score["metrics"]["extraction"]["recall"] == 1.0
    assert [u["claim_id"] for u in score["details"]["unmatched_predictions"]] == [outcomes[0].claims[-1].claim_id]


def test_wrong_labels_count_as_matches_but_not_correct():
    outcomes = perfect_outcomes()
    outcomes[1].claims[1] = _pred("X2", 1, "contradicted")
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert (score["counts"]["M"], score["counts"]["C"]) == (5, 4)
    assert score["metrics"]["extraction"]["f1"] == 1.0
    assert score["metrics"]["joint"]["f1"] == pytest.approx(0.8)
    wrong = score["details"]["wrong_label"]
    assert len(wrong) == 1 and wrong[0]["expected_label"] == "unknown" and wrong[0]["predicted_label"] == "contradicted"


def test_provider_error_answer_keeps_its_gold_as_missed():
    outcomes = [perfect_outcomes()[0], AnswerOutcome("X2", "error", [], "provider_error", "HTTP 500")]
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert (score["counts"]["G"], score["counts"]["P"], score["counts"]["M"]) == (5, 3, 3)
    assert score["counts"]["error_answers"] == 1
    assert score["errors_by_type"] == {"provider_error": 1}
    assert score["metrics"]["joint"]["recall"] == pytest.approx(0.6)
    assert all(m["answer_error"] for m in score["details"]["missed_gold"])


def test_valid_empty_predictions_get_zero_not_null():
    outcomes = [AnswerOutcome("X1", "ok", []), AnswerOutcome("X2", "ok", [])]
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert score["counts"]["P"] == 0 and score["counts"]["empty_answers"] == 2
    assert score["metrics"]["extraction"] == {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    assert score["metrics"]["joint"] == {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    assert score["metrics"]["gold_claim_coverage"] == 0.0


def test_spec_arithmetic_example_g10_p10_m8_c7():
    text = " ".join(f"Item {i} costs {i}." for i in range(12))
    texts = {"Y": text}
    spans = [(s.start, s.end) for s in split_sentences(text)]
    gold = [GoldClaim("Y", make_claim_id("Y", s, e), s, e, text[s:e], "supported", (), "", ()) for s, e in spans[:10]]
    preds = []
    for i, (s, e) in enumerate(spans[:8]):  # 8 exact matches, 7 with the right label
        preds.append(Claim(claim_id=make_claim_id("Y", s, e), start_char=s, end_char=e, quote=text[s:e],
                           label="supported" if i < 7 else "unknown", fact_ids=[], reason="r"))
    for s, e in spans[10:12]:  # 2 extra predictions
        preds.append(Claim(claim_id=make_claim_id("Y", s, e), start_char=s, end_char=e, quote=text[s:e],
                           label="supported", fact_ids=[], reason="r"))
    score = score_split(texts, ["Y"], [AnswerOutcome("Y", "ok", preds)], gold)
    c = score["counts"]
    assert (c["G"], c["P"], c["M"], c["C"]) == (10, 10, 8, 7)
    assert score["metrics"]["extraction"] == {"precision": 0.8, "recall": 0.8, "f1": 0.8}
    assert score["metrics"]["joint"] == {"precision": 0.7, "recall": 0.7, "f1": 0.7}
    # matched-only label accuracy (7/8 = 0.875) is NOT the reported quality
    assert 0.875 not in score["metrics"]["joint"].values()


def test_partial_sentence_does_not_match():
    outcomes = perfect_outcomes()
    outcomes[0].claims[0] = _pred("X1", 0, "supported", start_shift=6)  # "costs 10." fragment
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert score["counts"]["M"] == 4
    assert GOLD[0].claim_id in {m["gold_claim_id"] for m in score["details"]["missed_gold"]}


def test_quote_mismatch_never_matches():
    outcomes = perfect_outcomes()
    claim = outcomes[0].claims[0]
    outcomes[0].claims[0] = claim.model_copy(update={"quote": "Alpha costs 99."})
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert score["counts"]["M"] == 4
    assert score["details"]["invalid_quote_prediction_ids"] == [claim.claim_id]


def test_each_gold_matches_at_most_one_prediction():
    outcomes = perfect_outcomes()
    outcomes[1].claims.insert(1, _pred("X2", 0, "supported"))
    score = score_split(TEXTS, SCHEDULED, outcomes, GOLD)
    assert (score["counts"]["P"], score["counts"]["M"]) == (6, 5)


def test_missing_answer_outcome_rejected():
    with pytest.raises(ScoringError, match="missing"):
        score_split(TEXTS, SCHEDULED, perfect_outcomes()[:1], GOLD)


def test_duplicated_answer_outcome_rejected():
    outcomes = perfect_outcomes() + [AnswerOutcome("X2", "ok", [])]
    with pytest.raises(ScoringError, match="duplicated"):
        score_split(TEXTS, SCHEDULED, outcomes, GOLD)


def test_unexpected_answer_outcome_rejected():
    outcomes = perfect_outcomes() + [AnswerOutcome("X9", "ok", [])]
    with pytest.raises(ScoringError, match="unexpected"):
        score_split(TEXTS, SCHEDULED, outcomes, GOLD)


def test_error_outcome_cannot_carry_claims():
    outcomes = [perfect_outcomes()[0], AnswerOutcome("X2", "error", [_pred("X2", 0, "supported")], "invalid_output")]
    with pytest.raises(ScoringError, match="cannot carry"):
        score_split(TEXTS, SCHEDULED, outcomes, GOLD)


def test_check_split_quality_stays_null():
    score = score_split(TEXTS, SCHEDULED, perfect_outcomes(), None)
    assert score["metrics"] is None and score["details"] is None
    assert (score["counts"]["G"], score["counts"]["M"], score["counts"]["C"]) == (None, None, None)
    assert score["counts"]["P"] == 5


def test_empty_scheduled_split_has_null_metrics():
    score = score_split(TEXTS, [], [], GOLD)
    assert score["metrics"] is None and score["counts"]["scheduled_answers"] == 0


def test_real_gold_scored_against_itself_is_perfect(answers_by_id, gold):
    dev_ids = sorted({g.answer_id for g in gold})
    outcomes = [
        AnswerOutcome(aid, "ok", [
            Claim(claim_id=g.claim_id, start_char=g.start_char, end_char=g.end_char, quote=g.quote,
                  label=g.expected_label, fact_ids=list(g.evidence_fact_ids), reason="gold")
            for g in gold if g.answer_id == aid
        ])
        for aid in dev_ids
    ]
    texts = {aid: answers_by_id[aid].ai_answer for aid in dev_ids}
    score = score_split(texts, dev_ids, outcomes, gold)
    assert len(dev_ids) == 40
    assert (score["counts"]["G"], score["counts"]["C"]) == (376, 376)
    assert score["metrics"]["joint"]["f1"] == 1.0
