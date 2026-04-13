# OpenAI Data Agent — Six-Layer Context Architecture

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: OpenAI Engineering Blog, January 29 2026_

_Scale: 600+ PB, 70,000 datasets, 3,500+ internal users_

### The Core Problem

Finding the right table across 70,000 datasets is the hardest sub-problem. Many tables look similar but differ critically (e.g., US users only vs. all users). **Layer 3 (Codex Enrichment)** is the most critical for solving this in production.

### The Six Layers (cumulative — each builds on the previous)

| Layer | Name | What It Provides |
| :--- | :--- | :--- |
| 1 | **Raw Schema** | Table names, column names, data types via `list_db`. |
| 2 | **Expert Descs** | Human-curated notes on table contents and caveats. |
| 3 | **Codex Enrichment** | Logic extracted from the code that *generates* the data. |
| 4 | **Institutional** | Product launch notes, incident reports, metric definitions. |
| 5 | **Learning Memory (self-correction loop)** | Stores corrections and nuances from previous conversations and applies them automatically to future requests. Reads the last 10 entries at session start. |
| 6 | **Runtime Context** | Live fallback via `query_db` and `execute_python`. |

### Application to Oracle Forge

| OpenAI Layer | DAB Agent Implementation |
| :--- | :--- |
| 1: Raw Schema | MCP Toolbox introspection |
| 3: Codex Enrichment | Pipeline logic extraction (Week 3 pipeline) |
| 5: Learning Memory | **Learning Memory (self-correction loop)** via `kb/corrections/log.md` (Reads the last 10 entries at session start) |

**Performance Impact of Layer 5:** OpenAI found that a query taking **22 minutes** without memory dropped to **1 minute 22 seconds** with the self-correction loop enabled.

### The Closed-Loop Self-Correction Pattern
- **Not Error Handling:** Error handling reacts to exceptions raised by the system. Self-correction evaluates the quality of the agent's own reasoning even when *no exception is raised*.
- **The Rule:** An answer that looks correct but uses the wrong table will not trigger an exception. Self-correction catches this by checking if the result is plausible before returning it (implemented in `self_corrector.py`).

### Key Engineering Lessons
1. **Tool Consolidation:** Overlapping tools confuse the agent. Restrict to one specific tool per context.
2. **Code Reveals What Metadata Hides:** Reading pipeline code tells you what was filtered and assumed, which never surfaces in SQL schemas.

### DAB Failure Scenarios
- **Join Key Mismatch**: PostgreSQL uses integers; MongoDB uses strings (e.g., `CUST-00123`). Layer 5 must document this zero-padding or formatting rule.
- **Ambiguous Definitions**: "Active Customer" means a purchase in the last 90 days, not just a row in the users table.

---
### ⚙️ Injection Test Verification
- **Test Questions Check:** Layer 5 equivalency, join key handling, and Closed-Loop Self-Correction.
- **Expected Outcome:** Identify Learning Memory (log.md), format overrides, and proactive quality evaluation vs error handling.
- **Last Status:** ✅ VERIFIED (100/100)
- **Verified On:** 2026-04-11
- **Test Specification:** openai_six_layers_test.md
