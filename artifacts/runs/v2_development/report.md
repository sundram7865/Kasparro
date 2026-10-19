# Run report: v2 / development

- run_id: `7eeefac5-6112-4e7b-99fb-a5e1a616e9b8`
- status: **completed**
- provider / model: `gemini` / `gemini-3.1-flash-lite`
- prompt_version: `v2-62a330f677ba`
- dataset / fact / evaluator: `long-brand-answers-50-v4` / `speaker-catalogue-v4` / `sentence-spans-and-labels-v4`
- source_revision: `760220b88e306afaa26e0ef6035f2aea9423b4f4`
- started / finished: 2026-10-19 12:03:40.270738+00:00 / 2026-10-19 12:11:44.210682+00:00 (483.9 s)
- settings: `{"provider": "gemini", "model": "gemini-3.1-flash-lite", "temperature": 0.0, "timeout_seconds": 120.0, "max_output_tokens": 16384, "max_model_turns": 3, "max_retries": 4, "min_request_interval_seconds": 2.0, "reasoning_effort": null, "sequential": true}`
- file hashes (sha256): `{"answers.csv": "fa28e813ea54b4e5ea985585f22f084d826241e1182accbc27ace17066125724", "brand_facts.csv": "2190d40fad2dd167ef2437956c43d595aaf2554ea673a4789b9343cb7e2936f2", "development_gold.csv": "afe84cc78f304afb6a4aaa505dd7504af80fcbf8bc507806aa5ff0aab6bf4850"}`

## Counts

| scheduled | ok | errors | empty | G | P | M | C |
|---|---|---|---|---|---|---|---|
| 40 | 40 | 0 | 0 | 376 | 371 | 370 | 361 |

Predicted label counts: `{"supported": 123, "contradicted": 115, "unknown": 133}`

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction (span match) | 0.9973 | 0.9840 | 0.9906 |
| **joint (span + label)** | 0.9730 | 0.9601 | **0.9665** |

Gold claim coverage C/G: **0.9601**

## Answer errors

None.

## Confusion matrix (matched claims, rows = expected, columns = predicted)

| expected \ predicted | supported | contradicted | unknown |
|---|---|---|---|
| supported | 117 | 2 | 0 |
| contradicted | 6 | 113 | 1 |
| unknown | 0 | 0 | 131 |

## Joint recall by difficulty tag

| tag | correct | gold |
|---|---|---|
| arithmetic | 28 | 33 |
| box_scope | 9 | 9 |
| capability_vs_connector | 12 | 12 |
| capability_vs_rating | 4 | 4 |
| comparison | 15 | 20 |
| condition_scope | 13 | 13 |
| condition_swap | 6 | 6 |
| conditions | 5 | 5 |
| cross_brand_comparison | 2 | 2 |
| date_scope | 21 | 21 |
| explicit_false | 27 | 27 |
| feature_conflation | 22 | 23 |
| feature_scope | 6 | 6 |
| future_scope | 11 | 11 |
| historical_scope | 13 | 15 |
| inference | 18 | 22 |
| missing_condition | 7 | 7 |
| missing_fact | 22 | 25 |
| model_scope | 29 | 29 |
| negation | 43 | 43 |
| negative_missing_fact | 6 | 6 |
| outdated_fact | 6 | 6 |
| policy_scope | 52 | 52 |
| policy_vs_capability | 16 | 17 |
| price | 13 | 13 |
| price_vs_shipping | 11 | 11 |
| qualification | 24 | 24 |
| region_scope | 4 | 4 |
| requirement_vs_availability | 6 | 6 |
| scope | 12 | 12 |
| unit_conversion | 30 | 32 |
| variant_transfer | 8 | 8 |

## Wrong-label matches (9)

| claim_id | expected | predicted | tags |
|---|---|---|---|
| A16:455:618 | contradicted | supported | comparison, arithmetic |
| A17:1444:1607 | contradicted | supported | comparison, arithmetic |
| A20:486:662 | contradicted | unknown | historical_scope |
| A22:504:666 | contradicted | supported | unit_conversion |
| A25:306:459 | supported | contradicted | comparison, arithmetic |
| A32:751:928 | contradicted | supported | historical_scope |
| A34:809:958 | supported | contradicted | comparison, arithmetic |
| A34:1155:1315 | contradicted | supported | unit_conversion |
| A35:1442:1606 | contradicted | supported | comparison, arithmetic |

## Missed gold claims (6)

| gold claim_id | expected | answer error | quote |
|---|---|---|---|
| A14:371:557 | unknown | False | ClearTrail Plus supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A17:1055:1247 | unknown | False | The normal manufacturing origin of CloudNote Air is India, even when the unit is purchased... |
| A21:893:1087 | unknown | False | The normal manufacturing origin of ClearTrail Plus is India, even when the unit is purchas... |
| A37:1659:1853 | unknown | False | The normal manufacturing origin of ClearTrail Mini is India, even when the unit is purchas... |
| A39:494:691 | supported | False | Whatever conclusions a buyer draws from the water-resistance rating, water damage remains ... |
| A39:870:1062 | unknown | False | The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance o... |

## Unmatched (extra) predictions (1)

| claim_id | label | quote |
|---|---|---|
| A32:2518:2656 | unknown | If a comparison depends on a missing specification, ask for that specification before trea... |

## Per-answer outcomes

| answer | status | claims | turns | latency ms | tools |
|---|---|---|---|---|---|
| A01 | ok | 9 | 2 | 3930 | get_brand_facts(cleartrail) |
| A02 | ok | 10 | 2 | 3978 | get_brand_facts(cloudnote) |
| A03 | ok | 9 | 2 | 4441 | get_brand_facts(cloudnote) |
| A04 | ok | 11 | 2 | 4725 | get_brand_facts(stonewave) |
| A05 | ok | 8 | 2 | 4900 | get_brand_facts(stonewave) |
| A06 | ok | 10 | 2 | 4184 | get_brand_facts(cleartrail) |
| A07 | ok | 8 | 2 | 3586 | get_brand_facts(cleartrail) |
| A08 | ok | 10 | 2 | 10673 | get_brand_facts(cleartrail) |
| A09 | ok | 9 | 2 | 53708 | get_brand_facts(cloudnote) |
| A10 | ok | 10 | 2 | 32082 | get_brand_facts(cloudnote) |
| A11 | ok | 10 | 2 | 35530 | get_brand_facts(stonewave) |
| A12 | ok | 9 | 2 | 5386 | get_brand_facts(stonewave) |
| A13 | ok | 10 | 2 | 4139 | get_brand_facts(stonewave) |
| A14 | ok | 8 | 2 | 4111 | get_brand_facts(cleartrail) |
| A15 | ok | 10 | 2 | 5376 | get_brand_facts(cleartrail) |
| A16 | ok | 9 | 2 | 5866 | get_brand_facts(cloudnote) |
| A17 | ok | 10 | 2 | 4291 | get_brand_facts(cloudnote) |
| A18 | ok | 8 | 2 | 54459 | get_brand_facts(stonewave) |
| A19 | ok | 10 | 2 | 9463 | get_brand_facts(stonewave) |
| A20 | ok | 8 | 2 | 3999 | get_brand_facts(stonewave) |
| A21 | ok | 7 | 2 | 3854 | get_brand_facts(cleartrail) |
| A22 | ok | 10 | 2 | 4363 | get_brand_facts(cleartrail) |
| A23 | ok | 8 | 2 | 3646 | get_brand_facts(cloudnote) |
| A24 | ok | 10 | 2 | 9905 | get_brand_facts(cloudnote) |
| A25 | ok | 9 | 2 | 4138 | get_brand_facts(cloudnote) |
| A26 | ok | 10 | 2 | 5011 | get_brand_facts(stonewave) |
| A27 | ok | 9 | 2 | 28854 | get_brand_facts(stonewave) |
| A28 | ok | 10 | 2 | 11698 | get_brand_facts(cleartrail) |
| A29 | ok | 9 | 2 | 4497 | get_brand_facts(cleartrail) |
| A30 | ok | 11 | 2 | 4555 | get_brand_facts(cloudnote) |
| A31 | ok | 10 | 2 | 4143 | get_brand_facts(cloudnote) |
| A32 | ok | 10 | 2 | 4232 | get_brand_facts(cloudnote) |
| A33 | ok | 11 | 2 | 4391 | get_brand_facts(stonewave) |
| A34 | ok | 8 | 2 | 5673 | get_brand_facts(stonewave) |
| A35 | ok | 10 | 2 | 24933 | get_brand_facts(cleartrail) |
| A36 | ok | 8 | 2 | 14795 | get_brand_facts(cleartrail) |
| A37 | ok | 9 | 2 | 47077 | get_brand_facts(cleartrail) |
| A38 | ok | 9 | 2 | 15328 | get_brand_facts(cloudnote) |
| A39 | ok | 8 | 2 | 15021 | get_brand_facts(cloudnote) |
| A40 | ok | 9 | 2 | 6310 | get_brand_facts(stonewave) |

Full predictions (spans, quotes, labels, fact_ids, reasons) are in `report.json`.
