# Run report: v1 / development

- run_id: `606e18f2-5cf7-48e6-832a-f1bba39995e7`
- status: **completed**
- provider / model: `gemini` / `gemma-4-26b-a4b-it`
- prompt_version: `v1-d858d0abad7f`
- dataset / fact / evaluator: `long-brand-answers-50-v4` / `speaker-catalogue-v4` / `sentence-spans-and-labels-v4`
- source_revision: `964f0a6ec2cec3df4d3678020f7fb87094cce807-dirty`
- started / finished: 2026-10-19 11:47:31.245597+00:00 / 2026-10-19 11:53:42.025179+00:00 (370.8 s)
- settings: `{"provider": "gemini", "model": "gemma-4-26b-a4b-it", "temperature": 0.0, "timeout_seconds": 120.0, "max_output_tokens": 16384, "max_model_turns": 3, "max_retries": 4, "min_request_interval_seconds": 2.0, "reasoning_effort": null, "sequential": true, "answer_subset": ["A01", "A07", "A24"]}`
- file hashes (sha256): `{"answers.csv": "fa28e813ea54b4e5ea985585f22f084d826241e1182accbc27ace17066125724", "brand_facts.csv": "2190d40fad2dd167ef2437956c43d595aaf2554ea673a4789b9343cb7e2936f2", "development_gold.csv": "afe84cc78f304afb6a4aaa505dd7504af80fcbf8bc507806aa5ff0aab6bf4850"}`

## Counts

| scheduled | ok | errors | empty | G | P | M | C |
|---|---|---|---|---|---|---|---|
| 3 | 0 | 3 | 0 | 27 | 0 | 0 | 0 |

Predicted label counts: `{}`

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction (span match) | 0.0000 | 0.0000 | 0.0000 |
| **joint (span + label)** | 0.0000 | 0.0000 | **0.0000** |

Gold claim coverage C/G: **0.0000**

## Answer errors

| answer | type | message |
|---|---|---|
| A01 | provider_timeout | provider request exceeded 120s |
| A07 | provider_timeout | provider request exceeded 120s |
| A24 | provider_timeout | provider request exceeded 120s |

## Confusion matrix (matched claims, rows = expected, columns = predicted)

| expected \ predicted | supported | contradicted | unknown |
|---|---|---|---|
| supported | 0 | 0 | 0 |
| contradicted | 0 | 0 | 0 |
| unknown | 0 | 0 | 0 |

## Joint recall by difficulty tag

| tag | correct | gold |
|---|---|---|
| arithmetic | 0 | 2 |
| box_scope | 0 | 1 |
| comparison | 0 | 1 |
| condition_swap | 0 | 1 |
| cross_brand_comparison | 0 | 1 |
| date_scope | 0 | 2 |
| explicit_false | 0 | 2 |
| feature_conflation | 0 | 2 |
| feature_scope | 0 | 1 |
| inference | 0 | 1 |
| missing_fact | 0 | 2 |
| model_scope | 0 | 2 |
| negation | 0 | 2 |
| policy_scope | 0 | 6 |
| policy_vs_capability | 0 | 1 |
| price | 0 | 1 |
| qualification | 0 | 1 |
| region_scope | 0 | 1 |
| requirement_vs_availability | 0 | 1 |
| scope | 0 | 2 |
| unit_conversion | 0 | 2 |
| variant_transfer | 0 | 1 |

## Wrong-label matches (0)


## Missed gold claims (27)

| gold claim_id | expected | answer error | quote |
|---|---|---|---|
| A01:306:460 | supported | True | For the current India catalogue, ClearTrail Mini is listed at INR 1,200 less than ClearTra... |
| A01:461:647 | contradicted | True | For an authorized India purchase with the original invoice and a manufacturing defect, Cle... |
| A01:649:832 | unknown | True | An opened ClearTrail Mini can be returned to any authorized India seller within thirty day... |
| A01:833:1040 | unknown | True | The sustained amplifier output of ClearTrail Mini is forty watts per channel during ordina... |
| A01:1237:1439 | unknown | True | An authorized India service centre guarantees repair of ClearTrail Mini within two working... |
| A01:1440:1619 | contradicted | True | The stated laboratory playback time for ClearTrail Mini, using a new battery with EQ off a... |
| A01:1620:1767 | supported | True | For an India purchase at the official catalogue list price on 1 October 2026, ClearTrail M... |
| A01:1769:1942 | contradicted | True | The official India retail box for ClearTrail Mini includes a wall charging adapter, even t... |
| A01:1943:2104 | supported | True | The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a s... |
| A07:306:511 | unknown | True | A retail purchase of ClearTrail Plus in Germany qualifies for the same 12-month manufactur... |
| A07:512:698 | unknown | True | ClearTrail Plus supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A07:700:884 | contradicted | True | The manufacturer supports a stereo pair made from one ClearTrail Plus and one ClearTrail M... |
| A07:987:1153 | supported | True | With all port covers closed, the laboratory immersion allowance for ClearTrail Plus is lim... |
| A07:1350:1533 | supported | True | Considering the speaker alone and leaving retail packaging and accessories out of the meas... |
| A07:1534:1719 | supported | True | Basic Bluetooth listening on ClearTrail Plus does not require the manufacturer companion a... |
| A07:1721:1919 | unknown | True | The plastic used in the enclosure of ClearTrail Plus contains at least sixty percent post-... |
| A07:1920:2143 | contradicted | True | Water damage to ClearTrail Plus is included in the standard India manufacturer warranty af... |
| A24:306:498 | unknown | True | The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance o... |
| A24:499:683 | contradicted | True | For an authorized India purchase with the original invoice and a manufacturing defect, Clo... |
| A24:685:890 | unknown | True | Compared with the unlisted RivalSound Trek, CloudNote Air provides two additional hours of... |
| A24:891:1091 | unknown | True | An authorized India service centre guarantees repair of CloudNote Air within two working d... |
| A24:1092:1287 | unknown | True | CloudNote Air accepts two active Bluetooth source connections at the same time and switche... |
| A24:1484:1675 | supported | True | The manufacturer permits stereo pairing only between two units of the exact CloudNote Air ... |
| A24:1676:1854 | contradicted | True | When measuring just the speaker rather than the retail box and accessories, CloudNote Air ... |
| A24:1856:2025 | supported | True | The move from the 2025 India catalogue to the 2026 catalogue raised the tax-inclusive list... |
| A24:2026:2214 | supported | True | Even when other warranty conditions are met for an authorized India purchase, the original... |
| A24:2215:2381 | supported | True | The official India retail box for CloudNote Air does not contain a wall charging adapter, ... |

## Unmatched (extra) predictions (0)


## Per-answer outcomes

| answer | status | claims | turns | latency ms | tools |
|---|---|---|---|---|---|
| A01 | error | 0 | 1 | 126237 | get_brand_facts(cleartrail) |
| A07 | error | 0 | 1 | 122049 | get_brand_facts(cleartrail) |
| A24 | error | 0 | 1 | 122284 | get_brand_facts(cloudnote) |

Full predictions (spans, quotes, labels, fact_ids, reasons) are in `report.json`.
