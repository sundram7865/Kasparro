# Run report: v1 / development

- run_id: `2e8de0a7-8413-4dee-b04e-591ffa7e8aa6`
- status: **completed**
- provider / model: `gemini` / `gemini-3.8-flash`
- prompt_version: `v1-d858d0abad7f`
- dataset / fact / evaluator: `long-brand-answers-50-v4` / `speaker-catalogue-v4` / `sentence-spans-and-labels-v4`
- source_revision: `dcf44bfcf8a1ed07a6526cfd2da92a90c413475c`
- started / finished: 2026-10-19 11:20:54.975606+00:00 / 2026-10-19 11:22:26.564277+00:00 (91.6 s)
- settings: `{"provider": "gemini", "model": "gemini-3.8-flash", "temperature": 0.0, "timeout_seconds": 120.0, "max_output_tokens": 16384, "max_model_turns": 3, "max_retries": 4, "min_request_interval_seconds": 2.0, "reasoning_effort": null, "sequential": true, "answer_subset": ["A01", "A07", "A24"]}`
- file hashes (sha256): `{"answers.csv": "fa28e813ea54b4e5ea985585f22f084d826241e1182accbc27ace17066125724", "brand_facts.csv": "2190d40fad2dd167ef2437956c43d595aaf2554ea673a4789b9343cb7e2936f2", "development_gold.csv": "afe84cc78f304afb6a4aaa505dd7504af80fcbf8bc507806aa5ff0aab6bf4850"}`

## Counts

| scheduled | ok | errors | empty | G | P | M | C |
|---|---|---|---|---|---|---|---|
| 3 | 3 | 0 | 0 | 27 | 27 | 27 | 27 |

Predicted label counts: `{"supported": 10, "contradicted": 7, "unknown": 10}`

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction (span match) | 1.0000 | 1.0000 | 1.0000 |
| **joint (span + label)** | 1.0000 | 1.0000 | **1.0000** |

Gold claim coverage C/G: **1.0000**

## Answer errors

None.

## Confusion matrix (matched claims, rows = expected, columns = predicted)

| expected \ predicted | supported | contradicted | unknown |
|---|---|---|---|
| supported | 10 | 0 | 0 |
| contradicted | 0 | 7 | 0 |
| unknown | 0 | 0 | 10 |

## Joint recall by difficulty tag

| tag | correct | gold |
|---|---|---|
| arithmetic | 2 | 2 |
| box_scope | 1 | 1 |
| comparison | 1 | 1 |
| condition_swap | 1 | 1 |
| cross_brand_comparison | 1 | 1 |
| date_scope | 2 | 2 |
| explicit_false | 2 | 2 |
| feature_conflation | 2 | 2 |
| feature_scope | 1 | 1 |
| inference | 1 | 1 |
| missing_fact | 2 | 2 |
| model_scope | 2 | 2 |
| negation | 2 | 2 |
| policy_scope | 6 | 6 |
| policy_vs_capability | 1 | 1 |
| price | 1 | 1 |
| qualification | 1 | 1 |
| region_scope | 1 | 1 |
| requirement_vs_availability | 1 | 1 |
| scope | 2 | 2 |
| unit_conversion | 2 | 2 |
| variant_transfer | 1 | 1 |

## Wrong-label matches (0)


## Missed gold claims (0)


## Unmatched (extra) predictions (0)


## Per-answer outcomes

| answer | status | claims | turns | latency ms | tools |
|---|---|---|---|---|---|
| A01 | ok | 9 | 2 | 23402 | get_brand_facts(cleartrail) |
| A07 | ok | 8 | 2 | 36029 | get_brand_facts(cleartrail) |
| A24 | ok | 10 | 2 | 32105 | get_brand_facts(cloudnote) |

Full predictions (spans, quotes, labels, fact_ids, reasons) are in `report.json`.
