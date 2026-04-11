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

**Usage in Agent:** All documents in this directory are injected into the agent's baseline context. They define the architectural "ground truth" that governs tool selection and memory management.

**Verification (The Karpathy Method):**
Every document must pass a structured **Injection Test** before it is considered valid.
- **Protocol**: 
    1. Fresh LLM session (no baseline context).
    2. Paste document as the ONLY information.
    3. Run `python kb/architecture/injection_tests/run_injection_tests.py --doc <doc_name>`.
    4. Grader requires **100/100** score (all concepts present, no contradictions).
- **Automation**: Test rubrics and results are stored in the injection_tests/

**Maintenance:** Knowledge is a garden, not a dumpster. Pruning is mandatory. Remove pre-training generalities; keep only DAB-specific precision.

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
│       └── architecture_system_overview_test.md
```
