# Error analysis and the one targeted change (v1 → v2)

All numbers come from the saved live runs in `artifacts/runs/`. Provider, model and settings are identical
for both versions: Gemini `gemini-3.1-flash-lite`, temperature 0, 120 s timeout, 3 turns, sequential.
Data and evaluator are also identical. Recompute with
`python -m claimcheck.cli rescore artifacts/runs/<run>/report.json`.

## 1. v1 baseline: development, 40 answers

| G | P | M | C | extraction P / R / F1 | joint P / R / F1 | answer errors |
|---|---|---|---|---|---|---|
| 376 | 281 | 281 | 269 | 1.000 / 0.747 / 0.855 | 0.957 / 0.715 / **0.819** | 0 |

Joint recall by expected label: supported 115/120, contradicted 110/120, **unknown 44/136**.

**Main failure: under-extraction of claims the catalogue can't verify.** v1 missed 95 gold
sentences, and **91 of them have the gold label `unknown`**. Extraction precision was 1.000, so the model
was never over-extracting. It was skipping product assertions that have no catalogue row. Missed gold by
difficulty tag: missing_fact 18, feature_conflation 18, inference 18, policy_scope 10,
price_vs_shipping 9, future_scope 9, missing_condition 7, condition_scope 5, negative_missing_fact 4.

Typical skipped sentences (all asserted product or policy facts, all gold `unknown`):

* "Using a twenty-watt wall adapter, a fully discharged … reaches a complete charge in ninety minutes…" (7 of 7 missed)
* "An authorized India service centre guarantees repair of … within two working days…" (5 missed)
* "… supports the AAC Bluetooth audio codec…", "The normal manufacturing origin of … is India…",
  "Orders for … receive free delivery to every India postal code…", "… will drop by INR 300 during
  January 2027…", "In winter weather below freezing…", "… maintains uninterrupted playback at … one hundred metres…"

Diagnosis: the model merged two separate decisions. It treated "is this sentence a factual claim?" as if
it were "can the catalogue verify this sentence?". The spec says to extract claims "including false or
unsupported assertions", and that missing information stays `unknown`.

Secondary failure: 12 wrong labels on matched claims. These were mostly arithmetic: minute conversions
(1020 vs 960 minutes) and the direction of a price difference.

## 2. The change

Only one section of the system prompt changed (`claimcheck/prompts/v1.md` → `v2.md`, Step 2). The code,
tool, parser, provider, model and settings are unchanged.

> Whether a sentence is a claim depends only on what it asserts, never on whether the catalogue covers it.
> [… list of assertion kinds: specifications, features, compatibility, price, delivery, returns, repairs,
> warranty, materials, origin, colours, future changes, comparisons …] A product assertion that the
> catalogue cannot confirm or refute is still a claim: select it and label it unknown. Never drop a
> sentence because no catalogue row mentions its topic.

The labelling rules are word-for-word the same in both versions.

## 3. Measured effect: development, same 40 answers

| metric | v1 | v2 | delta |
|---|---|---|---|
| extraction precision | 1.0000 | 0.9973 | -0.0027 |
| extraction recall | 0.7473 | 0.9840 | +0.2367 |
| extraction F1 | 0.8554 | 0.9906 | +0.1352 |
| joint precision | 0.9573 | 0.9730 | +0.0158 |
| joint recall (= C/G coverage) | 0.7154 | 0.9601 | +0.2447 |
| **joint F1** | **0.8189** | **0.9665** | **+0.1477** |
| P / M / C | 281 / 281 / 269 | 371 / 370 / 361 | |
| answer errors | 0 | 0 | |

Joint recall by expected label in v2: supported 117/120, contradicted 113/120, **unknown 131/136** (up from 44).
96 gold claims were fixed (`artifacts/comparison_development.md`).

## 4. Regressions and what is still wrong (v2)

**4 regressions** (correct in v1, wrong in v2):

| gold claim | expected | v2 | note |
|---|---|---|---|
| A17:1444:1607 | contradicted | supported | price-difference direction (Air is *cheaper* than Studio) |
| A35:1442:1606 | contradicted | supported | price-difference direction |
| A20:486:662 | contradicted | unknown | "2025 price was the same INR 1,999" (actually 1,799) |
| A39:494:691 | supported | missed | water-damage exclusion sentence not selected |

The labelling rules did not change. Three of the four regressions are arithmetic or comparison
judgements that this small model gets wrong in both versions (v1 made 10 errors of the same kinds: 4 price-direction, 5 minute-conversion, 1 historical price). They are best
read as run-to-run variance of a flash-lite model, which is not fully deterministic even at temperature 0.
The fourth is a selection miss.

Remaining v2 errors: **9 wrong labels.** 5 are price-difference direction (A16, A17, A25, A34:809, A35),
2 are minute conversions (A22 "780 minutes" vs 12 h = 720; A34 "1020 minutes" vs 16 h = 960), and 2 are
"the 2025 price was already the same" (A20, A32). There are also **6 missed claims** (5 `unknown`:
codec/origin/range sentences, plus 1 `supported`) and **1 extra prediction** (A32 closing advice, "If a
comparison depends on a missing specification, ask…", labelled `unknown`), a side effect of the more
inclusive selection rule.

**Next change I would make (not done; one change per iteration):** move arithmetic out of the model. A
second read-only tool, or a Python post-check, would compute price differences, their direction, and
hour/minute/kilogram conversions from the fact rows. That would target the 9 remaining label errors.
Running a stronger model would likely also help: `gemini-3.8-flash` scored 27/27 on the 3-answer smoke
test (`artifacts/preliminary/`), but its free-tier quota is 20 requests per day.

## 5. Final-check split (A41–A50)

| run | answers | errors | P | label counts | quality |
|---|---|---|---|---|---|
| v1 check | 10 | 0 | 75 | supported 32, contradicted 27, unknown 16 | null (private labels) |
| v2 check | 10 | 0 | 87 | supported 31, contradicted 29, unknown 27 | null (private labels) |

Both versions were frozen in commit `760220b` before either check run. No prompt or code was tuned on
A41–A50. The check inputs are visible in `answers.csv`, so this is not a fully blind benchmark.
