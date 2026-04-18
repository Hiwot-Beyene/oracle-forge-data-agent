# Corrections Changelog

## 2026-04-17

- **Removed E4–E12** — these entries were paper-sourced domain facts with no observed agent failure logs, violating the TRP rule (corrections must be backed by real run traces). Their content is fully covered by `kb/domain/schemas.md` and `kb/domain/join_key_glossary.md`.
- **Rewrote E3b and E3c** — stripped answer leakage (specific correct values mentioned in the entries). Both entries now describe only the correct *approach*, not the correct *answer*.
- **Added Yelp section to `schemas.md`** — MongoDB `business` collection field semantics, attribute interpretation rule, category/state extraction patterns.
- **Added Book Reviews decade extraction note to `schemas.md`** — covers the E2 pattern (year from `details`, decade SQL formula).
- **Added Yelp section to `join_key_glossary.md`** — `businessid_N` ↔ `businessref_N` prefix mapping, MongoDB limit guidance.
- **Updated dataset coverage table** in `log.md` to reflect only observed-failure entries (E1, E3, E3b, E3c).
- **Added TRP compliance note** at top of `log.md` stating the evidence-based standard.

## 2026-04-15

- **Reframed `log.md` as Layer 5 learning memory** (per `kb/architecture/architecture_system_overview.md` and `openai_six_layers.md`): imperative **wrong → right** rules for heterogeneous DAB work, not a dump of runtime errors or terminate reasons.
- **Aligned entry shape to challenge docs:** `kb/architecture/injection_tests/openai_agent_context_test.md` (**query → what was wrong → correct approach**) and `kb/domain/join_key_glossary.md` (**`[Query]` … `[Fix applied]`** / optional join-specific fields).
- **Coverage table** in `log.md` lists all twelve `query_*` bundles; entries **E1–E12** include dedicated **AG News (E4)** and **MusicBrainz (E12)**; PanCancer text aligned to Postgres clinical + **DuckDB** molecular per `db_config.yaml` / glossary.
- Each entry includes **`[Source logs]`** paths to `run_2` harness artifacts (`final_agent.json`, sibling `llm_calls.jsonl` / `tool_calls.jsonl`).
- Recorded **provenance** for harness batch **`run_2`** (`DataAgentBench` + `dab_runs` for Yelp when needed).
