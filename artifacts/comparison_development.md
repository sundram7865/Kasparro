# v1 vs v2 comparison (identical inputs, evaluator, provider, model and settings)

- base: v1 run `bdf2b222-5410-4fc9-af3c-2ad859c31ba3`
- candidate: v2 run `7eeefac5-6112-4e7b-99fb-a5e1a616e9b8`

| metric | base | candidate | delta |
|---|---|---|---|
| extraction precision | 1.0000 | 0.9973 | -0.0027 |
| extraction recall | 0.7473 | 0.9840 | +0.2367 |
| extraction f1 | 0.8554 | 0.9906 | +0.1352 |
| joint precision | 0.9573 | 0.9730 | +0.0158 |
| joint recall | 0.7154 | 0.9601 | +0.2447 |
| joint f1 | 0.8189 | 0.9665 | +0.1477 |
| gold claim coverage C/G | 0.7154 | 0.9601 | +0.2447 |
| G | 376 | 376 | +0 |
| P | 281 | 371 | +90 |
| M | 281 | 370 | +89 |
| C | 269 | 361 | +92 |
| error_answers | 0 | 0 | +0 |
| extra (unmatched) predictions | 0 | 1 | +1 |

## Fixed (wrong/missed in base, correct in candidate): 96

| gold claim | expected | base | candidate |
|---|---|---|---|
| A01:306:460 | supported | wrong:contradicted | correct |
| A01:461:647 | contradicted | wrong:unknown | correct |
| A02:1085:1272 | unknown | missed | correct |
| A02:876:1084 | unknown | missed | correct |
| A03:335:505 | unknown | missed | correct |
| A03:506:687 | unknown | missed | correct |
| A05:1652:1828 | unknown | missed | correct |
| A05:371:531 | contradicted | wrong:supported | correct |
| A05:699:890 | unknown | missed | correct |
| A05:891:1095 | unknown | missed | correct |
| A06:495:697 | unknown | missed | correct |
| A06:699:897 | unknown | missed | correct |
| A06:898:1081 | unknown | missed | correct |
| A07:1721:1919 | unknown | missed | correct |
| A07:512:698 | unknown | missed | correct |
| A08:1084:1282 | unknown | missed | correct |
| A08:1479:1676 | unknown | missed | correct |
| A08:2201:2395 | unknown | missed | correct |
| A08:687:889 | unknown | missed | correct |
| A09:1245:1430 | supported | wrong:contradicted | correct |
| A09:657:844 | unknown | missed | correct |
| A09:845:1048 | unknown | missed | correct |
| A10:1462:1643 | unknown | missed | correct |
| A10:1823:2004 | unknown | missed | correct |
| A10:2005:2200 | unknown | missed | correct |
| A10:371:563 | unknown | missed | correct |
| A12:1379:1559 | unknown | missed | correct |
| A12:335:515 | unknown | missed | correct |
| A12:676:871 | unknown | missed | correct |
| A12:872:1032 | contradicted | wrong:supported | correct |
| A13:1068:1270 | unknown | missed | correct |
| A13:511:680 | unknown | missed | correct |
| A15:1433:1627 | unknown | missed | correct |
| A15:1628:1825 | unknown | missed | correct |
| A15:306:495 | unknown | wrong:supported | correct |
| A15:496:698 | unknown | missed | correct |
| A17:1608:1785 | unknown | missed | correct |
| A17:2338:2519 | unknown | missed | correct |
| A17:507:694 | unknown | missed | correct |
| A18:1693:1874 | unknown | missed | correct |
| A18:491:661 | unknown | missed | correct |
| A18:943:1138 | unknown | missed | correct |
| A19:1068:1268 | unknown | missed | correct |
| A19:1465:1654 | unknown | missed | correct |
| A19:2009:2201 | unknown | missed | correct |
| A19:2202:2372 | unknown | missed | correct |
| A20:664:855 | unknown | missed | correct |
| A22:1706:1892 | unknown | missed | correct |
| A22:1893:2087 | unknown | missed | correct |
| A22:844:1033 | unknown | missed | correct |
| A24:306:498 | unknown | missed | correct |
| A25:1185:1366 | unknown | missed | correct |
| A25:1674:1851 | contradicted | missed | correct |
| A25:460:630 | unknown | missed | correct |
| A25:632:824 | unknown | missed | correct |
| A26:1976:2153 | unknown | missed | correct |
| A26:557:727 | unknown | missed | correct |
| A26:729:925 | unknown | missed | correct |
| A26:926:1107 | unknown | missed | correct |
| A27:1747:1938 | unknown | missed | correct |
| A27:324:493 | unknown | missed | correct |
| A27:494:688 | unknown | missed | correct |
| A27:690:873 | contradicted | missed | correct |
| A28:1123:1302 | unknown | missed | correct |
| A28:549:751 | unknown | missed | correct |
| A28:753:942 | unknown | missed | correct |
| A29:1172:1369 | unknown | missed | correct |
| A29:789:975 | unknown | missed | correct |
| A30:1846:2030 | unknown | missed | correct |
| A30:2031:2229 | unknown | missed | correct |
| A30:2230:2417 | unknown | missed | correct |
| A30:306:509 | unknown | missed | correct |
| A31:1051:1238 | unknown | missed | correct |
| A31:2156:2351 | unknown | missed | correct |
| A31:655:854 | unknown | missed | correct |
| A31:855:1050 | unknown | missed | correct |
| A32:1773:1960 | unknown | missed | correct |
| A32:371:576 | unknown | missed | correct |
| A32:577:749 | supported | missed | correct |
| A33:1575:1780 | unknown | missed | correct |
| A33:2112:2307 | unknown | missed | correct |
| A33:306:498 | unknown | missed | correct |
| A33:499:656 | contradicted | missed | correct |
| A34:1685:1854 | unknown | missed | correct |
| A35:1607:1804 | unknown | missed | correct |
| A35:2130:2321 | unknown | missed | correct |
| A35:689:883 | unknown | missed | correct |
| A35:884:1070 | unknown | missed | correct |
| A36:1256:1463 | unknown | missed | correct |
| A36:324:496 | unknown | missed | correct |
| A36:689:891 | unknown | missed | correct |
| A37:738:917 | unknown | missed | correct |
| A38:1208:1388 | unknown | missed | correct |
| A39:1794:1971 | unknown | missed | correct |
| A39:1972:2172 | unknown | missed | correct |
| A39:2173:2360 | unknown | missed | correct |

## Regressions (correct in base, wrong/missed in candidate): 4

| gold claim | expected | base | candidate |
|---|---|---|---|
| A17:1444:1607 | contradicted | correct | wrong:supported |
| A20:486:662 | contradicted | correct | wrong:unknown |
| A35:1442:1606 | contradicted | correct | wrong:supported |
| A39:494:691 | supported | correct | missed |

## Still wrong but changed: 0

