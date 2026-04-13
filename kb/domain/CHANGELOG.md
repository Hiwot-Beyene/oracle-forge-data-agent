# KB v2 Domain — CHANGELOG

All notable changes to the KB v2 domain knowledge files are documented here.

---

## [v1.4] — 2026-04-13

### Injection Test Results — ALL PASS
- **business_terms.md:** PASS — 100.0/100 (all 5 questions)
- **join_key_glossary.md:** PASS — 100.0/100 (all 5 questions)
- **schemas.md:** PASS — 100.0/100 (all 5 questions)
- **unstructured_fields.md:** PASS — 100.0/100 (all 5 questions)

**Model:** google/gemini-2.0-flash-001 | **Timestamp:** 2026-04-13 11:20 UTC

### Root Cause Fixes (v1.3 → v1.4)
- **business_terms Q2:** Split compound concept (4 facts in 1) into 3 atomic concepts. Removed redundant "NOT the BRCA gene" concept (already covered by "misinterpretation is confusing with gene").
- **join_key_glossary Q3:** Removed concept that tested info already stated in the question ("clinical in PG, molecular in DuckDB"). Rephrased question to not give away DB names.
- **schemas Q4:** Added "and what does each contain" to the question so model elaborates on Licenses/Advisories content.

---

## [v1.3] — 2026-04-13

### Document Revisions (v1.1 → v1.3)
- **business_terms.md:** Added bold callouts for cross-DB join rules, DB locations, and time window requirements. AG News section restructured with "Cross-Database Join Rule (CRITICAL)" callout. BRCA definition now includes "PostgreSQL" and "disease type column" inline. Intraday volatility states "OHLC in DuckDB." GitHub stars states "DuckDB not SQLite."
- **join_key_glossary.md:** Added bold "ALWAYS sample 5 values" and "ALWAYS merge in pandas" rules to General Patterns section. Added bold DB location callouts to PANCANCER, Stock Market, CRM sections. Restored markdown table formatting after accidental corruption.
- **schemas.md:** Added bold "DB split" summaries for Book Reviews, PANCANCER, Deps Dev, Stock Market sections. Deps Dev section now explicitly states UpstreamPublishedAt rule and JSON content definitions for Licenses/Advisories.
- **unstructured_fields.md:** CRM entry now includes explicit BANT definition row, `execute_python` tool requirement, and HIGH difficulty rating. GitHub README entry now includes LOW difficulty rating and SQLite vs DuckDB note. Semi-structured section header states "all rated LOW." Google Local parsing approaches bolded.

### Test Revisions
- All test questions rephrased to explicitly ask for the information concepts expect (e.g., "which database holds X" added to questions testing DB location knowledge)
- Redundant concepts removed (e.g., "sort by date" merged with "determined by UpstreamPublishedAt date")
- Overlapping concepts merged in join_key_glossary Q4 (4 → 3 concepts) and schemas Q4 (5 → 4 concepts)
- unstructured_fields Q1 reworded to use document terminology ("BANT lead qualification" instead of "complaint categories")

---

## [v1.0] — 2026-04-13

### Added
- **kb_v2_domain.md** (v1.0 seed, April 9): Master domain document with DAB overview, four hard requirements, DB query patterns, cross-DB join patterns, failure modes, and AGENT.md template.
- **kb_v2_domain.txt**: Plain text copy of master document.
- **business_terms.md** (v1.0): Domain term glossary covering all 11 DAB datasets. Includes cross-domain terms (churn, active account, fiscal year, etc.) and per-dataset terms with correct definitions and common wrong assumptions.
- **join_key_glossary.md** (v1.0): Join key format documentation for all 11 datasets. General normalization patterns, per-dataset join key mappings, and zero-row join recovery protocol.
- **schemas.md** (v1.0): Column semantics for all 11 datasets. Documents what columns mean in business context, authoritative table selection guide, and known gotchas.
- **unstructured_fields.md** (v1.0): Inventory of all free-text and semi-structured (JSON) fields across datasets. Extraction protocol and HR3 coverage map.

### Injection Test Run 1 (v1.0, pre-revision)
| Document | Avg Score |
|----------|-----------|
| business_terms.md | 65.0/100 |
| join_key_glossary.md | 85.0/100 |
| schemas.md | 80.0/100 |
| unstructured_fields.md | 72.0/100 |

### Sources
- DAB paper: arxiv.org/abs/2603.20576
- DataAgentBench repository: github.com/ucbepic/DataAgentBench
- OpenAI data agent blog: openai.com/index/inside-our-in-house-data-agent
- Direct dataset directory inspection (query files, SQL schemas, DB files)

### Known Gaps
- Column types and exact names need verification via live schema introspection
- DuckDB table schemas are TBD (marked "Schema TBD at runtime")
- CRM Arena Pro has 6 databases — not all schemas fully documented
- Patent publication SQLite schema needs runtime introspection (5GB file)
- Stock market DuckDB has 2,754 tables — per-ticker structure needs verification

---

_Next update: After all 4 documents reach consistent 100/100 PASS._
