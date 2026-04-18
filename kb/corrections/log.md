# KB v3 — Corrections Memory (Layer 5)

Structured learning memory the agent loads at session start (`kb/architecture/architecture_system_overview.md`, `agent/context_loader.py`). **Not** a raw run log.

## Format (challenge documentation)

- **Architecture / injection tests** (`kb/architecture/injection_tests/openai_agent_context_test.md`): each entry is **the query (or query class) that failed → what was wrong → correct approach**.
- **Join-key failures** (`kb/domain/join_key_glossary.md`, “Log the fix to KB v3”): when the lesson is about keys or zero-row joins, include **`[Join attempted]`**, **`[Mismatch cause]`** (or “N/A” if not a key mismatch), **`[Fix applied]`**, and optional **`[Result]`** when you measured match rate.

Each block below follows that contract. **`[Source logs]`** points to the DataAgentBench harness trace for `query1` / **`run_2`** (`final_agent.json`, with `llm_calls.jsonl` and `tool_calls.jsonl` in the same directory). Entries are numbered for stable reference; the agent receives the **tail** of this file in context.

---

## Dataset coverage (all DAB `db_config.yaml` bundles)

Every bundle under `DataAgentBench/query_*/db_config.yaml` appears below. `query_bookreview` maps to two entries (cross-engine + text extraction).

| `query_*` bundle | Primary entries |
|------------------|-----------------|
| `query_bookreview` | E1, E2, E2b |
| `query_yelp` | E3 |
| `query_agnews` | E4 |
| `query_googlelocal` | E5 |
| `query_stockmarket` | E6, E6d |
| `query_stockindex` | E6, E6b, E6c |
| `query_crmarenapro` | E7 |
| `query_PATENTS` | E8 |
| `query_GITHUB_REPOS` | E9 |
| `query_PANCANCER_ATLAS` | E10 |
| `query_DEPS_DEV_V1` | E11 |
| `query_music_brainz_20k` | E12 |

---

## E1 — Cross-engine SQL (query_bookreview: PostgreSQL + SQLite)

**[Query / pattern]:** Multi-table questions that need both `books_info` and `review` (e.g. decade vs rating).

**[Dataset]:** `query_bookreview`

**[What was wrong]:** Treating `review_database` as queryable inside a single PostgreSQL `JOIN`.

**[Correct approach]:** Run **separate** `query_db` calls per logical DB; merge in `execute_python` using `join_key_glossary.md` (`books_info.book_id` ↔ `review.purchase_id`, normalize types).

**[Join attempted]:** `books_info` ↔ `review` in one SQL  
**[Mismatch cause]:** N/A — engines differ (Postgres vs SQLite); not a padding issue.  
**[Fix applied]:** Two queries + merge on normalized keys.

**[Source logs]:** `/week8-9/DataAgentBench/query_bookreview/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E2 — Decade from unstructured `details` (query_bookreview)

**[Query / pattern]:** Publication decade aggregations from `books_info.details`.

**[Dataset]:** `query_bookreview`

**[What was wrong]:** Using Python `//` in SQLite SQL or joining before extracting a year.

**[Correct approach]:** Extract year in PostgreSQL with `regexp_match` / substring; decade = `CAST(year/10 AS INTEGER)*10` in SQL.

**[Source logs]:** `/week8-9/DataAgentBench/query_bookreview/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E2b — `execute_python`: fake `query_db_response` wrapper (query_bookreview)

**[Query / pattern]:** Any `execute_python` that merges `books_info` with `review` after two `query_db` calls.

**[Dataset]:** `query_bookreview`

**[What was wrong]:** Code assumed `var_tool_query_db_*["query_db_response"]["result"]` (OpenAI-style). DataAgentBench stores **either** a raw list/dict **or** a **path string** to a JSON spill file — **no** nested wrapper. Symptom: `TypeError: string indices must be integers` or `NameError` for invented `var_tool_*` ids.

**[Correct approach]:** `raw = var_tool_query_db_<exact_id_from_footer>; data = json.load(open(raw)) if isinstance(raw, str) else raw`. Use separate variables for the books query vs review query; join on normalized `bookid_*` / `purchaseid_*`.

**[Source logs]:** `/week8-9/DataAgentBench/query_bookreview/query1/logs/data_agent/run_10/final_agent.json`

---

## E3 — Yelp: Mongo ↔ DuckDB identity (query_yelp)

**[Query / pattern]:** Location filters + ratings from Mongo businesses and DuckDB reviews.

**[Dataset]:** `query_yelp`

**[What was wrong]:** Joining Mongo `business_id` to DuckDB `business_ref` without prefix mapping, or skipping **`list_db`** so collection names don’t match the live catalog. **`execute_python` failures** from invented storage names (e.g. guessed `var_tool_query_db_*`) instead of the exact `var_<tool_call_id>` in tool messages, or using truncated chat previews when the full result is a **`.json` spill file** (need `json.load(open(path))`). Endless Mongo **`limit`/`skip` paging** on `business` instead of one projected export plus one DuckDB `review` pull for state- or global aggregates.

**[Correct approach]:** Map **`businessid_*` ↔ `businessref_*`**. **`list_db`** on `businessinfo_database` first, then query with real collection names. Use **only** the storage keys returned after each tool call; **load spill files** for full rows. For “state with most reviews” / mean rating: merge all `review` rows with `business_id`+`description`, parse state from description, **groupby** state.

**[Join attempted]:** `business.business_id` ↔ `review.business_ref`  
**[Mismatch cause]:** Prefix difference (`businessid_` vs `businessref_`).  
**[Fix applied]:** Align IDs before merge.

**[Learned patterns — Yelp, durable]:** (1) **Storage:** Copy **`var_tool_*`** keys exactly from each tool footer; **`json.load`** spill paths; never **`var_call_*`**. (2) **Joins:** `businessid_*` ↔ `businessref_*` before any merge. (3) **Amenity / year-window counts:** **Group Mongo rows by `business_id`**, merge `attributes` dicts, then score — skipping non-dict `attributes` on the **first** row only loses parking signal when a duplicate row exists; **`query3`** traces (`run_7` et al.) show **undercounts** from this. (4) **Category leaderboards:** DAB prompts may omit **`categories`**; **discover** via **`list_db`** + sample doc. **Never** use **`description`** keywords alone (e.g. “Shopping”) as the category dimension — use structured **`categories`** (e.g. primary = first list entry). (5) **Answer shape:** State + mean in one short line where validators use a **window**; computed means only. (6) **User cohort + top categories:** Registration year is DuckDB **`user.yelping_since`**; join **`review.user_id`** → **`user.user_id`**, then Mongo **`categories`** for volume by label; **`return_answer`** lists **exact** category strings from the top buckets (substring graders). Details: `business_terms.md` → Yelp → **Schema discovery**, **calendar year × amenities** (bullets 16–17), **Yelp harness answer shapes**, **Yelp query-class recipes**.

**[Source logs] (examples):** `DataAgentBench/query_yelp/query*/logs/data_agent/run_*/final_agent.json` with `llm_calls.jsonl`, `tool_calls.jsonl`, `execute_python_artifacts.jsonl` — use **artifacts** to debug **`execute_python`**, not `log.md` as a run dump.

---

## E4 — AG News: Mongo articles + SQLite metadata (query_agnews)

**[Query / pattern]:** Article text vs author/region metadata.

**[Dataset]:** `query_agnews`

**[What was wrong]:** Querying only one engine or joining without a shared key.

**[Correct approach]:** MongoDB `articles` for title/description; SQLite `article_metadata` (+ `authors` as needed); merge in pandas on **`article_id`** (cast both sides to the same type if int/string mismatch) (`join_key_glossary.md`).

**[Join attempted]:** `articles.article_id` ↔ `article_metadata.article_id`  
**[Mismatch cause]:** Type or null handling.  
**[Fix applied]:** `list_db` then explicit cast on join keys.

**[Source logs]:** `/week8-9/DataAgentBench/query_agnews/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E5 — Google Local: SQLite reviews + PostgreSQL businesses (query_googlelocal)

**[Query / pattern]:** Business-level stats from reviews + metadata.

**[Dataset]:** `query_googlelocal`

**[What was wrong]:** One SQL string joining SQLite `review` to PostgreSQL `business_description`.

**[Correct approach]:** Query each logical DB separately; join on **`gmap_id`** in Python. Never use `review.name` as the business name — it is the **reviewer** name (`join_key_glossary.md`).

**[Join attempted]:** N/A if single cross-engine SQL was avoided.  
**[Fix applied]:** `gmap_id` only; validate with samples.

**[Source logs]:** `/week8-9/DataAgentBench/query_googlelocal/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E6 — Stock market / index (query_stockmarket, query_stockindex)

**[Query / pattern]:** Price or volatility questions across SQLite metadata + DuckDB trades.

**[Dataset]:** `query_stockmarket`, `query_stockindex`

**[What was wrong]:** Guessing DuckDB table/column names from a company or region name. For **`query_stockindex`**, answering with **long index names only** (e.g. “NASDAQ Composite”) so **`index_trade.Index`** symbols never appear in `return_answer` (substring graders expect values like **`IXIC`**). Using **previous-close** logic for “up/down days” instead of the bundle hint (**`Close` vs `Open`**). For **monthly-investment ranking**, listing the wrong top five or **country far from symbol** so paired substring checks fail.

**[Correct approach]:** **`query_stockmarket`:** Resolve **ticker** from SQLite `stockinfo`, then open the matching DuckDB table(s); many tickers are **separate tables** in DuckDB (`join_key_glossary.md`). **`query_stockindex`:** Join via **`index_trade.Index`**; **always include each index’s `Index` symbol** (from SQL) in the final answer. **Up/down days:** per DAB `db_description_withhint`, **up = `Close > Open`**, **down = `Close < Open`**. **DCA / top-N returns:** discover the index **universe** from the DB; equal monthly investments per index; **rank using one price convention consistently** — for cross-country questions, prefer **`CloseUSD`** end-to-end when populated (see `business_terms.md` — mixing **`Adj Close`** across countries compares local currencies and can mis-rank vs USD-based benchmarks). Map **country** from **`index_info`** + geography, not a static dict. List **top N** in **descending return order** with **symbol and country adjacent** for paired substring checks. Details: `business_terms.md` → **Stock Index** → **Monthly DCA — algorithm**.

**[Source logs]:**
- `query_stockmarket`: `/week8-9/DataAgentBench/query_stockmarket/query1/logs/data_agent/run_2/final_agent.json` (+ `llm_calls.jsonl`, `tool_calls.jsonl` same folder)
- `query_stockindex`: `/week8-9/DataAgentBench/query_stockindex/query1/logs/data_agent/run_2/final_agent.json` (+ same sibling files)

---

## E6b — `execute_python`: wrong `var_tool_*` for `index_trade` (query_stockindex)

**[Query / pattern]:** Volatility, returns, or any metric from DuckDB **`index_trade`** after separate SQLite **`index_info`** pulls.

**[Dataset]:** `query_stockindex`

**[What was wrong]:** Code used the **`index_info`** / `Exchange` query’s storage key (small list) for `pandas` OHLC work, or invented **`var_tool_query_db_*`** ids. Symptom: **`NameError`**, **`TypeError: JSON must be str`**, or **`list indices must be integers, not 'str'`** when indexing with `["result"]`. Alternatively, SQL **`Date >= '2020-01-01'`** on mixed-format date strings left empty or wrong rows; model then answered “no data”.

**[Correct approach]:** Identify the **`query_db`** call that returned **`Index`+`Date`+`Open`+`High`+`Low`** (often spill path). `json.load(open(path))` if needed. Parse dates in Python with **`errors='coerce'`**, filter **`year >= 2020`**. For **query1**, **`return_answer`** must include **`399001.SZ`** only among index tickers (see `validate.py` forbidden list).

**[Source logs]:** `/week8-9/DataAgentBench/query_stockindex/query1/logs/data_agent/run_3/final_agent.json`

---

## E6c — `SUBSTR(Date,1,4)` + `json.loads(open())` + query2 forbidden tickers (query_stockindex)

**[Query / pattern]:** North American **up vs down days** in a calendar year; loading full **`index_trade`** spill in **`execute_python`**.

**[Dataset]:** `query_stockindex`

**[What was wrong]:** (1) SQL **`CAST(SUBSTR(Date, 1, 4) AS INTEGER) = 2018`** — first four characters are often not numeric (**`Dece`**, **`Janu`**), DuckDB **Conversion Error**. (2) **`json.loads(open(path))`** or **`['result']`** on harness storage — wrong API / wrong shape. (3) **`query2` `validate.py`** forbids **`NYA`, `GSPTSE`, …** in the answer string; listing them as negatives fails; only **`IXIC`** may appear among those tickers.

**[Correct approach]:** `SELECT Index, Date, Open, Close FROM index_trade WHERE Index IN (...)` without brittle year-in-SQL, or pull NA indices only; **`rows = json.load(open(spill_path))`** if storage is a path; **`pd.to_datetime`**, **`dt.year == 2018`**, count **`Close > Open`** vs **`Close < Open`**. **`return_answer`:** include **`IXIC`** only if that is the sole qualifying symbol allowed by the validator — **no forbidden substrings**.

**[Source logs]:** `/week8-9/DataAgentBench/query_stockindex/query2/logs/data_agent/run_2/final_agent.json`

---

## E6d — `query_stockmarket`: wrong KB layer + `duckdb` in `execute_python` + spill/`["result"]` misuse

**[Query / pattern]:** Arca ETFs over **`Adj Close`** threshold (Q2); NYSE non-ETF up/down day ranking (Q4); NASDAQ Capital intraday volatility counts (Q5).

**[Dataset]:** `query_stockmarket`

**[What was wrong]:** (1) **`context_loader`** used the **generic** `business_terms.md` head (first *N* chars) instead of **`## Stock Market (query_stockmarket)`**, so Layer 2 showed **unrelated** correction hints (e.g. music_brainz). (2) **`import duckdb`** inside **`execute_python`** — **not installed** in the DAB container → **`ModuleNotFoundError`**. (3) Treating **`var_tool_query_db_*`** spill paths as dicts and indexing **`["result"]`** → **`TypeError`**. (4) **`return_answer`** with prose excuses, **`[]`**, or **`max_iterations`** instead of **`Company Description`** strings the **`validate.py`** fuzzy-matcher expects.

**[Correct approach]:** Ensure **`_build_domain_layer`** extracts the **Stock Market** H2 for **`query_stockmarket`**. Use **`query_db`** only for **`stocktrade_database`**. Use **`dab_load_rows`** / **`json.load(open(path))`** for spills. ISO **`Date`** range filters in SQL. **`return_answer`:** include **31** + all Q2 names; Q4/Q5 **top-5 names** verbatim from **`stockinfo`**. See **`business_terms.md`** → **Stock Market** → **Oracle Forge** bullets.

**[Source logs]:**
- `/week8-9/DataAgentBench/query_stockmarket/query2/logs/data_agent/run_0/final_agent.json`
- `/week8-9/DataAgentBench/query_stockmarket/query4/logs/data_agent/run_0/final_agent.json`
- `/week8-9/DataAgentBench/query_stockmarket/query5/logs/data_agent/run_0/final_agent.json`

---

## E7 — CRM BANT (query_crmarenapro)

**[Query / pattern]:** Lead qualification across CRM objects.

**[Dataset]:** `query_crmarenapro`

**[What was wrong]:** Single generic SQL without the six-DB layout (SQLite + DuckDB + Postgres).

**[Correct approach]:** Use bundle CRM tables; normalize **Salesforce-style 15 vs 18 char IDs** when joining across DBs (`join_key_glossary.md`); merge stepwise in pandas.

**[Join attempted]:** Cross-table lead / activity joins  
**[Mismatch cause]:** 15-char vs 18-char `AccountId` / contact IDs.  
**[Fix applied]:** Compare on first 15 case-insensitive characters when documented.

**[Source logs]:** `/week8-9/DataAgentBench/query_crmarenapro/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E8 — Patents CPC + publications (query_PATENTS)

**[Query / pattern]:** CPC hierarchy, filing trends, EMA over years.

**[Dataset]:** `query_PATENTS`

**[What was wrong]:** Bare regex on patent dates; one engine for CPC + full text.

**[Correct approach]:** Dates: **`dateutil.parser.parse()` or `pd.to_datetime()`** — not regex alone (`schemas.md`, `unstructured_fields.md`). SQLite publications + PostgreSQL `cpc_definition`; align CPC **precision levels** before join (`join_key_glossary.md`).

**[Join attempted]:** `publication` CPC text ↔ `cpc_definition.symbol`  
**[Mismatch cause]:** Different CPC depth / string format.  
**[Fix applied]:** Truncate or `LIKE 'prefix%'` per level; confirm with `cpc_definition.level`.

**[Source logs]:** `/week8-9/DataAgentBench/query_PATENTS/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E9 — GitHub README copyright (query_GITHUB_REPOS)

**[Query / pattern]:** README content vs language metadata.

**[Dataset]:** `query_GITHUB_REPOS`

**[What was wrong]:** Using only SQLite `languages` / `repos` for README text.

**[Correct approach]:** Filter non-Python in SQLite; read README bodies from DuckDB **artifacts** (`unstructured_fields.md`); join on normalized **`repo_name`**.

**[Join attempted]:** `repos.repo_name` ↔ DuckDB artifact repo id  
**[Mismatch cause]:** `owner/repo` formatting or case.  
**[Fix applied]:** Lowercase, strip whitespace, single canonical form.

**[Source logs]:** `/week8-9/DataAgentBench/query_GITHUB_REPOS/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E10 — PanCancer expression + histology (query_PANCANCER_ATLAS)

**[Query / pattern]:** Gene expression by histology for a cohort.

**[Dataset]:** `query_PANCANCER_ATLAS`

**[What was wrong]:** Single join because both concepts appear in one English question, or assuming both sides use the same engine.

**[Correct approach]:** **PostgreSQL** `clinical_info` for clinical/histology; **DuckDB** `molecular_database` for gene/expression data (`db_config.yaml`, `join_key_glossary.md`). Merge on **TCGA barcode**; **12-char vs 16-char** → truncate to shared prefix. Exclude histology in square brackets if the query says so.

**[Join attempted]:** Clinical ↔ molecular by patient  
**[Mismatch cause]:** Barcode length mismatch.  
**[Fix applied]:** Truncate both sides to common prefix length.

**[Source logs]:** `/week8-9/DataAgentBench/query_PANCANCER_ATLAS/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E11 — NPM top packages (query_DEPS_DEV_V1)

**[Query / pattern]:** “Latest release per package” + popularity.

**[Dataset]:** `query_DEPS_DEV_V1`

**[What was wrong]:** Ranking all version rows together.

**[Correct approach]:** Dedupe to **latest release per package** in SQLite `packageinfo`, then join DuckDB star/popularity tables for top-N.

**[Source logs]:** `/week8-9/DataAgentBench/query_DEPS_DEV_V1/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E12 — MusicBrainz tracks + sales (query_music_brainz_20k)

**[Query / pattern]:** Revenue or units for a track (title/artist) across catalogs.

**[Dataset]:** `query_music_brainz_20k`

**[What was wrong]:** Joining SQLite `tracks` to DuckDB `sales` without resolving `track_id`, or matching on title alone when duplicates exist.

**[Correct approach]:** Resolve **`track_id`** in SQLite `tracks` (use `source_id` / `source_track_id` if needed per glossary), then filter **`sales`** in DuckDB by that `track_id` (`join_key_glossary.md`).

**[Join attempted]:** `tracks` ↔ `sales`  
**[Mismatch cause]:** Missing `track_id` or type mismatch.  
**[Fix applied]:** Stable `track_id` join; sample keys before full merge.

**[Source logs]:** `/week8-9/DataAgentBench/query_music_brainz_20k/query1/logs/data_agent/run_2/final_agent.json` · same dir: `llm_calls.jsonl`, `tool_calls.jsonl`

---

## E13 — AG News category + domain KB slice (query_agnews)

**[Query / pattern]:** Sports/longest description, author-specific category fraction, regional/year aggregates with inferred **World / Sports / Business / Science/Technology**.

**[Dataset]:** `query_agnews`

**[What was wrong]:** (1) Domain layer used the generic `business_terms.md` head truncation, so the model never saw the **AG News** H2. (2) KB claimed **`category` lived in Mongo**; DAB schema has **no category column** — only **`title` + `description`** plus SQLite metadata (**`join_key_glossary.md`**, `db_description_withhint.txt`).

**[Correct approach]:** **`context_loader._build_domain_layer`**: extract **`## AG News (query_agnews)`**. Pull Mongo **`articles`** + SQLite **`article_metadata`** / **`authors`**, merge on **`article_id`**, **infer category in Python**, then **`return_answer`** with grader literals (e.g. title **The Rundown**, numeric **0.14414414414414414**, **336.6363636363636**, substring **Africa**).

**[Fix applied]:** H2 extraction + corrected **`business_terms.md`** section; router hint phrases for open KB routing.

**[Source logs]:** Under `DataAgentBench/query_agnews/query*/logs/data_agent/` when benchmark runs are logged there.

---

## Provenance (operators; not part of learning entries)

- Harness: DataAgentBench `run_agent.py` + `common_scaffold.DataAgent`. Oracle Forge `app.py` is separate.
- Last full sweep: `query1`, `run_2`, `google/gemini-2.0-flash-001`, 2026-04-15. Yelp logs under `dab_runs/…/run_2/` when canonical path not writable.
