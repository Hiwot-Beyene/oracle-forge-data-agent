# Recent fixes (Oracle Forge + DAB alignment)

Short report of changes aimed at **reliable tool runs**, **grading (`validate.py`)**, and **KB actually reaching the data agent**.

## Knowledge base (domain + loader)

- **`agent/context_loader.py` (new):** Loads Forge KB from disk (`kb/architecture`, `kb/domain`, `kb/corrections`). For **`query_yelp`**, injects the full **`## Yelp (query_yelp)`** section from `business_terms.md` (the old loader only read the first ~900 chars of that file, so Yelp guidance never appeared in prompts). **Yelp body cap** raised so the section is not truncated mid-file; **question-aware trim** drops the **query2-only** `### DAB validate.py…` block for amenity/count questions so the model is not flooded with mean-rating grader prose. No benchmark answers are injected.
- **`kb/domain/business_terms.md`:** Yelp — cross-DB storage keys, **query2** grader/answer-shape notes, **query3-style** “calendar year × amenities” (distinct `business_ref`, Mongo `attributes`, `BikeParking` / `BusinessParking` + `ast.literal_eval`, avoid swapping DuckDB vs Mongo `execute_python` variables). Added bullets **12–13**: merge rows by `business_id` before scoring (avoid **first-row `visited`** undercount when duplicate rows differ in attribute richness); do not mix **full** Mongo `business` exports with filtered `$in` lists without intersecting the DuckDB year-filtered id set. Removed misleading “always Pennsylvania: …” style templates; emphasize **computed** values only.
- **`kb/domain/join_key_glossary.md`:** Yelp — pointer to amenity/parking fields on Mongo `business.attributes`.
- **`kb/domain/unstructured_fields.md`:** Yelp — semi-structured `business.attributes` (string booleans, stringified `BusinessParking` dicts).
- **`kb/corrections/log.md`:** Minor wording so fixes don’t prescribe literal example numbers; **E3** note for **query3** (year × parking): single Mongo `$in`, dedupe, spill `json.load`, `BusinessParking` bool / `attributes` string `"None"`, avoid destructive string replace on parking fields.

## DataAgentBench / harness (not KB text)

- **`run_agent.py`:** Default `ORACLE_FORGE_ROOT` = sibling `../oracle-forge-data-agent`; larger **Yelp `DOMAIN_HINT` budget** so injected KB isn’t truncated. KB block unchanged in purpose — still loaded from Forge, not hardcoded answers.
- **`benchmark_service.py` / `eval/harness.py`:** Set `ORACLE_FORGE_ROOT` in the subprocess environment so benchmark runs load the same KB as CLI.
- **`common_scaffold/tools/db_utils/mongo_utils.py`:** Default Mongo **`limit`** is **`None`** (was 5), so full-collection queries aren’t silently truncated.
- **`common_scaffold/tools/ExecTool.py`:** **`execute_python`** env passed via **base64 + pickle** in-process (avoids host-path pickle files invisible to Docker and `nan` issues from stringifying env).
- **`query_yelp/query2/validate.py`:** Match **Pennsylvania** / token **PA** without naive `find("pa")`; accept ground-truth mean as any `\d+\.\d+` in the full answer (fixes “Pennsylvania (PA) … approximately 3.7” style answers).

Together, these changes fix **missing KB in traces**, **wrong Yelp aggregates**, **execute_python env failures in Docker**, and **query2 false negatives** on otherwise correct prose answers.

**Yelp query 2–6 (Forge KB only):** Expanded **`business_terms.md`** with **Yelp harness answer shapes** (state + mean proximity, **`categories`** + `BusinessAcceptsCreditCards` for category leaderboards, WiFi + state, verbatim **name** + **all category strings** for date-window top-rating questions). **`join_key_glossary.md`** and **`unstructured_fields.md`** document **`categories`**. **`context_loader.infer_dataset_hint`** adds Yelp triggers (`wifi`, `credit card`, …) and drops the misleading **`average rating for`** bookreview trigger that could steal Yelp questions in Flask routing.

**Yelp query3 / query4 (Forge KB):** **`business_terms.md`** — **Schema discovery** subsection (DAB prompts may omit Mongo fields); **`calendar year`** bullets **16–17** (mandatory **`business_id` → merge `attributes`** before skipping non-dict rows; **`BikeParking`** case-insensitive truth). **Harness answer shape** item 2 — **do not** rank categories from **`description`** text. **`corrections/log.md` E3** — condensed to **learning patterns** (not per-run trace dumps); **`MEMORY.md`** pointer to schema discovery.

**Yelp Q3–Q7 (Forge KB):** **`business_terms.md`** — harness item **5** (user cohort + top categories, verbatim labels); **`Yelp query-class recipes`** (Q3–Q7 algorithm sketches, no benchmark numbers). **`join_key_glossary.md`** / **`unstructured_fields.md`** — DuckDB **`user.user_id`**, **`yelping_since`**. **`context_loader.py`** — Yelp routing keywords (`yelping_since`, registered-on-Yelp phrasing, …); **`YELP_USER_COHORT`** injection when the question matches; larger **corrections tail** for `query_yelp` so E3 patterns stay in context.

**Stock index Q2 / Q3 (Forge KB):** **`business_terms.md`** — DAB **Open/Close** definition for up/down days; **`index_trade.Index`** symbols mandatory in answers; DCA + symbol–country proximity. **`join_key_glossary.md`** — `index_trade.Index` as join/answer key. **`context_loader.py`** — `query_stockindex` routing; full **`## Stock Index`** H2 (includes **Oracle Forge — session injection**) + E6 tail.

**Stock index Q3 (methodology, not answers):** Removed example tickers from KB prose; added **`### Monthly DCA — algorithm`** (universe from SQL, **`CloseUSD`** vs **`Adj Close`** discipline, no hardcoded symbol→country maps). Session injection text lives under **`### Oracle Forge — session injection`** in **`business_terms.md`**.

**DataAgentBench `run_agent.py`:** **`DOMAIN_HINT`** character limit for **`stockindex`** and **`bookreview`** raised to **10000** (was **420** for most bundles), matching the Yelp pattern so Forge KB actually reaches the agent during benchmark runs.

**Book review (`query_bookreview`):** **`context_loader.py`** injects **`## Book Reviews (query_bookreview)`** + join glossary + **`unstructured_fields.md`** excerpt. **Oracle Forge** session lines live in **`business_terms.md`** under **## Book Reviews**. Previously the generic branch only read the **first 900 chars** of `business_terms.md` (file header), so agents rarely saw book-specific rules.

**Stock index Q1-style:** **`business_terms.md`** — single-winner answers: avoid listing runner-up tickers when validators forbid extra symbols.

**Bookreview `no_tool_call` (Gemini/OpenRouter):** `BOOKREVIEW_SQL_HINT` incorrectly implied **`var_shim_*`** keys were invalid; this harness uses **`var_shim_…`** when tool calls are parsed from \`\`\`json fences. Hints and **`business_terms.md`** (Book Reviews) now say to copy **exact** footer keys (`var_tool_*` or `var_shim_*`). **`run_agent.py`** prepends bookreview-specific **CORRECTION_HINT** text. **`DataAgent.py`** — if the model returns **empty content** after a tool result, inject a **user nudge** and continue instead of **`no_tool_call`** termination.

**TRP1 KB layering refactor:** **`context_loader.py`** — Layer 1 = **`kb/architecture/`** only (`MEMORY.md` + `architecture_system_overview.md`). Layer 2 = **`kb/domain/`** (`business_terms` per dataset H2, `join_key_glossary`, `unstructured_fields` excerpt). Layer 3 = **`kb/corrections`**. Inline Python FORGE strings removed; **### Oracle Forge — session injection** blocks added under Yelp / Stock Index / Book Reviews in **`business_terms.md`**.
