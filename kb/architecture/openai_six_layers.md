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
| 5 | **Learning Memory** | Structured log of failures/corrections (Last 10 entries). |
| 6 | **Runtime Context** | Live fallback via `query_db` and `execute_python`. |

### Application to Oracle Forge

| OpenAI Layer | DAB Agent Implementation |
| :--- | :--- |
| 1: Raw Schema | MCP Toolbox introspection |
| 3: Codex Enrichment | Pipeline logic extraction (Week 3 pipeline) |
| 5: Learning Memory | `kb/corrections/log.md` failures log |

**Performance Impact:** OpenAI found that a query taking **22 minutes** without Layer 5 memory dropped to **1 minute 22 seconds** with it enabled.

### DAB Failure Scenarios
- **Join Key Mismatch**: PostgreSQL uses integers; MongoDB uses strings (e.g., `CUST-00123`). Layer 5 must document this zero-padding or formatting rule.
- **Ambiguous Definitions**: "Active Customer" means a purchase in the last 90 days, not just a row in the users table.

---
### ⚙️ Injection Test Verification
- **Test Question:** "What is Layer 5 in this architecture and what is the Oracle Forge equivalent?"
- **Expected Outcome:** Identify Learning Memory and link it to kb/corrections/log.md.
- **Last Status:** 
- **Verified On:** 2026-04-11
- **Test Specification:** openai_six_layers_test.md
