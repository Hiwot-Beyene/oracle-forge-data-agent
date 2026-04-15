# AGENT.md — Team Mistral Oracle Forge Data Agent

_TRP1 FDE Programme · Tenacious Intelligence Corp · April 2026_
_Status: Sprint 1 — interim submission (2026-04-15)_

This file is loaded at every session start as the agent's primary context
index. It points into `kb/` for deeper knowledge rather than duplicating it,
and it is the architecture description that ships with the DataAgentBench PR.

---

## Mission

The Oracle Forge is a natural-language data analyst over DataAgentBench's
heterogeneous databases. It accepts a plain-English business question,
routes sub-queries across PostgreSQL, SQLite, and MongoDB (DuckDB planned),
reconciles ill-formatted join keys, and returns a verifiable answer with a
full query trace. Every answer is traceable to the tool calls that produced it.

---

## Databases and MCP tools (`agent/mcp/tools.yaml`)

| Source | Kind | Dataset |
|---|---|---|
| `dab-postgres-bookreview` | postgres | bookreview |
| `dab-sqlite-bookreview` | sqlite | bookreview |
| `dab-mongo-yelp` | mongodb | yelp |

| Tool | Kind | Purpose |
|---|---|---|
| `postgres-bookreview` | postgres-sql | Read-only SQL on `books_info` (book metadata) |
| `sqlite-bookreview` | sqlite-sql | Read-only SQL on `review` (Amazon reviews) |
| `mongo-yelp-business` | mongodb-find | Yelp business collection (metadata, not ratings) |
| `mongo-yelp-aggregate` | mongodb-aggregate | Yelp business aggregations |

**Toolsets:** `dab-all`, `dab-bookreview`, `dab-yelp`, `dab-relational`.

**Critical cross-database facts** (must not be inferred from field names):

- **bookreview join**: `books_info.book_id` (PostgreSQL) = `review.purchase_id`
  (SQLite). The field is named `purchase_id` but is a book foreign key.
- **yelp ratings split**: MongoDB `yelp_db.business` holds business metadata
  only — there is no per-business star rating on this collection. Review
  scores live in DuckDB `review.rating`. Rating math requires crossing the
  MongoDB → DuckDB boundary.
- **DuckDB via MotherDuck** is noted as Future in `tools.yaml` and is not yet
  wired into MCP; DuckDB files are currently executed in the Flask app path
  with optional `MOTHERDUCK_TOKEN` + `DUCKDB_LOCAL_USE_MOTHERDUCK=1`.

---

## Three-layer context architecture (`agent/context_loader.py`)

Loaded on every session start via `build_context_layers(dataset, question)`.
Dataset is auto-detected from the question text when not provided, via
`DATASET_ALIASES` and `infer_canonical_dataset_from_question()`. Each layer
is capped at `max_layer_chars` (default 9000) with a truncation marker.

### Layer 1 — Architecture (pre-question, always loaded)

From `kb/architecture/`:

- `MEMORY.md` — KB index and pre-load budget.
- `architecture_system_overview.md` — design philosophy and KB layout.
- `claude_tool_scoping.md` — why each DB has its own tool.
- `oracle_forge_mapping.md` — reference designs → this codebase.

### Layer 2 — Domain (dataset-scoped, loaded after question)

From `kb/domain/`:

- `business_terms.md` — ambiguous term definitions.
- `join_key_glossary.md` — per-dataset entity-ID formats and join rules.
- `unstructured_fields.md` — which fields require text extraction.
- `schemas.md` — **sliced to the detected dataset's section only**, not
  loaded whole (see `_extract_dataset_scoped_schema`).

### Layer 3 — Corrections memory (pre-question, tail-only)

From `kb/corrections/log.md` — last ~120 lines. Read at session start;
appended after every observed failure. This is the self-learning loop.

Two additional entry points expose the same layers for the router/planner:
`build_agent_session_kb_context()` and `build_router_planner_user_payload()`.

---

## Key design decisions (from `planning/sprint_01_inception.md` §4)

1. **LLM provider — OpenRouter** via the `openai` Python SDK
   (`base_url=https://openrouter.ai/api/v1`). Reason: single unified endpoint
   covering hundreds of models through the standard OpenAI interface; the
   team does not have Azure/Gemini/Together keys.
2. **Starting model — `anthropic/claude-3.5-sonnet`** for smoke tests and
   baseline; `meta-llama/llama-3.1-8b-instruct:free` as fallback. Reason:
   confirmed tool-calling support on OpenRouter and the Claude family
   appears on the DAB leaderboard.
3. **Starting datasets — `bookreview` then `yelp`**. Reason: `bookreview`
   is the DAB README's own example (simplest schema, lowest-risk pipeline
   validation); `yelp` adds MongoDB for multi-engine coverage.
4. **Access — FastAPI REST on the shared server** at
   `http://[server-ip]:8000/query`. Reason: tenai-infra ran once but
   blocked on subsequent attempts; FastAPI gives facilitator-accessible
   agent access without requiring Tailscale/tmux from non-Drivers.
5. **Context as a separate, testable module** — `agent/context_loader.py`.
   Reason: Intelligence Officers can run injection tests on KB documents
   without needing a running database connection.
6. **Sandbox — DAB's built-in Docker sandbox** (`python-data:3.12` via
   `common_scaffold/tools/ExecTool.py`). Reason: already implemented in
   the scaffold; building a separate sandbox wastes Sprint 1 time.

---

## How we address DAB's four hard requirements

| DAB requirement | Current handling |
|---|---|
| **Multi-database integration** | MCP Toolbox per-source tools; toolsets per dataset; cross-DB joins executed in the Docker sandbox via `execute_python`. `query_router.py` stub exists for Sprint 2 consolidation. |
| **Ill-formatted join keys** | Documented per-dataset in `kb/domain/join_key_glossary.md` (e.g. bookreview `book_id` ↔ `purchase_id`). Detection + format-aware normalisation is in `join_key_resolver.py` (stub; Sprint 2). Currently mismatches are detected at runtime and logged to corrections. |
| **Unstructured text transformation** | Inventory in `kb/domain/unstructured_fields.md`. Pipeline (`text_extractor.py`) is a Sprint 2 stub. |
| **Domain knowledge** | `kb/domain/business_terms.md` injected in Layer 2 on every session. |

---

## Self-correction

Currently a **write-only loop**: failed runs trigger a structured entry in
`kb/corrections/log.md`, which is then re-read at the next session's Layer 3.
The closed-loop in-session self-corrector (`self_corrector.py`, Sprint 2)
will diagnose the failure class (query error / join key format / DB type /
data quality) and retry before surfacing the error to the user.

---

## Evaluation harness (`eval/`)

- `harness.py` — entrypoint; scores held-out DAB traces against ground truth.
- `scorer.py` — pass@1 scoring via DAB `validate_outputs.py`.
- `trace_logger.py` — per-run tool-call trace (writes `trace_summary.jsonl`).
- `regression_suite.py` — compares a run against prior passes.
- `config.yaml` / `config_loader.py` — profiles: `first_run`, `submission`.
- `held_out/manifest.yaml` — 12-dataset held-out test set (query1 per dataset).
- `scores/score_log.jsonl` — append-only JSONL score log.

### Baseline → current (held-out, 2 datasets with DAB traces)

| Run | Profile | Traces scored | trace_overrides | n_pass / n_total | pass@1 |
|---|---|---|---|---|---|
| `20260415T131132Z_first_run` | `first_run` | bookreview `run_0`, yelp `run_0` | — | 1 / 2 | **0.5000** |
| `20260415T131132Z_submission` | `submission` | bookreview `run_4`, yelp `run_1` | — | 2 / 2 | **1.0000** |

**What moved the score (yelp):** baseline `run_0` answered `"4.0"` for the
average business rating in Indianapolis; submission `run_1` answered `"3.55"`
and matched ground truth `"≈ 3.55"`. The difference is cross-collection
reasoning — correctly joining MongoDB `yelp_db.business` metadata with DuckDB
`review.rating`, which is the Layer 2 `join_key_glossary.md` + schema-slice
guidance at work rather than raw LLM capability. Bookreview passes at both
baseline and submission, confirming the simpler PG ↔ SQLite path is stable.

**What's excluded:** the other 10 datasets in the manifest (`agnews`,
`stockmarket`, `stockindex`, `crmarenapro`, `googlelocal`, `PATENTS`,
`PANCANCER_ATLAS`, `GITHUB_REPOS`, `DEPS_DEV_V1`, `music_brainz_20k`) have
no traces yet in the DAB clone, so the harness skips them
(`reason: missing_trace`) and excludes them from pass@1. Sprint 2 expands
coverage using the same validated ingestion and context pattern.

---

## How to run

Bootstrap the three-layer context for a question (prints warnings and a
system-prompt preview):

```bash
python -m agent.main \
  --dataset query_yelp \
  --question "Which businesses have the highest average rating by city?" \
  --print-layers
```

Start the MCP Toolbox (serves the tools above on `:5000`):

```bash
./toolbox --config agent/mcp/tools.yaml
curl http://localhost:5000/v1/tools | python3 -m json.tool | grep name
```

Run the held-out evaluation (regenerates `eval/scores/score_log.jsonl`):

```bash
DAB_ROOT=/path/to/DataAgentBench python -m eval --reset-log
```

---

## What works / what's pending (as of 2026-04-15)

**Delivered** (from `planning/sprint_01_operations.md` §2):

- AI-DLC governance complete — Inception, mob approval, Operations all in
  `planning/`.
- KB architecture and domain complete with injection tests at
  `kb/architecture/injection_tests/` and `kb/domain/injection_tests/`.
- Two datasets loaded and smoke-tested: `query_bookreview`, `query_yelp`.
- Evaluation harness producing a baseline and a submission-profile run
  with trace logs. pass@1 improved from 0.5 → 1.0 across the two datasets.
- Three-layer context loader running; both `query_bookreview` and
  `query_yelp` passing end-to-end under the submission profile.

**Pending / Sprint 2:**

- `join_key_resolver.py`, `query_router.py`, `self_corrector.py`,
  `text_extractor.py` — stubs exist, implementations pending.
- `kb/corrections/log.md` population beyond the initial entries.
- Full DAB dataset coverage beyond `bookreview` + `yelp` (10 datasets not
  yet run against DAB).
- DuckDB / MotherDuck wiring in `agent/mcp/tools.yaml` (currently "Future").
- LinkedIn / Medium articles (Signal Corps Sprint 2).

---

## References

- `planning/sprint_01_inception.md` — written commitment and DoD.
- `planning/sprint_01_operations.md` — current delivery status.
- `planning/sprint_01_mob_approval.md` — approval record.
- `docs/guides/Oracle_Forge_Driver_Execution_Guide.md` — Driver runbook.
- `docs/guides/DAB_SETUP.md` — database and sandbox setup.
- DataAgentBench: https://github.com/ucbepic/DataAgentBench
- DAB paper: https://arxiv.org/html/2603.20576
