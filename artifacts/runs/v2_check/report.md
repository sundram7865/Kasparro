# Run report: v2 / check

- run_id: `fcc18201-5b9a-463a-8d29-07ed4bce164b`
- status: **completed**
- provider / model: `gemini` / `gemini-3.1-flash-lite`
- prompt_version: `v2-62a330f677ba`
- dataset / fact / evaluator: `long-brand-answers-50-v4` / `speaker-catalogue-v4` / `sentence-spans-and-labels-v4`
- source_revision: `760220b88e306afaa26e0ef6035f2aea9423b4f4`
- started / finished: 2026-10-19 12:12:59.934950+00:00 / 2026-10-19 12:14:43.167792+00:00 (103.2 s)
- settings: `{"provider": "gemini", "model": "gemini-3.1-flash-lite", "temperature": 0.0, "timeout_seconds": 120.0, "max_output_tokens": 16384, "max_model_turns": 3, "max_retries": 4, "min_request_interval_seconds": 2.0, "reasoning_effort": null, "sequential": true}`
- file hashes (sha256): `{"answers.csv": "fa28e813ea54b4e5ea985585f22f084d826241e1182accbc27ace17066125724", "brand_facts.csv": "2190d40fad2dd167ef2437956c43d595aaf2554ea673a4789b9343cb7e2936f2", "development_gold.csv": "afe84cc78f304afb6a4aaa505dd7504af80fcbf8bc507806aa5ff0aab6bf4850"}`

## Counts

| scheduled | ok | errors | empty | G | P | M | C |
|---|---|---|---|---|---|---|---|
| 10 | 10 | 0 | 0 | null | 87 | null | null |

Predicted label counts: `{"unknown": 27, "contradicted": 29, "supported": 31}`

## Metrics

Quality metrics are **null**: this split has no labels available to the harness (final-check labels are held privately by the reviewers).

## Answer errors

None.

## Per-answer outcomes

| answer | status | claims | turns | latency ms | tools |
|---|---|---|---|---|---|
| A41 | ok | 9 | 2 | 3981 | get_brand_facts(stonewave) |
| A42 | ok | 10 | 2 | 24327 | get_brand_facts(cleartrail) |
| A43 | ok | 9 | 2 | 3979 | get_brand_facts(cleartrail) |
| A44 | ok | 10 | 2 | 5554 | get_brand_facts(cleartrail) |
| A45 | ok | 9 | 2 | 10169 | get_brand_facts(cloudnote) |
| A46 | ok | 11 | 2 | 4035 | get_brand_facts(cloudnote) |
| A47 | ok | 8 | 2 | 24021 | get_brand_facts(stonewave) |
| A48 | ok | 6 | 2 | 18813 | get_brand_facts(stonewave) |
| A49 | ok | 5 | 2 | 4072 | get_brand_facts(stonewave) |
| A50 | ok | 10 | 2 | 4165 | get_brand_facts(cleartrail) |

Full predictions (spans, quotes, labels, fact_ids, reasons) are in `report.json`.
