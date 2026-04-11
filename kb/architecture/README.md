# Architecture Knowledge Base

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

## Document Index

| File                                       | Content                                      |
| ------------------------------------------ | -------------------------------------------- |
| `architecture_system_overview.md`          | High-level system architecture and layers    |
| `claude_memory_layers.md`                  | Three-layer MEMORY.md pattern                |
| `claude_tool_scoping.md`                   | 40+ tools with tight boundaries              |
| `claude_autodream.md`                      | Background memory consolidation pattern      |
| `openai_six_layers.md`                     | Context architecture (schema → preferences)  |
| `openai_table_enrichment.md`               | Codex-powered schema enrichment              |
| `oracle_forge_mapping.md`                  | Implementation mapping to Oracle Forge       |

**Usage in Agent:** All documents in this directory are injected into the agent's
system prompt at session start via `agent/context_builder.py`. The agent does not
need to request them — they are part of its baseline knowledge.

**Verification:** Every document has passed an injection test (see `injection_tests/`
directory). Protocol: (1) fresh LLM session, (2) document loaded as only context,
(3) specific question asked, (4) answer matches expected.

**Maintenance:** Updates by Intelligence Officers only. Mob session review required
before modification. All changes recorded in `CHANGELOG.md`.

---

## Directory Structure

```
kb/
├── architecture/
│   ├── README.md                    # This document
│   ├── CHANGELOG.md                 # Version tracking
│   ├── architecture_system_overview.md
│   ├── claude_memory_layers.md      # The 3-layer MEMORY.md pattern
│   ├── claude_tool_scoping.md       # 40+ tools with tight boundaries
│   ├── claude_autodream.md          # Memory consolidation pattern
│   ├── openai_six_layers.md         # Context architecture from OpenAI
│   ├── openai_table_enrichment.md   # Codex-powered schema resolution
│   ├── oracle_forge_mapping.md      # Oracle Forge specific mapping
│   └── injection_tests/
│       ├── claude_memory_layers_test.md
│       ├── claude_tool_scoping_test.md
│       ├── claude_autodream_test.md
│       ├── openai_six_layers_test.md
│       ├── openai_table_enrichment_test.md
│       └── test_combined.md
```
