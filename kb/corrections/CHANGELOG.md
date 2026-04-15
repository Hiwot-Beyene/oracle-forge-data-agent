# Corrections Changelog

## 2026-04-15

- **Reframed `log.md` as Layer 5 learning memory** (per `kb/architecture/architecture_system_overview.md` and `openai_six_layers.md`): imperative **wrong → right** rules for heterogeneous DAB work, not a dump of runtime errors or terminate reasons.
- **Aligned entry shape to challenge docs:** `kb/architecture/injection_tests/openai_agent_context_test.md` (**query → what was wrong → correct approach**) and `kb/domain/join_key_glossary.md` (**`[Query]` … `[Fix applied]`** / optional join-specific fields).
- **Coverage table** in `log.md` lists all twelve `query_*` bundles; entries **E1–E12** include dedicated **AG News (E4)** and **MusicBrainz (E12)**; PanCancer text aligned to Postgres clinical + **DuckDB** molecular per `db_config.yaml` / glossary.
- Each entry includes **`[Source logs]`** paths to `run_2` harness artifacts (`final_agent.json`, sibling `llm_calls.jsonl` / `tool_calls.jsonl`).
- Recorded **provenance** for harness batch **`run_2`** (`DataAgentBench` + `dab_runs` for Yelp when needed).
