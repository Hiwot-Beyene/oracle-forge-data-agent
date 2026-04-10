# kb/architecture/kb_v1_architecture.md

# KB v1 — Architecture Knowledge Base

_The Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.1 | Updated with team-verified documents and architecture diagram_

---

## DIRECTORY STRUCTURE

```
kb/
├── architecture/
│   ├── README.md                    # Index of all architecture documents
│   ├── CHANGELOG.md                 # Version tracking (required for rubric)
│   ├── claude_memory_layers.md      # The 3-layer MEMORY.md pattern
│   ├── claude_tool_scoping.md       # 40+ tools with tight boundaries
│   ├── claude_autodream.md          # Memory consolidation pattern
│   ├── openai_six_layers.md         # Context architecture from OpenAI
│   ├── openai_table_enrichment.md   # Codex-powered schema resolution
│   └── injection_tests/
│       ├── test_memory_layers.txt   # Test queries + expected answers
│       ├── test_tool_scoping.txt
│       └── test_six_layers.txt
```

---

## README — Document Index

| File                         | Content                                     |
| ---------------------------- | ------------------------------------------- |
| `claude_memory_layers.md`    | Three-layer MEMORY.md pattern               |
| `claude_tool_scoping.md`     | 40+ tools with tight boundaries             |
| `claude_autodream.md`        | Background memory consolidation             |
| `openai_six_layers.md`       | Context architecture (schema → preferences) |
| `openai_table_enrichment.md` | Codex-powered schema enrichment             |

**Usage in Agent:** All documents in this directory are injected into the agent's
system prompt at session start via `agent/context_builder.py`. The agent does not
need to request them — they are part of its baseline knowledge.

**Verification:** Every document has passed an injection test (see `injection_tests/`
directory). Protocol: (1) fresh LLM session, (2) document loaded as only context,
(3) specific question asked, (4) answer matches expected.

**Maintenance:** Updates by Intelligence Officers only. Mob session review required
before modification. All changes recorded in `CHANGELOG.md`.

---

## SECTION A: The Oracle Forge Architecture — System Overview

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

---

## SECTION B: Claude Code — Three-Layer Memory Architecture

_Source: Claude Code npm leak, March 31 2026 — 512,000 lines TypeScript_

### Core Insight

Claude Code solves "context entropy" — the tendency for long agent sessions to become
confused — through a three-layer memory architecture that treats memory as an
**external system**, not part of the context window.

### Layer 1 — MEMORY.md (Index Layer)

- **Location:** Project root
- **Purpose:** Entry point for context loading — lightweight pointer index
  (~150 chars per entry)
- **Content:** High-level project structure, key conventions, pointers to topic files
- **When loaded:** At every session start — perpetually in context
- **Never stores actual information — only pointers**
- **Read-before-write discipline:** agent reads current MEMORY.md before any
  update to prevent overwrite
- **Self-healing:** if the agent learns a prior assumption was wrong, it rewrites
  the relevant memory file so the correction persists across sessions

### Layer 2 — Topic Files (Detailed Knowledge)

- **Location:** `.claude/memory/` directory
- **Purpose:** Deep knowledge on specific domains
- **Content:** Detailed instructions for testing, deployment, database schema, etc.
- **When loaded:** On-demand when agent encounters relevant task
- **Trigger:** Keyword matching or explicit agent request
- Only files **relevant to the current task** are loaded — not a full dump

### Layer 3 — Session Transcripts (Interaction Memory)

- **Location:** `.claude/sessions/`
- **Purpose:** Searchable record of past interactions
- **Content:** Full conversation history, tool calls, outputs, user corrections
- **When loaded:** Agent searches transcripts when uncertain or user references
  past work
- **Search method:** Embedding-based semantic search

### Application to Oracle Forge

| Claude Code Pattern | DAB Agent Implementation                                           |
| ------------------- | ------------------------------------------------------------------ |
| MEMORY.md index     | AGENT.md — DB connection summary and KB pointers                   |
| Topic files         | `kb/domain/` directory with schema details per dataset             |
| Session transcripts | `kb/corrections/kb_v3_corrections.md` with structured failure logs |

### Key Insight

The three layers prevent context window bloat. The agent navigates from
index → topic → transcript only when needed. Apply the same principle:
do not inject all KB documents into every query — inject only what that
query needs.

---

## SECTION C: Claude Code — Tool Scoping Philosophy

_Source: Claude Code npm leak, March 31 2026_

### The Pattern

Claude Code exposes 40+ tools to the agent, but each tool has:

- **Tight domain boundaries** — one tool does one thing well
- **Explicit preconditions** — what must be true before calling
- **Clear error semantics** — what failure means and how to recover

### Tool Categories

1. **File System:** `read_file`, `write_file`, `list_directory`, `search_content`
2. **Code Execution:** `run_terminal`, `run_python`, `run_tests`
3. **Git:** `git_status`, `git_diff`, `git_commit`, `git_branch`
4. **External:** `web_search`, `web_fetch`, `api_call`

### The "Tool First" Design Rule

Tools are designed **before** the agent prompt. The prompt references tools by
name and purpose. The agent never generates raw shell commands — it selects tools
from the manifest.

### Application to Oracle Forge

| Claude Code Tool | DAB Agent Equivalent                         |
| ---------------- | -------------------------------------------- |
| `run_terminal`   | MCP Toolbox PostgreSQL executor              |
| `search_content` | Schema introspection via MCP                 |
| `git_diff`       | Query trace comparison in evaluation harness |

### Required MCP Tools for DAB

1. `query_postgres_[dataset]` — one tool per PostgreSQL database
2. `query_mongo_[collection]` — one tool per MongoDB collection
3. `extract_structured_text` — unstructured field parser (Week 3 module)
4. `resolve_join_key` — format normalizer for cross-DB joins

### Key Insight

**Do not give the agent raw SQL execution. Give it named tools.** This enables:

- Query tracing (evaluation harness requirement)
- Automatic dialect translation (PostgreSQL vs. SQLite vs. DuckDB)
- Failure recovery (tool returns structured error, agent can retry)

---

## SECTION D: Claude Code — autoDream Memory Consolidation

_Source: Claude Code npm leak, March 31 2026_

### The Pattern

autoDream is an asynchronous background process that:

1. **Orient** — Read MEMORY.md to understand current state
2. **Gather** — Find new signals from daily logs and session transcripts
3. **Consolidate** — Merge disparate observations, remove contradictions,
   convert vague insights to concrete facts
4. **Prune** — Keep context efficient by removing stale or redundant entries

### Consolidation Triggers (from source code)

- User corrects same pattern 3+ times → Write to MEMORY.md
- Agent successfully uses a pattern 5+ times → Promote to topic file
- Topic file grows beyond 500 words → Split into subtopics

### The "Dream" Metaphor

The system processes memory **offline**, not during active sessions. This prevents
the consolidation work from consuming the agent's context window or slowing
response time.

### Application to Oracle Forge

| autoDream Function | DAB Agent Implementation                                   |
| ------------------ | ---------------------------------------------------------- |
| Pattern detection  | Manual review of `kb/corrections/` after each test run     |
| Consolidation      | IOs update `kb/domain/` based on observed failure patterns |
| Pruning            | Weekly CHANGELOG.md review to remove obsolete entries      |

### Key Insight

The value is not the automation — it is the **structured format**. Every correction
follows: `[Query] → [What failed] → [Correct approach]`. This format makes the
knowledge injectable into future LLM contexts. KB v3 is a manual autoDream.

---

## SECTION E: OpenAI Data Agent — Six-Layer Context Architecture

_Source: OpenAI Engineering Blog, January 29 2026_
_Scale: 600+ PB, 70,000 datasets, 3,500+ internal users_

### The Core Problem

Finding the right table across 70,000 datasets is the hardest sub-problem.
Many tables look similar on the surface but differ critically — one includes
only logged-in users, another includes logged-out users too. Context engineering
is the bottleneck, not query generation.

### The Six Layers (cumulative — each builds on the previous)

| Layer | Name                        | What It Provides                                                                                                                         |
| ----- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | **Raw Schema**              | Table names, column names, data types via `INFORMATION_SCHEMA`. No business meaning — only structure                                     |
| 2     | **Table Relationships**     | Foreign key relationships, join paths inferred from schema constraints and query history                                                 |
| 3     | **Column Semantics**        | What each column means in business terms. Example: `status_code = 3` means "active customer." Source: data dictionary, human annotation  |
| 4     | **Query Patterns**          | Common joins, aggregations, filters that work. Example: "Always filter `deleted_at IS NULL` before counting users." Source: log analysis |
| 5     | **Institutional Knowledge** | Domain-specific definitions not in schema. Example: "Churn = no purchase in 90 days." Source: business documentation                     |
| 6     | **User Preferences**        | Individual preferred aggregations, date ranges, output formats. Source: session history                                                  |

### Application to Oracle Forge

| OpenAI Layer        | DAB Agent Implementation                     |
| ------------------- | -------------------------------------------- |
| 1: Raw Schema       | MCP Toolbox introspection at startup         |
| 2: Relationships    | Foreign keys from `information_schema`       |
| 3: Column Semantics | `kb/domain/schema_descriptions.md`           |
| 4: Query Patterns   | `kb/domain/query_patterns.md`                |
| 5: Institutional    | `kb/domain/domain_terms.md`                  |
| 6: User Preferences | Future iteration — out of scope for Week 8-9 |

**Minimum viable for DAB:** Layers 1, 3, and 5 must demonstrably work.
Layer 3 (Column Semantics) is the hardest — document what `user_id` means
in PostgreSQL vs. `cust_id` in MongoDB **before** the agent runs its first query.

### Self-Correction Loop

- If intermediate result looks wrong (zero rows, unexpected nulls), agent
  diagnoses, adjusts, retries
- Does NOT surface the error to the user
- Carries learnings forward between steps
- Result: analysis time dropped from 22 minutes to 90 seconds with memory enabled

### Key Insight

**Layer 3 (Column Semantics) is the hardest sub-problem.** OpenAI explicitly calls
out table enrichment as the bottleneck. For DAB, this means documenting what
`user_id` means in PostgreSQL vs. `cust_id` in MongoDB before the agent runs
its first query.

---

## SECTION F: OpenAI Data Agent — Codex-Powered Table Enrichment

_Source: OpenAI Engineering Blog, January 29 2026_

### The Problem

Raw schema tells you: table `users`, column `status`, type `integer`.

It does **not** tell you:

- `status = 1` means "active"
- `status = 2` means "suspended"
- `status = 3` means "deleted" (but records remain for audit)

Without enrichment, the agent produces **syntactically correct but semantically
wrong** queries.

### The OpenAI Solution

A specialized Codex model (not the main agent LLM) runs daily as an async process:

1. **Scan** table and column names
2. **Generate** plausible business descriptions from pipeline code
3. **Present** descriptions to human data stewards for verification
4. **Store** verified descriptions in the enrichment layer

### The Closed-Loop Self-Correction Pattern

1. Agent runs query with current enrichment
2. User corrects output ("That's not what churn means here")
3. Correction flows to enrichment layer (not just session memory)
4. Next query uses corrected enrichment

### Oracle Forge Equivalent

We cannot run a daily Codex async pipeline in two weeks. Our equivalent:

- `schema_introspector` utility runs at **agent startup** (not daily async)
- Human-verified column semantics written manually into `kb/domain/schema_descriptions.md`
- Corrections flow to KB v3 and are injected on the next session

### Key Insight

**Table enrichment is the difference between a demo agent and a production agent.**
A demo agent assumes schema is self-documenting. A production agent knows that
`status = 2` means suspended and filters accordingly.

---

## SECTION G: Mapping to Oracle Forge — Minimum Required Implementation

| OpenAI Layer            | Oracle Forge Equivalent                              | File Location                         |
| ----------------------- | ---------------------------------------------------- | ------------------------------------- |
| Raw Schema              | MCP Toolbox introspection + `build_unified_schema()` | `utils/oracle_forge_utils.py`         |
| Column Semantics        | Schema descriptions + domain term glossary           | `kb/domain/schema_descriptions.md`    |
| Query Patterns          | Successful query log                                 | `kb/domain/query_patterns.md`         |
| Institutional Knowledge | Domain terms + join key glossary                     | `kb/domain/domain_terms.md`           |
| Learning Memory         | Corrections log                                      | `kb/corrections/kb_v3_corrections.md` |
| Runtime Context         | Direct DB query tools                                | `agent/tools.yaml` (MCP config)       |

---

## INJECTION TEST EVIDENCE
