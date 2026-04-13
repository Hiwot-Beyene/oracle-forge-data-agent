# The Oracle Forge Architecture — System Overview

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

```
USER INPUT (Natural Language Question)
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│               LAYER 1: CONTEXT COMPILER (The Driver)                  │
│   Responsibility: Assemble the exact context window for the LLM.      │
│                                                                       │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌────────────────┐  │
│  │  KB v1/v2 (Static)  │ │ KB v3 (Corrections) │ │Schema Introsp. │  │
│  │  - Domain Terms     │ │ - "Last time we     │ │- MCP Toolbox   │  │
│  │  - Join Key Glossary│ │   failed on ID fmt" │ │  Routing Info  │  │
│  └─────────────────────┘ └─────────────────────┘ └────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│               LAYER 2: REASONING & ROUTING (LLM)                      │
│   Prompt: "You have access to PG, Mongo, SQLite. Use the glossary     │
│            to resolve 'churn'. Check corrections log before executing."│
└───────────────────────────────────────────────────────────────────────┘
        │
        │  (Agent outputs: Plan to query PG users + Mongo support_notes)
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│           LAYER 3: SELF-CORRECTING EXECUTION LOOP                     │
│                   (The Sentinel / Sandbox)                            │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │  PostgreSQL  │  │   MongoDB    │  │  Unstructured Extraction  │    │
│  │  (Users)     │─▶│  (Tickets)   │  │  (Week 3 pipeline)        │    │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘    │
│                           │                                           │
│                           ▼                                           │
│                  ┌─────────────────────┐                              │
│                  │   JOIN RESOLVER     │ ◀── FAILS? (ID mismatch)     │
│                  │  ──RETRY──▶ Write to KB v3                         │
│                  └─────────────────────┘                              │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      EVALUATION HARNESS                               │
│  - Traces every tool call (PostgreSQL tool, Mongo tool, Python exec)  │
│  - Compares output to DAB Expected Result                             │
│  - Updates Score Log                                                  │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
FINAL VERIFIABLE OUTPUT + TRACE
```

**How the three KB documents map to this architecture:**

- **KB v1** (this document) feeds Layer 1 — the architectural patterns that govern
  how the context compiler, routing logic, and execution loop are designed
- **KB v2** feeds Layer 1 — the domain knowledge (schema descriptions, join key
  glossary, domain terms) injected before every query
- **KB v3** feeds Layer 1 — the corrections log injected as "do not repeat these
  mistakes" at the start of every session

## The Four KB Subdirectories

### kb/architecture/
Contains documents about how the agent itself works: the memory architecture, tool scoping rules, context loading order, and this structural overview. Documents here are written for the agent, about the agent. They change when the agent architecture changes.

### kb/domain/
Contains documents about the data: schema descriptions per DAB dataset, join key formats, and business term definitions. Documents here change when datasets are loaded or new failure patterns reveal schema misunderstandings.

### kb/evaluation/
Contains documents about how the agent is scored: DAB query format, pass@1 scoring, and failure taxonomy.

### kb/corrections/
`kb/corrections/log.md` is the self-learning loop. It is a running structured log of agent failures written by Drivers after every failure. The agent reads the last 10 entries at session start.

## The Karpathy Method — Minimum Content, Maximum Precision

The Karpathy discipline is **removal, not accumulation**. 
- Every document must be minimal and precise. 
- Every document must pass an **Injection Test** before committing.
- Remove everything the LLM already knows from pretraining; include only DAB-specific knowledge.
- The test for every sentence is: "If the agent read only this sentence with no other context, could it take the correct action?"

## Worktree Sub-Agent Spawn Modes (Claude Code Pattern)

The agent uses git worktrees to achieve process isolation for parallel experiments. 
- **Isolated Testing:** Multiple trial runs of the same query run in isolation (`src/tools/EnterWorktreeTool.ts`) to prevent state corruption.
- **Aggregation:** Their results are aggregated by the execution harness after trials finish.
- **Rule:** Never test destructive modifications directly in the primary workspace. Always spawn a sub-agent into an isolated worktree.

## Token Budget Summary

| Document | Budget | Load Type |
| :--- | :--- | :--- |
| **MEMORY.md** | ~200 tok | Mandatory (Pre-load) |
| **tool_scoping.md** | ~300 tok | Mandatory (Pre-load) |
| **corrections/log.md**| ~400 tok | Mandatory (Pre-load) |
| **Topic Docs** | ~300-400 tok | On-Demand/Post-Question |

**Total mandatory pre-load goal: ~900 tokens.**

---
### ⚙️ Injection Test Verification
- **Test Questions Check:** 4 KB subdirectories, Karpathy Method rules, and Worktree Sub-Agent details.
- **Expected Outcome:** Identification of architecture/domain/evaluation/corrections, removal principle, and process isolation.
- **Last Status:** ✅ VERIFIED (100/100)
- **Verified On:** 2026-04-11
- **Test Specification:** architecture_system_overview_test.md