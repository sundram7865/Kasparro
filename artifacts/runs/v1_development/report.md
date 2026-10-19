# Run report: v1 / development

- run_id: `bdf2b222-5410-4fc9-af3c-2ad859c31ba3`
- status: **completed**
- provider / model: `gemini` / `gemini-3.1-flash-lite`
- prompt_version: `v1-d858d0abad7f`
- dataset / fact / evaluator: `long-brand-answers-50-v4` / `speaker-catalogue-v4` / `sentence-spans-and-labels-v4`
- source_revision: `7b356222eafcb3877853baa733ad4a09af0ef2ac`
- started / finished: 2026-10-19 11:55:00.016295+00:00 / 2026-10-19 12:02:03.119092+00:00 (423.1 s)
- settings: `{"provider": "gemini", "model": "gemini-3.1-flash-lite", "temperature": 0.0, "timeout_seconds": 120.0, "max_output_tokens": 16384, "max_model_turns": 3, "max_retries": 4, "min_request_interval_seconds": 2.0, "reasoning_effort": null, "sequential": true}`
- file hashes (sha256): `{"answers.csv": "fa28e813ea54b4e5ea985585f22f084d826241e1182accbc27ace17066125724", "brand_facts.csv": "2190d40fad2dd167ef2437956c43d595aaf2554ea673a4789b9343cb7e2936f2", "development_gold.csv": "afe84cc78f304afb6a4aaa505dd7504af80fcbf8bc507806aa5ff0aab6bf4850"}`

## Counts

| scheduled | ok | errors | empty | G | P | M | C |
|---|---|---|---|---|---|---|---|
| 40 | 40 | 0 | 0 | 376 | 281 | 281 | 269 |

Predicted label counts: `{"contradicted": 114, "unknown": 45, "supported": 122}`

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction (span match) | 1.0000 | 0.7473 | 0.8554 |
| **joint (span + label)** | 0.9573 | 0.7154 | **0.8189** |

Gold claim coverage C/G: **0.7154**

## Answer errors

None.

## Confusion matrix (matched claims, rows = expected, columns = predicted)

| expected \ predicted | supported | contradicted | unknown |
|---|---|---|---|
| supported | 115 | 4 | 0 |
| contradicted | 6 | 110 | 1 |
| unknown | 1 | 0 | 44 |

## Joint recall by difficulty tag

| tag | correct | gold |
|---|---|---|
| arithmetic | 29 | 33 |
| box_scope | 9 | 9 |
| capability_vs_connector | 12 | 12 |
| capability_vs_rating | 4 | 4 |
| comparison | 16 | 20 |
| condition_scope | 7 | 13 |
| condition_swap | 6 | 6 |
| conditions | 5 | 5 |
| cross_brand_comparison | 1 | 2 |
| date_scope | 21 | 21 |
| explicit_false | 25 | 27 |
| feature_conflation | 5 | 23 |
| feature_scope | 6 | 6 |
| future_scope | 2 | 11 |
| historical_scope | 14 | 15 |
| inference | 4 | 22 |
| missing_condition | 0 | 7 |
| missing_fact | 7 | 25 |
| model_scope | 28 | 29 |
| negation | 42 | 43 |
| negative_missing_fact | 2 | 6 |
| outdated_fact | 6 | 6 |
| policy_scope | 41 | 52 |
| policy_vs_capability | 17 | 17 |
| price | 13 | 13 |
| price_vs_shipping | 2 | 11 |
| qualification | 23 | 24 |
| region_scope | 3 | 4 |
| requirement_vs_availability | 5 | 6 |
| scope | 12 | 12 |
| unit_conversion | 27 | 32 |
| variant_transfer | 8 | 8 |

## Wrong-label matches (12)

| claim_id | expected | predicted | tags |
|---|---|---|---|
| A01:306:460 | supported | contradicted | comparison, arithmetic |
| A01:461:647 | contradicted | unknown | policy_scope |
| A05:371:531 | contradicted | supported | unit_conversion |
| A09:1245:1430 | supported | contradicted | unit_conversion, qualification |
| A12:872:1032 | contradicted | supported | unit_conversion |
| A15:306:495 | unknown | supported | condition_scope |
| A16:455:618 | contradicted | supported | comparison, arithmetic |
| A22:504:666 | contradicted | supported | unit_conversion |
| A25:306:459 | supported | contradicted | comparison, arithmetic |
| A32:751:928 | contradicted | supported | historical_scope |
| A34:809:958 | supported | contradicted | comparison, arithmetic |
| A34:1155:1315 | contradicted | supported | unit_conversion |

## Missed gold claims (95)

| gold claim_id | expected | answer error | quote |
|---|---|---|---|
| A02:876:1084 | unknown | False | The sustained amplifier output of CloudNote Studio is forty watts per channel during ordin... |
| A02:1085:1272 | unknown | False | CloudNote Studio supports the AAC Bluetooth audio codec on compatible phones, so its publi... |
| A03:335:505 | unknown | False | Orders for CloudNote Air receive free delivery to every India postal code, so there is no ... |
| A03:506:687 | unknown | False | An opened CloudNote Air can be returned to any authorized India seller within thirty days ... |
| A05:699:890 | unknown | False | The Bluetooth connection on StoneWave Go maintains uninterrupted playback at a distance of... |
| A05:891:1095 | unknown | False | The sustained amplifier output of StoneWave Go is forty watts per channel during ordinary ... |
| A05:1652:1828 | unknown | False | Using a twenty-watt wall adapter, a fully discharged StoneWave Go reaches a complete charg... |
| A06:495:697 | unknown | False | No version of ClearTrail Plus has ever been offered in blue, including previous-year retai... |
| A06:699:897 | unknown | False | The plastic used in the enclosure of ClearTrail Plus contains at least sixty percent post-... |
| A06:898:1081 | unknown | False | The official India catalogue price of ClearTrail Plus will drop by INR 300 during January ... |
| A07:512:698 | unknown | False | ClearTrail Plus supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A07:1721:1919 | unknown | False | The plastic used in the enclosure of ClearTrail Plus contains at least sixty percent post-... |
| A08:687:889 | unknown | False | An authorized India service centre guarantees repair of ClearTrail Mini within two working... |
| A08:1084:1282 | unknown | False | The plastic used in the enclosure of ClearTrail Mini contains at least sixty percent post-... |
| A08:1479:1676 | unknown | False | ClearTrail Mini accepts two active Bluetooth source connections at the same time and switc... |
| A08:2201:2395 | unknown | False | The normal manufacturing origin of ClearTrail Mini is India, even when the unit is purchas... |
| A09:657:844 | unknown | False | CloudNote Studio supports the AAC Bluetooth audio codec on compatible phones, so its publi... |
| A09:845:1048 | unknown | False | An authorized India service centre guarantees repair of CloudNote Studio within two workin... |
| A10:371:563 | unknown | False | The normal manufacturing origin of CloudNote Air is India, even when the unit is purchased... |
| A10:1462:1643 | unknown | False | The official India catalogue price of CloudNote Air will drop by INR 300 during January 20... |
| A10:1823:2004 | unknown | False | An opened CloudNote Air can be returned to any authorized India seller within thirty days ... |
| A10:2005:2200 | unknown | False | CloudNote Air accepts two active Bluetooth source connections at the same time and switche... |
| A12:335:515 | unknown | False | The official India catalogue price of StoneWave Go will drop by INR 300 during January 202... |
| A12:676:871 | unknown | False | The plastic used in the enclosure of StoneWave Go contains at least sixty percent post-con... |
| A12:1379:1559 | unknown | False | An opened StoneWave Go can be returned to any authorized India seller within thirty days f... |
| A13:511:680 | unknown | False | Orders for StoneWave Go receive free delivery to every India postal code, so there is no s... |
| A13:1068:1270 | unknown | False | A retail purchase of StoneWave Go in Germany qualifies for the same 18-month manufacturer ... |
| A14:371:557 | unknown | False | ClearTrail Plus supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A15:496:698 | unknown | False | An authorized India service centre guarantees repair of ClearTrail Mini within two working... |
| A15:1433:1627 | unknown | False | The normal manufacturing origin of ClearTrail Mini is India, even when the unit is purchas... |
| A15:1628:1825 | unknown | False | ClearTrail Mini accepts two active Bluetooth source connections at the same time and switc... |
| A17:507:694 | unknown | False | In winter weather below freezing, CloudNote Air delivers its full 10-hour laboratory batte... |
| A17:1055:1247 | unknown | False | The normal manufacturing origin of CloudNote Air is India, even when the unit is purchased... |
| A17:1608:1785 | unknown | False | Using a twenty-watt wall adapter, a fully discharged CloudNote Air reaches a complete char... |
| A17:2338:2519 | unknown | False | The official India catalogue price of CloudNote Air will drop by INR 300 during January 20... |
| A18:491:661 | unknown | False | Orders for StoneWave Max receive free delivery to every India postal code, so there is no ... |
| A18:943:1138 | unknown | False | StoneWave Max accepts two active Bluetooth source connections at the same time and switche... |
| A18:1693:1874 | unknown | False | The official India catalogue price of StoneWave Max will drop by INR 300 during January 20... |
| A19:1068:1268 | unknown | False | No version of StoneWave Max has ever been offered in blue, including previous-year retail ... |
| A19:1465:1654 | unknown | False | After an announced firmware update next quarter, StoneWave Max will gain a built-in voice ... |
| A19:2009:2201 | unknown | False | The Bluetooth connection on StoneWave Max maintains uninterrupted playback at a distance o... |
| A19:2202:2372 | unknown | False | Orders for StoneWave Max receive free delivery to every India postal code, so there is no ... |
| A20:664:855 | unknown | False | The normal manufacturing origin of StoneWave Go is India, even when the unit is purchased ... |
| A21:893:1087 | unknown | False | The normal manufacturing origin of ClearTrail Plus is India, even when the unit is purchas... |
| A22:844:1033 | unknown | False | In winter weather below freezing, ClearTrail Mini delivers its full 12-hour laboratory bat... |
| A22:1706:1892 | unknown | False | ClearTrail Mini supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A22:1893:2087 | unknown | False | The Bluetooth connection on ClearTrail Mini maintains uninterrupted playback at a distance... |
| A24:306:498 | unknown | False | The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance o... |
| A25:460:630 | unknown | False | Orders for CloudNote Air receive free delivery to every India postal code, so there is no ... |
| A25:632:824 | unknown | False | The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance o... |
| A25:1185:1366 | unknown | False | An opened CloudNote Air can be returned to any authorized India seller within thirty days ... |
| A25:1674:1851 | contradicted | False | An original invoice is unnecessary when claiming the standard India manufacturer warranty ... |
| A26:557:727 | unknown | False | Orders for StoneWave Max receive free delivery to every India postal code, so there is no ... |
| A26:729:925 | unknown | False | The plastic used in the enclosure of StoneWave Max contains at least sixty percent post-co... |
| A26:926:1107 | unknown | False | The official India catalogue price of StoneWave Max will drop by INR 300 during January 20... |
| A26:1976:2153 | unknown | False | Using a twenty-watt wall adapter, a fully discharged StoneWave Max reaches a complete char... |
| A27:324:493 | unknown | False | Orders for StoneWave Go receive free delivery to every India postal code, so there is no s... |
| A27:494:688 | unknown | False | StoneWave Go accepts two active Bluetooth source connections at the same time and switches... |
| A27:690:873 | contradicted | False | Basic Bluetooth playback on StoneWave Go requires the manufacturer companion app to be ins... |
| A27:1747:1938 | unknown | False | The Bluetooth connection on StoneWave Go maintains uninterrupted playback at a distance of... |
| A28:549:751 | unknown | False | No version of ClearTrail Plus has ever been offered in blue, including previous-year retai... |
| A28:753:942 | unknown | False | In winter weather below freezing, ClearTrail Plus delivers its full 20-hour laboratory bat... |
| A28:1123:1302 | unknown | False | Using a twenty-watt wall adapter, a fully discharged ClearTrail Plus reaches a complete ch... |
| A29:789:975 | unknown | False | ClearTrail Mini supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A29:1172:1369 | unknown | False | ClearTrail Mini accepts two active Bluetooth source connections at the same time and switc... |
| A30:306:509 | unknown | False | No version of CloudNote Studio has ever been offered in blue, including previous-year reta... |
| A30:1846:2030 | unknown | False | The official India catalogue price of CloudNote Studio will drop by INR 300 during January... |
| A30:2031:2229 | unknown | False | CloudNote Studio accepts two active Bluetooth source connections at the same time and swit... |
| A30:2230:2417 | unknown | False | CloudNote Studio supports the AAC Bluetooth audio codec on compatible phones, so its publi... |
| A31:655:854 | unknown | False | The plastic used in the enclosure of CloudNote Studio contains at least sixty percent post... |
| A31:855:1050 | unknown | False | The normal manufacturing origin of CloudNote Studio is India, even when the unit is purcha... |
| A31:1051:1238 | unknown | False | CloudNote Studio supports the AAC Bluetooth audio codec on compatible phones, so its publi... |
| A31:2156:2351 | unknown | False | The Bluetooth connection on CloudNote Studio maintains uninterrupted playback at a distanc... |
| A32:371:576 | unknown | False | The sustained amplifier output of CloudNote Air is forty watts per channel during ordinary... |
| A32:577:749 | supported | False | The built-in microphone is included on CloudNote Air, so microphone availability should be... |
| A32:1773:1960 | unknown | False | In winter weather below freezing, CloudNote Air delivers its full 10-hour laboratory batte... |
| A33:306:498 | unknown | False | The Bluetooth connection on StoneWave Max maintains uninterrupted playback at a distance o... |
| A33:499:656 | contradicted | False | The built-in Wi-Fi capability of StoneWave Max is present, independently of whatever Bluet... |
| A33:1575:1780 | unknown | False | The sustained amplifier output of StoneWave Max is forty watts per channel during ordinary... |
| A33:2112:2307 | unknown | False | StoneWave Max accepts two active Bluetooth source connections at the same time and switche... |
| A34:1685:1854 | unknown | False | Orders for StoneWave Go receive free delivery to every India postal code, so there is no s... |
| A35:689:883 | unknown | False | The Bluetooth connection on ClearTrail Plus maintains uninterrupted playback at a distance... |
| A35:884:1070 | unknown | False | ClearTrail Plus supports the AAC Bluetooth audio codec on compatible phones, so its publis... |
| A35:1607:1804 | unknown | False | ClearTrail Plus accepts two active Bluetooth source connections at the same time and switc... |
| A35:2130:2321 | unknown | False | After an announced firmware update next quarter, ClearTrail Plus will gain a built-in voic... |
| A36:324:496 | unknown | False | Orders for ClearTrail Mini receive free delivery to every India postal code, so there is n... |
| A36:689:891 | unknown | False | An authorized India service centre guarantees repair of ClearTrail Mini within two working... |
| A36:1256:1463 | unknown | False | Compared with the unlisted RivalSound Trek, ClearTrail Mini provides two additional hours ... |
| A37:738:917 | unknown | False | Using a twenty-watt wall adapter, a fully discharged ClearTrail Mini reaches a complete ch... |
| A37:1659:1853 | unknown | False | The normal manufacturing origin of ClearTrail Mini is India, even when the unit is purchas... |
| A38:1208:1388 | unknown | False | Using a twenty-watt wall adapter, a fully discharged CloudNote Studio reaches a complete c... |
| A39:870:1062 | unknown | False | The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance o... |
| A39:1794:1971 | unknown | False | Using a twenty-watt wall adapter, a fully discharged CloudNote Air reaches a complete char... |
| A39:1972:2172 | unknown | False | An authorized India service centre guarantees repair of CloudNote Air within two working d... |
| A39:2173:2360 | unknown | False | In winter weather below freezing, CloudNote Air delivers its full 10-hour laboratory batte... |

## Unmatched (extra) predictions (0)


## Per-answer outcomes

| answer | status | claims | turns | latency ms | tools |
|---|---|---|---|---|---|
| A01 | ok | 9 | 2 | 4455 | get_brand_facts(cleartrail) |
| A02 | ok | 8 | 2 | 4755 | get_brand_facts(cloudnote) |
| A03 | ok | 7 | 2 | 3957 | get_brand_facts(cloudnote) |
| A04 | ok | 11 | 2 | 16369 | get_brand_facts(stonewave) |
| A05 | ok | 5 | 2 | 38138 | get_brand_facts(stonewave) |
| A06 | ok | 7 | 2 | 16670 | get_brand_facts(cleartrail) |
| A07 | ok | 6 | 2 | 4765 | get_brand_facts(cleartrail) |
| A08 | ok | 6 | 2 | 3979 | get_brand_facts(cleartrail) |
| A09 | ok | 7 | 2 | 4197 | get_brand_facts(cloudnote) |
| A10 | ok | 6 | 2 | 3544 | get_brand_facts(cloudnote) |
| A11 | ok | 10 | 2 | 4755 | get_brand_facts(stonewave) |
| A12 | ok | 6 | 2 | 4971 | get_brand_facts(stonewave) |
| A13 | ok | 8 | 2 | 3695 | get_brand_facts(stonewave) |
| A14 | ok | 8 | 2 | 42759 | get_brand_facts(cleartrail) |
| A15 | ok | 7 | 2 | 4469 | get_brand_facts(cleartrail) |
| A16 | ok | 9 | 2 | 4390 | get_brand_facts(cloudnote) |
| A17 | ok | 7 | 2 | 3889 | get_brand_facts(cloudnote) |
| A18 | ok | 5 | 2 | 3836 | get_brand_facts(stonewave) |
| A19 | ok | 6 | 2 | 4457 | get_brand_facts(stonewave) |
| A20 | ok | 7 | 2 | 7891 | get_brand_facts(stonewave) |
| A21 | ok | 7 | 2 | 8697 | get_brand_facts(cleartrail) |
| A22 | ok | 7 | 2 | 7223 | get_brand_facts(cleartrail) |
| A23 | ok | 8 | 2 | 3954 | get_brand_facts(cloudnote) |
| A24 | ok | 9 | 2 | 4097 | get_brand_facts(cloudnote) |
| A25 | ok | 5 | 2 | 3856 | get_brand_facts(cloudnote) |
| A26 | ok | 6 | 2 | 39083 | get_brand_facts(stonewave) |
| A27 | ok | 5 | 2 | 26655 | get_brand_facts(stonewave) |
| A28 | ok | 7 | 2 | 13091 | get_brand_facts(cleartrail) |
| A29 | ok | 7 | 2 | 12632 | get_brand_facts(cleartrail) |
| A30 | ok | 7 | 2 | 8146 | get_brand_facts(cloudnote) |
| A31 | ok | 6 | 2 | 3669 | get_brand_facts(cloudnote) |
| A32 | ok | 6 | 2 | 11369 | get_brand_facts(cloudnote) |
| A33 | ok | 7 | 2 | 5584 | get_brand_facts(stonewave) |
| A34 | ok | 7 | 2 | 39937 | get_brand_facts(stonewave) |
| A35 | ok | 6 | 2 | 3960 | get_brand_facts(cleartrail) |
| A36 | ok | 5 | 2 | 3988 | get_brand_facts(cleartrail) |
| A37 | ok | 8 | 2 | 23382 | get_brand_facts(cleartrail) |
| A38 | ok | 8 | 2 | 4111 | get_brand_facts(cloudnote) |
| A39 | ok | 6 | 2 | 7265 | get_brand_facts(cloudnote) |
| A40 | ok | 9 | 2 | 4413 | get_brand_facts(stonewave) |

Full predictions (spans, quotes, labels, fact_ids, reasons) are in `report.json`.
