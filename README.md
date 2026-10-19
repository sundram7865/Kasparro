# ClaimCheck: extract and classify claims in long AI answers

Kasparro FSE Intern Pathway Assessment (v4). This Python agent reads a long AI-written buying answer about
speakers, finds every factual claim sentence, and labels each one `supported`, `contradicted` or
`unknown` against the supplied catalogue. It looks facts up through **live, model-requested
`get_brand_facts` tool calls**. The repo also contains a deterministic evaluation harness, a preserved
baseline (v1) and a candidate (v2), a thin FastAPI service and PostgreSQL storage.

| | value |
|---|---|
| Provider / model | Google Gemini via its OpenAI-compatible tool-calling API, `gemini-3.1-flash-lite`, temperature 0 |
| Provider request timeout | **120 s** per request (`PROVIDER_TIMEOUT_SECONDS`); timeouts are never retried |
| Turn limit | 3 model turns per answer (turn 1 must call the tool, turn 3 must answer) |
| Dataset / facts / evaluator | `long-brand-answers-50-v4` / `speaker-catalogue-v4` / `sentence-spans-and-labels-v4` |
| Execution | sequential |

## Results (live runs, Gemini `gemini-3.1-flash-lite`)

| run | answers | answer errors | G | P | M | C | extraction F1 | **joint F1** | joint P / R |
|---|---|---|---|---|---|---|---|---|---|
| **v1 development** | 40 | 0 | 376 | 281 | 281 | 269 | 0.8554 | **0.8189** | 0.9573 / 0.7154 |
| **v2 development** | 40 | 0 | 376 | 371 | 370 | 361 | 0.9906 | **0.9665** | 0.9730 / 0.9601 |
| v1 check (A41–A50) | 10 | 0 | null | 75 | null | null | null | null | null |
| v2 check (A41–A50) | 10 | 0 | null | 87 | null | null | null | null | null |

* **The targeted change (v2) raised joint F1 from 0.819 to 0.967** on identical inputs, model, settings and
  scoring. It fixed 96 gold claims and caused 4 regressions. Details: [`artifacts/error_analysis.md`](artifacts/error_analysis.md)
  and [`artifacts/comparison_development.md`](artifacts/comparison_development.md).
* Check-run quality is `null` by design; the reviewers hold the labels. Both versions were frozen in commit
  `760220b` before the check runs.
* Each report contains predictions (span, quote, label, fact_ids, reason), answer outcomes, development
  missed/extra/wrong-label records, a confusion matrix, metrics, settings, versions and file hashes:
  [`v1_development`](artifacts/runs/v1_development/report.md), [`v2_development`](artifacts/runs/v2_development/report.md),
  [`v1_check`](artifacts/runs/v1_check/report.md) and [`v2_check`](artifacts/runs/v2_check/report.md). Each has a
  `report.json` and per-answer sanitized model/tool exchanges in `exchanges/`; for example,
  [`v2_development/exchanges/A07.json`](artifacts/runs/v2_development/exchanges/A07.json) shows the system prompt,
  the numbered sentences, the model's `get_brand_facts` tool call, the tool result and the final JSON.
* Live API evidence (a real `/classify` call, a joined `GET /evaluation-runs/{id}` from PostgreSQL, and
  404/422 cases): [`artifacts/api_live/`](artifacts/api_live/).
* Tests: **89 passed** ([`artifacts/test_output.txt`](artifacts/test_output.txt)).
* PostgreSQL persistence evidence: every stored run (the four official runs plus the aborted first attempt), exported through the same joined query as `GET /evaluation-runs/{id}`: [`artifacts/db_export/`](artifacts/db_export/). Stored claim counts match the reports (281 / 371 / 75 / 87).


---

## 1. How it works

```
answers.csv row ──► AgentInput(answer_id, brand_id, question, ai_answer)   (gold/claims/labels rejected)
                     │
                     ├─ Python: split ai_answer into sentences S1..Sn with exact code-point offsets
                     │
   turn 1 (tool_choice=required) ─► model calls get_brand_facts(brand_id) ─► executor validates
                     │                 name + {brand_id} args, unknown brand = answer error, returns
                     │                 the brand's rows {fact_version: speaker-catalogue-v4, facts:[...]}
   turn 2 (auto)  ─► model may request another brand, or returns JSON
                     │   {"claims":[{"sentence_id","label","fact_ids","reason"}]}
   turn 3 (none)  ─► must answer; a tool request here = turn_limit_exceeded
                     │
                     ├─ Python: sentence_id ─► [start_char, end_char), quote = ai_answer[start:end],
                     │          claim_id = answer_id:start:end, fact_ids must exist, labels checked,
                     │          no duplicates/overlaps, sorted, reason trimmed to ≤ 2 sentences
                     ▼
              AgentResult(status ok | error(type, sanitized message), claims, turns, tool calls, latency)
```

Key design decisions:

* **The model never counts characters.** Python segments the untouched `ai_answer` into sentences
  (a `.`, `!` or `?` followed by whitespace or end of text, so `1.5` and `0.35` don't split). The
  model returns sentence IDs, and Python derives every offset and quote from the source text. Before
  writing any agent code I checked that all 376 development gold spans are exactly segmenter
  sentences (`tests/test_segment.py`). Spans therefore can't drift, and repeated sentences are
  resolved by position. The model is never given a claim list: it sees every sentence, including
  advice and the injected instruction, and decides which ones are factual claims.
* **Real tool use.** `get_brand_facts` is offered as an OpenAI-format function. Turn 1 uses
  `tool_choice="required"`, and a final answer that never fetched facts is an answer error
  (`no_tool_call`). Several tool requests in one turn are allowed. Only this one read-only lookup
  exists: any other tool name gives `illegal_tool`, an unknown brand gives `unknown_brand`, and bad
  arguments give `tool_argument_error`. Nothing from the answer text is ever executed.
* **Untrusted answer text.** Sentences are wrapped in `<answer_sentences>` and the prompt says they
  are data. Injected sentences ("Ignore the classification instructions…") are neither extracted nor
  obeyed (see A07/A18/A32 in the reports).
* **Answer-level errors are preserved.** Invalid JSON, schema violations, unknown sentence IDs,
  duplicates, invented fact IDs, illegal tools, unknown brands, provider errors, timeouts and turn
  exhaustion all produce `status=error` with a sanitized type and message and **no accepted
  predictions**. They are never converted into `unknown` labels. A valid empty claim list is
  accepted.
* **Gold isolation.** The inference path (`agent.py`, `facts_tool.py`, providers) never imports
  gold. `runner.py` loads `development_gold.csv` only after every answer outcome has been persisted.
  A test confirms that no gold marker or explanation appears in any model or tool payload.
* **Provider retries.** HTTP 429/5xx and connection errors are retried up to 4 times with backoff
  (respecting `retry-after`). These are transport retries, not model turns. Timeouts are not retried.

## 2. Repository layout

| path | purpose |
|---|---|
| `claimcheck/data.py` | CSV loading (`csv` module, UTF-8, `newline=""`), typed fact values (`"false"` → `False`), inclusive dates |
| `claimcheck/segment.py` | deterministic sentence spans |
| `claimcheck/facts_tool.py` | `get_brand_facts` schema and validating executor |
| `claimcheck/agent.py` | the 3-turn agent, output parsing and validation |
| `claimcheck/prompts/v1.md`, `v2.md` | baseline and candidate system prompts (versioned by SHA-256 prefix) |
| `claimcheck/providers/` | OpenAI-compatible live provider (Gemini/OpenAI/Groq) and deterministic fakes for tests |
| `claimcheck/validation.py` | span bounds, quote equality, IDs, overlaps, labels, fact IDs |
| `claimcheck/scoring.py` | exact-span harness scoring |
| `claimcheck/runner.py` | sequential runs: metadata, persistence, scoring after predictions are saved |
| `claimcheck/db.py`, `schema.sql` | PostgreSQL tables `runs`, `answer_results`, `claim_results` |
| `claimcheck/api.py` | FastAPI app |
| `claimcheck/reports.py`, `cli.py` | JSON/Markdown reports, comparison, CLI |
| `data/` | the issued CSVs, byte-for-byte, plus `SHA256SUMS` |
| `artifacts/runs/{v1,v2}_{development,check}/` | the four live-run reports, each with `report.json`, `report.md` and per-answer `exchanges/` |
| `artifacts/` | v1/v2 comparison, error analysis, test output, live API evidence |

## 3. Setup

Prerequisites: Python 3.12, Docker (for PostgreSQL), and a Gemini API key (free tier works).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then set GEMINI_API_KEY=...  (never commit .env)
docker compose up -d          # PostgreSQL 16 on 127.0.0.1:5433 (user/password/db: claimcheck)
python -m claimcheck.cli init-db
python -m claimcheck.cli verify-data   # counts, gold offset check, SHA-256 of the issued CSVs
```

`DATABASE_URL` (in `.env`) defaults to `postgresql://claimcheck:claimcheck@127.0.0.1:5433/claimcheck`.
The tests use `TEST_DATABASE_URL` (`…/claimcheck_test`); the test fixture creates and resets that
database. Other providers: set `LLM_PROVIDER=openai` or `groq`, plus the matching key and `LLM_MODEL`.

## 4. Commands

```bash
# tests (DB tests need the compose database; see artifacts/test_output.txt for an actual run)
python -m pytest -v

# the four live runs (each writes artifacts/runs/<version>_<split>/ and stores the run in PostgreSQL)
python -m claimcheck.cli run --agent-version v1 --split development
python -m claimcheck.cli run --agent-version v2 --split development
python -m claimcheck.cli run --agent-version v1 --split check
python -m claimcheck.cli run --agent-version v2 --split check

# compare v1 and v2 on identical inputs and scoring rules; recompute metrics from saved predictions
python -m claimcheck.cli compare artifacts/runs/v1_development/report.json artifacts/runs/v2_development/report.json --out artifacts/comparison_development.md
python -m claimcheck.cli rescore artifacts/runs/v2_development/report.json

# API
uvicorn claimcheck.api:get_app --factory --port 8000
curl -X POST localhost:8000/classify -H "content-type: application/json" \
     -d '{"answer_id":"A01","brand_id":"cleartrail","question":"...","ai_answer":"...","agent_version":"v2"}'
curl -X POST localhost:8000/evaluation-runs -H "content-type: application/json" -d '{"agent_version":"v2","split":"check"}'
curl localhost:8000/evaluation-runs/<run_id>
```

### API contract

| endpoint | behaviour |
|---|---|
| `POST /classify` | Body: `answer_id, brand_id, question, ai_answer, agent_version (v1/v2)`. Returns **200** with validated claims. **422** for invalid requests or any extra field (`claims`, `gold`, `expected_label`, …). **404** for an unknown primary brand. **502** for provider errors or invalid output (including illegal tools, unknown requested brands and turn exhaustion). **504** for timeouts. Error bodies are `{"error": {"type", "message"}}`, sanitized and never echoing the input. |
| `POST /evaluation-runs` | Body: `agent_version, split (development/check)`. Processes the fixed CSV split and returns **201** with `run_id`, status, counts and metrics (`null` for check). Per-answer errors are preserved. An infrastructure failure returns 500 with the `run_id`, and the run is stored as `failed` with its partial evidence. |
| `GET /evaluation-runs/{id}` | Joins run metadata, answer outcomes and predicted claims from PostgreSQL. Answers are ordered by schedule position and claims by span. **404** for a missing run, **422** for an invalid UUID. |

### Storage

`runs` holds the split, agent/prompt/dataset/evaluator/fact versions, provider, model, settings (JSONB),
source revision (git SHA, with `-dirty` if the tree had uncommitted changes), file hashes, status, counts,
metrics and the missed/extra/wrong-label ID lists. `answer_results` has one terminal row per scheduled
answer, including errors and valid empty outputs, with its status, sanitized error, latency, model
turns, tool calls, usage and trace reference. `claim_results` has one row per accepted prediction, with
its span, quote, label, fact IDs and reason, plus the development match fields (`NULL` for checks).
Constraints: `UNIQUE(run_id, answer_id)`, `UNIQUE(run_id, answer_id, start_char, end_char)`, foreign
keys, and CHECK constraints on labels, splits, statuses and spans. All SQL is parameterized (psycopg 3).

## 5. Harness

* Predictions match gold only when `answer_id`, `start_char` and `end_char` are all identical, after
  the prediction's quote has been checked against the source text. A partial or merged sentence
  doesn't match, and each gold span matches at most one prediction. There is no fuzzy matching and no
  LLM judge.
* Over the whole split: G = gold claims, P = accepted predictions, M = exact span matches, C = matches
  with the correct label. Extraction P/R/F1 = M/P, M/G, 2M/(P+G). Joint P/R/F1 = C/P, C/G, 2C/(P+G).
  A zero denominator counts as 0 when the split has gold; an empty split gives null metrics.
* **Joint F1 is the headline metric.** Reports also give C/G coverage, missed gold IDs (flagged when
  caused by an answer error), unmatched (extra) prediction IDs, wrong-label matches, answer error
  counts by type, a confusion matrix, and joint recall by expected label and difficulty tag.
  Matched-only label accuracy is never reported as overall quality.
* The scorer requires exactly one outcome per scheduled answer: missing, duplicated or unexpected
  outcomes raise an error. An errored answer adds no predictions, and its gold stays in G as missed.
* **Check runs** (A41–A50) save predictions, errors, counts, timing and versions. G, M, C and all
  quality metrics stay `null`; the reviewers score them with their private labels.



## 6. Improvement: diagnosis, change, effect

**Diagnosis (v1 development).** v1 had perfect extraction precision (1.000) but recall of only 0.747:
it missed 95 gold sentences, and **91 of them have the gold label `unknown`**. Joint recall for `unknown`
claims was 44/136, against 115/120 for supported and 110/120 for contradicted. The model skipped product
assertions that have no catalogue row: free delivery, 30-day returns, 2-day repairs, AAC codec,
multipoint, 100 m range, recycled plastic, manufacturing origin, 2027 prices, firmware plans,
cold-weather runtime and charging time. It treated "the catalogue can't verify this" as "this is not a
claim". The spec says to extract claims "including false or unsupported assertions".

**One targeted change (v2).** Only Step 2 of the system prompt changed: decide whether a sentence is a
claim from its wording, before checking the facts. A product assertion the catalogue can't confirm or
refute is still a claim and is labelled `unknown`. The labelling rules, code, tool, provider, model and
settings are identical (`diff claimcheck/prompts/v1.md claimcheck/prompts/v2.md`).

**Effect.** Extraction recall rose from 0.747 to 0.984 and joint F1 from **0.819 to 0.967**. Unknown
recall went from 44/136 to 131/136. 96 gold claims were fixed.

**Regressions, reported honestly.** 4 gold claims were correct in v1 and wrong in v2: two price-difference
directions (A17, A35), one historical-price claim (A20) and one missed supported sentence (A39). There is
also 1 new extra prediction: an advice sentence in A32 selected as `unknown`. The remaining v2 errors are 9
wrong labels (5 price-difference direction, 2 minute conversions, 2 historical "same price" claims) and 6
missed sentences. The next change I'd make, not done here because it's one change per iteration, is to
compute price differences and unit conversions in Python, for example with a read-only arithmetic tool.

## 7. Model choice and preliminary runs (disclosed)

* The first model was `gemini-3.8-flash`. It scored 27/27 on a 3-answer smoke test, but the **free tier
  allows only 20 requests per day for that model**. The first official v1 attempt hit HTTP 429 from
  A07 onward, so I stopped it; it is stored in PostgreSQL as run `1e5adbce...` with status `failed` (exported to [`artifacts/db_export/`](artifacts/db_export/)).
  Spacing out requests doesn't help, because the limit is per day.
* `gemma-4-31b-it` and `gemma-4-26b-a4b-it` support tool calling but were too slow on the free tier
  (130–260 s per answer, and 120 s timeouts). The Gemma smoke test also showed inline `<thought>...</thought>`
  blocks and fenced JSON. I changed the final-output parser to drop reasoning blocks and read the last
  fenced JSON block; nothing else is repaired, and the result must still pass full validation. This
  change was made **before** the official v1 run, so it applies equally to v1 and v2.
* All four official runs use `gemini-3.1-flash-lite`, the fastest free model that worked (3–25 s per
  answer). The smoke reports are in [`artifacts/preliminary/`](artifacts/preliminary/).

## 8. Tests

`python -m pytest -v` was **actually run**: **89 passed** in about 4 s. The full output is in
[`artifacts/test_output.txt`](artifacts/test_output.txt). The API and database tests ran against the
real PostgreSQL 16 container, not mocks.

| file | what it checks |
|---|---|
| `test_data.py` | quoted commas and embedded newlines/CRLF round-trip exactly; issued counts (50/132/376); every gold quote equals `ai_answer[start:end]`; `"false"` → `False`; numbers/strings; blank unit/condition → `None`; inclusive dates; header validation; SHA-256 of the issued files |
| `test_segment.py` | every gold span is a segment; full coverage without whitespace edges; decimals; trailing text |
| `test_validation.py` | valid and invalid offsets, quote equality, whitespace, duplicate IDs, overlapping spans, ordering, claim_id derivation, unknown fact IDs, labels, reason length |
| `test_scoring.py` | perfect output; missed claims; extra advice extracted; wrong labels; provider-error answer; valid empty predictions; **G=10 P=10 M=8 C=7 → 0.80 / 0.70**; partial spans; quote mismatch; one match per gold; missing/duplicated/unexpected outcomes rejected; null check metrics; empty split; real gold scored against itself = 1.0 |
| `test_agent_fake.py` | fake provider: happy path and exact spans; multi-tool turns; forced final turn; malformed JSON; unsupported labels; invented fact IDs; unknown/duplicate sentence IDs; illegal tool (never executed); unknown requested brand; bad tool args; timeout; provider error; turn exhaustion; no tool use; sanitized secrets; **gold never in model/tool payloads** (all 40 answers, v1 and v2); injection kept in the untrusted block |
| `test_api_db.py` | `/classify` 200/422 (gold and claim fields, bad version)/404/502/504; development run persisted and retrieved with joined, ordered answers including error and empty answers; check run with null quality; 404/422 run lookups; infrastructure failure marks the run `failed` and keeps partial rows; DB unique/FK/CHECK constraints |

The fake providers only exercise control flow; all quality numbers come from the four live runs.

## 9. Reproducibility

* Issued CSVs are committed unchanged (`data/`, CRLF record endings preserved by `.gitattributes`), and
  their SHA-256 hashes are in `data/SHA256SUMS` and in every run's metadata:
  * `answers.csv` `fa28e813ea54b4e5ea985585f22f084d826241e1182accbc27ace17066125724`
  * `brand_facts.csv` `2190d40fad2dd167ef2437956c43d595aaf2554ea673a4789b9343cb7e2936f2`
  * `development_gold.csv` `afe84cc78f304afb6a4aaa505dd7504af80fcbf8bc507806aa5ff0aab6bf4850`
* All four runs use the same provider, model, temperature, timeout, token limit, retry policy and
  evaluator; only the agent version (system prompt) differs. Every report records the prompt version
  hash and git revision.
* Pinned dependencies are in `requirements.txt` (Python 3.12.6). No keys or `.env` values are
  committed; `.env.example` is the secret-free template.



## 10. Limitations and unfinished work

* **Model strength.** Free-tier quotas forced a flash-lite model, and most remaining errors are
  arithmetic (price-difference direction, minute conversions). The planned arithmetic helper (section 6)
  is not implemented.
* **Determinism.** Gemini isn't fully deterministic at temperature 0. A rerun can change a few labels;
  three of the four v2 regressions are this kind of borderline arithmetic judgement. I made only one run
  per version and didn't average repeated runs.
* **Check split.** The A41–A50 inputs are visible in `answers.csv`, so this isn't a fully blind
  benchmark. No prompt or code was tuned on them, and their quality is unknown to me.
* **Sentence segmentation** relies on `.`, `!` or `?` followed by whitespace. It matches all 376 gold spans
  here, but abbreviations like "e.g. " would split a sentence in other data.
* **Deferred by design:** no concurrency, no Langfuse, no React, no authentication, no idempotency or
  durable recovery. `POST /evaluation-runs` runs synchronously, so a development run holds the request
  for a few minutes.
* The live API evidence covers `/classify` and `GET /evaluation-runs/{id}`. The four official runs were
  executed through the CLI, which calls the same `execute_run` service function as
  `POST /evaluation-runs`. That endpoint itself is exercised in the tests against real PostgreSQL with a
  fake provider.

## 11. Time spent

About 2 hours of build time (15:45–17:50 IST on 19 October 2026). That covers the agent, harness, API,
DB and tests, then about 25 minutes of live runs, analysis and documentation. The 5 PM submission came
while the live runs were blocked by the free-tier quota; the runs, analysis and test output were
committed afterwards (see the git history timestamps).

## 12. AI assistance disclosure

I built this with **Claude Code** (Anthropic's coding agent), which the assessment allows. I directed the
work and made the decisions: the provider (Gemini with my own key), switching models when the free
quota ran out, and keeping exactly one change between v1 and v2. Claude Code wrote most of the code,
tests, prompts and documentation. It is **not** listed as a commit author or co-author.

These checks were actually executed, and their outputs are committed:

* all 376 gold quotes equal `ai_answer[start:end]`, and every gold span is a segmenter sentence (`verify-data`, tests);
* the issued CSVs are byte-identical to the files I received (SHA-256 in `data/SHA256SUMS`);
* 89 tests passed, including API and DB tests against the real PostgreSQL container (`artifacts/test_output.txt`);
* four live runs with real tool calls, inspected through the saved exchanges (no API key appears in any artifact);
* `rescore` recomputes the saved v2 development metrics exactly from the saved predictions;
* live `/classify` and `GET /evaluation-runs/{id}` calls (`artifacts/api_live/`);
* the v1→v2 change was diagnosed from the v1 development report only, and both versions were frozen before the check runs.

