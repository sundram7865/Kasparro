# Run report: v1 / development

- run_id: `3b8853b1-90e9-4158-a5e0-7920b3e644fd`
- status: **completed**
- provider / model: `gemini` / `gemini-3.1-flash-lite`
- prompt_version: `v1-d858d0abad7f`
- dataset / fact / evaluator: `long-brand-answers-50-v4` / `speaker-catalogue-v4` / `sentence-spans-and-labels-v4`
- source_revision: `964f0a6ec2cec3df4d3678020f7fb87094cce807-dirty`
- started / finished: 2026-10-19 11:54:14.495094+00:00 / 2026-10-19 11:54:33.936498+00:00 (19.4 s)
- settings: `{"provider": "gemini", "model": "gemini-3.1-flash-lite", "temperature": 0.0, "timeout_seconds": 120.0, "max_output_tokens": 16384, "max_model_turns": 3, "max_retries": 4, "min_request_interval_seconds": 2.0, "reasoning_effort": null, "sequential": true, "answer_subset": ["A01", "A07", "A24"]}`
- file hashes (sha256): `{"answers.csv": "fa28e813ea54b4e5ea985585f22f084d826241e1182accbc27ace17066125724", "brand_facts.csv": "2190d40fad2dd167ef2437956c43d595aaf2554ea673a4789b9343cb7e2936f2", "development_gold.csv": "afe84cc78f304afb6a4aaa505dd7504af80fcbf8bc507806aa5ff0aab6bf4850"}`

## Counts

| scheduled | ok | errors | empty | G | P | M | C |
|---|---|---|---|---|---|---|---|
| 3 | 3 | 0 | 0 | 27 | 24 | 24 | 22 |

Predicted label counts: `{"contradicted": 7, "unknown": 8, "supported": 9}`

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction (span match) | 1.0000 | 0.8889 | 0.9412 |
| **joint (span + label)** | 0.9167 | 0.8148 | **0.8627** |

Gold claim coverage C/G: **0.8148**

## Answer errors

None.

## Confusion matrix (matched claims, rows = expected, columns = predicted)

| expected \ predicted | supported | contradicted | unknown |
|---|---|---|---|
| supported | 9 | 1 | 0 |
| contradicted | 0 | 6 | 1 |
| unknown | 0 | 0 | 7 |

## Joint recall by difficulty tag

| tag | correct | gold |
|---|---|---|
| arithmetic | 1 | 2 |
| box_scope | 1 | 1 |
| comparison | 0 | 1 |
| condition_swap | 1 | 1 |
| cross_brand_comparison | 1 | 1 |
| date_scope | 2 | 2 |
| explicit_false | 2 | 2 |
| feature_conflation | 1 | 2 |
| feature_scope | 1 | 1 |
| inference | 0 | 1 |
| missing_fact | 1 | 2 |
| model_scope | 2 | 2 |
| negation | 2 | 2 |
| policy_scope | 5 | 6 |
| policy_vs_capability | 1 | 1 |
| price | 1 | 1 |
| qualification | 1 | 1 |
| region_scope | 1 | 1 |
| requirement_vs_availability | 1 | 1 |
| scope | 2 | 2 |
| unit_conversion | 2 | 2 |
| variant_transfer | 1 | 1 |

## Wrong-label matches (2)

| claim_id | expected | predicted | tags |
|---|---|---|---|
| A01:306:460 | supported | contradicted | comparison, arithmetic |
| A01:461:647 | contradicted | unknown | policy_scope |

## Missed gold claims (3)

| gold claim_id | expected | answer error | quote |
|---|---|---|---|
| A07:512:698 | unknown | False | ClearTrail Plus supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A07:1721:1919 | unknown | False | The plastic used in the enclosure of ClearTrail Plus contains at least sixty percent post-... |
| A24:306:498 | unknown | False | The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance o... |

## Unmatched (extra) predictions (0)


## Per-answer outcomes

| answer | status | claims | turns | latency ms | tools |
|---|---|---|---|---|---|
| A01 | ok | 9 | 2 | 10744 | get_brand_facts(cleartrail) |
| A07 | ok | 6 | 2 | 3567 | get_brand_facts(cleartrail) |
| A24 | ok | 9 | 2 | 5075 | get_brand_facts(cloudnote) |

Full predictions (spans, quotes, labels, fact_ids, reasons) are in `report.json`.
