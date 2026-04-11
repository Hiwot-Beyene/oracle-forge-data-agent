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
- **Purpose**: Entry point for context loading — a lightweight pointer index (~150 chars per entry).
- **Function**: It **lists every other KB document by name with a one-sentence description**. The agent reads MEMORY.md first at session start and **is used to decide which topic files to load next**.
- **Token Budget:** ~200 tokens (strict cap). Growing it beyond this defeats its purpose as an index.
- **Source Logic:** `src/memdir/` handles the index registry. It functions like a table of contents — pointing to topic files, not containing content itself.

### Layer 2 — Topic Files (Detailed Knowledge)

- **Location:** `.claude/memory/` or `kb/domain/`
- **Purpose:** Deep knowledge on specific domains (schemas, deployment, business terms)
- **When loaded:** On-demand when agent encounters relevant task
- **Source Logic:** `src/services/extractMemories/` extracts learnings and writes them back to these files.

### Layer 3 — Session Transcripts (Interaction Memory)

- **Location:** `.claude/sessions/`
- **Purpose:** Searchable record of past interactions.
- **Content Details**: Session transcripts are logs of past agent runs. They record exactly **which queries were asked, which tools were called, and what results came back**.
- **When loaded:** Agent searches only when a new question closely resembles a past one.
- **Context Rule**: Session transcripts are never pre-loaded into context.
- **Cost Logic**: **Searching is cheap, while pre-loading is expensive.** This prevents context window bloat by avoiding unnecessary injections of historical data.
- **Enforcement:** `src/QueryEngine.ts` enforces this never-pre-load discipline.

### Application to Oracle Forge

| Claude Code Pattern | DAB Agent Implementation                                           |
| ------------------- | ------------------------------------------------------------------ |
| MEMORY.md index     | README.md / MEMORY.md — DB connection summary and KB pointers      |
| Topic files         | `kb/domain/` directory with schema details per dataset             |
| Session transcripts | `kb/corrections/log.md` with structured failure logs               |

---
### ⚙️ Injection Test Verification
- **Test Question:** "What is the purpose of MEMORY.md and what token limit applies to it?"
- **Expected Outcome:** Identify MEMORY.md as a lightweight index (~200 tokens) used to decide which topic files to load.
- **Last Status:** ✅ PASS (100/100)
- **Verified On:** 2026-04-11
- **Test Specification:** claude_memory_layers_test.md
