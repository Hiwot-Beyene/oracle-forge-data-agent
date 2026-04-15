# AI-DLC Inception Document — Sprint 01
**Project:** Oracle Forge Data Agent  
**Programme:** TRP1 FDE Programme — Tenacious Intelligence Corp  
**Team:** Team Mistral  
**Prepared by:** Drivers — Nebiyou Belayineh, Hiwot Beyene  
**Date written:** 2026-04-11  
**Status:** Approved by team mob session  

---

## Team Roster

| Name | Role |
|---|---|
| Nebiyou Belayineh | Driver |
| Hiwot Beyene | Driver |
| Martha Ketsla | Intelligence Officer |
| Nahom Desalegn | Intelligence Officer |
| Tsegaye Assefa | Signal Corps |
| Abdulaziz | Signal Corps |

---

## Section 1 — Press Release

Team Mistral has delivered an Oracle Forge data agent that answers natural-language analytics questions across the full DataAgentBench workload and returns evidence with every answer. The agent runs through a layered context flow using `kb/architecture/MEMORY.md`, `kb/domain/schemas.md`, `kb/domain/join_key_glossary.md`, `kb/domain/unstructured_fields.md`, `kb/domain/business_terms.md`, and `kb/corrections/log.md`; this lets the system route queries across PostgreSQL, SQLite, MongoDB, and DuckDB, normalize inconsistent join keys, extract structure from free text when needed, and produce auditable outputs. The evaluation harness records tool traces and validation results per query, then logs pass@1 progress for repeatable measurement across all 54 benchmark queries in 12 datasets. The service is available on the shared server with reproducible setup instructions and team-operable workflows for improvement, validation, and benchmark submission.

---

## Section 2 — Honest FAQ (User Perspective)

**Q1: If I ask about any supported benchmark dataset, will the system answer?**  
Yes. The system is designed around all DAB datasets, not only a starter pair. It first identifies the target dataset and required sources, then runs stepwise retrieval and merge logic. When confidence is low (for example zero-row joins after normalization retries), it returns a transparent response with trace context rather than hiding uncertainty.

**Q2: How do I trust the answer?**  
Every response is paired with execution evidence: tool calls, intermediate query outputs, normalization decisions, and final validation status. Answers are scored against benchmark validators, and mismatches are logged into corrections so repeated failures become explicit engineering tasks.

**Q3: What happens for complex text-heavy questions?**  
The system handles unstructured and semi-structured fields through `execute_python`-driven extraction flows documented in `kb/domain/unstructured_fields.md`, including review sentiment, support transcript interpretation, clinical-note extraction, JSON field parsing, and README-level artifact analysis.

---

## Section 3 — Honest FAQ (Technical Perspective)

**Q1: What is the hardest failure mode?**  
Cross-database entity reconciliation remains the hardest class: key formats may differ (`15/18-char Salesforce IDs`, prefixed IDs, TCGA barcode length differences, ticker-to-table indirection). The team addresses this using the join glossary protocol: sample keys, normalize deterministically, merge in pandas, and log zero-row recoveries.

**Q2: What dependency can break correctness fastest?**  
Schema assumptions drifting from real runtime shape. Several datasets include large or partially discovered schemas (for example CRM and market datasets). Mitigation is mandatory introspection (`list_db` plus sampled queries) before answering, with KB updates and injection-test refresh whenever assumptions change.

**Q3: What is the biggest operational risk?**  
Silent context regressions caused by KB growth without validation. The mitigation is strict injection-test discipline and changelogs in each KB area (`architecture`, `domain`, `evaluation`, `corrections`) so each new entry is verified before being trusted in agent context.

---

## Section 4 — Key Decisions

**Decision 1: Single benchmark-wide architecture instead of dataset-specific agent branches**  
Chosen: One routing and execution architecture for all 12 datasets, with dataset-specific knowledge in KB documents.  
Reason: This keeps behavior consistent and improves maintainability while preserving domain precision.

**Decision 2: Context-first query handling**  
Chosen: Load architecture index + domain semantics + recent corrections before heavy query planning.  
Reason: DAB errors are often context errors, not SQL syntax errors; better context reduces wasted tool calls.

**Decision 3: Stepwise cross-DB merge policy**  
Chosen: Query each source independently, normalize keys, merge in Python; avoid direct cross-engine SQL assumptions.  
Reason: This is the most reliable path for heterogeneous backends and inconsistent identifiers.

**Decision 4: Evidence-driven acceptance**  
Chosen: A task is complete only with a saved artifact (logs, traces, validators, score files, test outputs).  
Reason: Team handover and benchmark submission depend on reproducible evidence, not verbal status.

---

## Section 5 — Full-Delivery Definition of Done

1. **All DAB datasets are mapped and routable.**  
Evidence: `kb/domain/schemas.md` contains entries for all benchmark datasets, and routing checks are recorded in evaluation logs.

2. **Four database engines are operational through MCP tools.**  
Evidence: `mcp/tools.yaml` and runtime tool listing show PostgreSQL, SQLite, MongoDB, and DuckDB access.

3. **Context architecture is live and verifiable.**  
Evidence: prompt traces confirm loading of `MEMORY.md`, domain docs, and recent correction entries before answer generation.

4. **Join-key normalization is implemented as a standard path.**  
Evidence: runs involving mixed ID formats show normalization steps and successful post-normalization merge behavior.

5. **Unstructured and semi-structured extraction pathways are active.**  
Evidence: successful runs on text/JSON dependent queries use `execute_python` with saved extraction traces.

6. **Business-term semantics are enforced in metric computation.**  
Evidence: query answers involving terms like `repeat purchase rate`, `intraday volatility`, `BANT`, `BRCA`, and `Pass@1` align with `kb/domain/business_terms.md`.

7. **Evaluation harness supports repeated scoring and regression visibility.**  
Evidence: `eval/scores/score_log.jsonl` includes timestamped run lines with per-query validity and pass@1 trends.

8. **Corrections loop is active and used in subsequent runs.**  
Evidence: `kb/corrections/log.md` contains failure->fix entries and later traces show those corrections referenced.

9. **Knowledge base quality gates are active.**  
Evidence: injection test files under `kb/architecture/injection_tests/` and `kb/domain/injection_tests/` pass and are updated with changes.

10. **Shared utility modules are tested and reusable.**  
Evidence: `utils/` includes at least three reusable modules with tests and usage documentation.

11. **Service access is team-wide and reproducible.**  
Evidence: API endpoint responds from the shared server; `README.md` setup works from a clean clone by a non-driver member.

12. **Benchmark submission package is ready.**  
Evidence: `results/` output, architecture note, and submission checklist artifacts are complete and reviewable.

---

## Section 6 — Dataset Coverage Plan (All 12)

| Dataset | Engines | Key complexity focus |
|---|---|---|
| `query_agnews` | MongoDB + SQLite | category/region split and article join integrity |
| `query_bookreview` | PostgreSQL + SQLite | metadata + review merge, review text interpretation |
| `query_crmarenapro` | SQLite + DuckDB + PostgreSQL | Salesforce ID formats, BANT extraction, multi-source joins |
| `query_DEPS_DEV_V1` | SQLite + DuckDB | JSON advisory/license parsing and package-project linking |
| `query_GITHUB_REPOS` | SQLite + DuckDB | language filtering + README artifact analysis |
| `query_googlelocal` | PostgreSQL + SQLite | `gmap_id` joins, business/review text and JSON fields |
| `query_music_brainz_20k` | SQLite + DuckDB | track identity consistency for revenue joins |
| `query_PANCANCER_ATLAS` | PostgreSQL + DuckDB | cohort semantics, TCGA IDs, clinical + molecular merge |
| `query_PATENTS` | PostgreSQL + SQLite | CPC hierarchy mapping at scale |
| `query_stockindex` | SQLite + DuckDB | index metadata + OHLC analytics |
| `query_stockmarket` | SQLite + DuckDB | ticker resolution and per-symbol table access |
| `query_yelp` | DuckDB + MongoDB | nested data, entity resolution, heterogeneous joins |

---

## Section 7 — Execution Sequence

| Phase | Primary objective | Output artifact |
|---|---|---|
| Environment and data readiness | Load DAB assets and validate engines/tools | `planning/evidence/infra_checks/*` |
| Context baseline | Freeze KB v1/v2 with injection proof | `kb/*/CHANGELOG.md` + injection logs |
| Agent routing and execution loop | Complete all-engine query and merge flow | tool traces + run logs |
| Evaluation and corrections loop | Run, score, capture failures, apply fixes | `eval/scores/score_log.jsonl` + `kb/corrections/log.md` |
| Submission packaging | Assemble reproducible repository and benchmark outputs | `results/*` + updated `README.md` |

---

**Mob approval record:** `planning/sprint_01_mob_approval.md`

---

*Document version: 2.1 — deduplicated and aligned with separate mob approval file*  
*Review baseline: Full benchmark readiness and dataset-wide delivery*  
*Programme: TRP1 FDE Programme · Tenacious Intelligence Corp · April 2026*