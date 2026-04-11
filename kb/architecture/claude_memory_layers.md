# Claude Code — Three-Layer Memory Architecture

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: Claude Code npm leak, March 31 2026 — 512,000 lines TypeScript_

### Core Insight

Claude Code solves "context entropy" — the tendency for long agent sessions to become
confused — through a three-layer memory architecture that treats memory as an
**external system**, not part of the context window.

### Layer 1 — MEMORY.md (Index Layer)

- **Location:** Project root
- **Purpose:** Entry point for context loading — lightweight pointer index (~150 chars per entry)
- **Token Budget:** ~200 tokens (strict cap)
- **When loaded:** At every session start — mandatory pre-load
- **Source Logic:** `src/memdir/` handles the index registry. It functions like a table of contents — pointing to topic files, not containing content itself.

### Layer 2 — Topic Files (Detailed Knowledge)

- **Location:** `.claude/memory/` or `kb/domain/`
- **Purpose:** Deep knowledge on specific domains (schemas, deployment, business terms)
- **When loaded:** On-demand when agent encounters relevant task
- **Source Logic:** `src/services/extractMemories/` extracts learnings and writes them back to these files.

### Layer 3 — Session Transcripts (Interaction Memory)

- **Location:** `.claude/sessions/`
- **Purpose:** Searchable record of past interactions
- **When loaded:** Agent searches only when needed; **never** pre-loaded
- **Enforcement:** `src/QueryEngine.ts` (~46K lines) enforces the never-pre-load discipline for transcripts.

### Application to Oracle Forge

| Claude Code Pattern | DAB Agent Implementation                                           |
| ------------------- | ------------------------------------------------------------------ |
| MEMORY.md index     | README.md / MEMORY.md — DB connection summary and KB pointers      |
| Topic files         | `kb/domain/` directory with schema details per dataset             |
| Session transcripts | `kb/corrections/log.md` with structured failure logs               |

---
### ⚙️ Injection Test Verification
- **Test Question:** "What is the purpose of MEMORY.md and why is it capped at 200 tokens?"
- **Expected Outcome:** Correct description of index layer and context budget preservation logic.
- **Last Status:** ✅ PASS (100/100)
- **Verified On:** 2026-04-11
- **Test Specification:** [claude_memory_layers_test.md](file:///g:/projects/group/oracle-forge-data-agent/kb/architecture/injection_tests/claude_memory_layers_test.md)
