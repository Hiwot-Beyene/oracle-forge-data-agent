# Mapping to Oracle Forge — Minimum Required Implementation

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

| OpenAI Layer            | Oracle Forge Equivalent                              | File Location                         |
| ----------------------- | ---------------------------------------------------- | ------------------------------------- |
| Raw Schema              | MCP Toolbox introspection + `build_unified_schema()` | `utils/oracle_forge_utils.py`         |
| Column Semantics        | Schema descriptions + domain term glossary           | `kb/domain/schema_descriptions.md`    |
| Query Patterns          | Successful query log                                 | `kb/domain/query_patterns.md`         |
| Institutional Knowledge | Domain terms + join key glossary                     | `kb/domain/domain_terms.md`           |
| Learning Memory         | Corrections log                                      | `kb/corrections/kb_v3_corrections.md` |
| Runtime Context         | Direct DB query tools                                | `agent/tools.yaml` (MCP config)       |

---
