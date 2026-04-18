# Oracle Forge Architecture — Knowledge Index

This file is the **Index Layer (KB v1)** for the Oracle Forge Knowledge Base: lightweight pointers to architecture docs under `kb/architecture/`. **`agent/context_loader.py` loads Layer 1 from this directory only** (`MEMORY.md` + `architecture_system_overview.md`) — not from `kb/domain/`.

**Session start (challenge model):** Layer 2 = **domain** (`kb/domain/` — `business_terms.md` per dataset, `join_key_glossary.md`, `unstructured_fields.md` excerpt). Layer 3 = **corrections** (`kb/corrections/log.md` tail). Operational “Forge” hints for DAB live under **### Oracle Forge — session injection** inside each dataset section of `business_terms.md`, not in Python code.

- architecture_system_overview.md: Core design philosophy and the four KB subdirectories.
- claude_memory_layers.md: The three-layer memory architecture (Pointer, Knowledge, Transcripts).
- claude_autodream.md: Post-session background memory consolidation process.
- claude_tool_scoping.md: Philosophy of tight domain boundaries for tool reliability.
- openai_six_layers.md: Six-layer institutional context architecture (PG/Mongo rules).
- openai_table_enrichment.md: Codex-powered schema enrichment and filtering assumptions.
- oracle_forge_mapping.md: Mapping of reference designs to our active codebase.
- CHANGELOG.md: History of architectural modifications and testing runs.

**DAB / schema:** When the harness `DATABASE DESCRIPTION` omits fields (e.g. Mongo `categories`), agents must **discover** live keys via **`list_db`** and sample **`query_db`** — see `kb/domain/business_terms.md` → Yelp → **Schema discovery**, and `kb/corrections/log.md` E3 (learning, not raw run logs).

**Stock indices (`query_stockindex`):** OHLC in DuckDB `index_trade`; symbols in **`Index`**. Up/down day semantics and answer shapes (symbols + countries) — `business_terms.md` → **Stock Index (query_stockindex)**; E6 in `kb/corrections/log.md`.

**Book reviews (`query_bookreview`):** Forge injects the full **`## Book Reviews`** section (not the first page of `business_terms.md`). Join keys and verbatim titles — `join_key_glossary.md`; E1–E2 in `kb/corrections/log.md`.
