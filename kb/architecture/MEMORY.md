# Architecture Knowledge Base — Index

## What this is

This is the index of the Oracle Forge architecture knowledge base. Load this document first at every session start. It tells the agent what architecture documents exist and what each one contains. Use it to decide which documents to load next based on the question being asked.

## Document registry

### tool_scoping.md

**Contains:** The exact database-to-tool mapping for all four DAB engine types (PostgreSQL, MongoDB, SQLite, DuckDB). Which MCP tool to call for each engine. Which query dialect to use per engine. The tool scoping philosophy: each tool has a single tight responsibility — one tool, one database type, one query dialect. A tool that does one thing precisely is more reliable than a tool doing multiple things loosely. This is why the Oracle Forge agent uses separate database tools instead of one general query tool. Also contains the zero-row rule and the cross-database join pattern.
**Already loaded:** Yes. tool_scoping.md is mandatory step 1 and is already in context from session start when any question arrives.
**Token budget:** ~300 tokens.

### corrections/log.md

**Contains:** The running structured log of agent failures. Entry format: `[query that failed] → [what was wrong] → [correct approach]`. The agent reads only the last 10 entries — not all entries.
**If missing:** Log the message "corrections log not yet created" and continue. Do not stop.
**Already loaded:** Yes. Mandatory step 2, always in context from session start.
**Token budget:** ~400 tokens (last 10 entries only).

### claude_code_memory.md

**Contains:** Claude Code's three-layer memory architecture — this is how the agent's own context loading and memory system works. From the March 2026 source leak: (1) MEMORY.md index — a small file that lists all topic files with one-sentence descriptions, (2) topic files loaded on demand when relevant to the current question, (3) session transcripts searched but never pre-loaded. Also contains the autoDream consolidation pattern implemented in src/tasks/DreamTask/ and src/services/autoDream/ — a background process that runs after sessions end, consolidates learnings into topic files, and removes outdated entries. And the tool scoping philosophy: each tool has one tight responsibility.
**Load when:** The agent needs to understand its own context loading, its own memory architecture, or how its own memory system works. This is the document about the agent itself — not about external systems.
**Token budget:** ~380 tokens. On demand.

### openai_agent_context.md

**Contains:** OpenAI's six-layer context architecture for their internal data agent (January 2026). This is an external reference about how OpenAI built their system — it is NOT about the Oracle Forge agent's own memory or context loading. All six layers in order. What Codex Enrichment (Layer 3) is: a daily asynchronous background process where Codex crawls the codebase that generates each table and derives facts invisible in SQL metadata. How the learning memory (Layer 5) works. The closed-loop self-correction pattern. Three engineering lessons: tool consolidation, less prescriptive prompting, code reveals what metadata hides.
**Load when:** The agent needs to understand external context layering strategy or how to handle table ambiguity. Do NOT load this when the question is about the agent's own memory or context loading — use claude_code_memory.md for that.
**Token budget:** ~360 tokens. On demand.

### kb_v1_architecture.md

**Contains:** How the Oracle Forge KB is structured across four subdirectories (architecture, domain, evaluation, corrections). The Karpathy method discipline: removal not accumulation, every document must pass an injection test before the agent loads it. The injection test six-step protocol. The token budget rules for mandatory vs optional loading. Why MEMORY.md is capped at 200 tokens.
**Load when:** The agent needs to understand its own knowledge base structure.
**Token budget:** ~300 tokens. On demand.

### kb/domain/business_terms.md

**Contains:** Definitions of domain-specific terms not derivable from schema alone — what "churn" means, what "active customer" means, fiscal year boundaries, status code meanings.
**This document is optional, not mandatory.** It is step 7 in the context loading order. Load it only when the question uses ambiguous business language that is not resolvable from the schema.
**Token budget:** ~300 tokens. Optional, post-question, step 7 only.

## Context loading order — follow exactly

```
Step 1: Load kb/architecture/tool_scoping.md       [MANDATORY ~300 tok — before question]
Step 2: Load kb/corrections/log.md last 10 entries  [MANDATORY ~400 tok — before question]
         → If missing: log "corrections log not yet created", continue, do not stop
Step 3: Load kb/architecture/MEMORY.md              [MANDATORY ~200 tok — before question]
Step 4: Receive the question
Step 5: Identify which dataset(s) are involved
Step 6: Load kb/domain/schemas.md for those datasets [~400 tok per dataset — post-question]
Step 7: If ambiguous business language detected:
         load kb/domain/business_terms.md            [OPTIONAL ~300 tok — post-question]
         Step 7 is optional. Load only when ambiguity is detected.
Step 8: Answer the question
```

## Token budget

**Mandatory pre-load total: ~900 tokens.** Breakdown:

- Step 1 tool_scoping.md = 300 tokens
- Step 2 corrections/log.md last 10 entries = 400 tokens
- Step 3 MEMORY.md = 200 tokens

**Post-question optional maximum: ~700 tokens.** The optional budget covers post-question loads only — it is NOT part of the 900-token mandatory pre-load. It covers schemas and business_terms combined, not each separately.

**Total maximum across a full session: ~1,600 tokens.**

Schema loads and business_terms.md are NOT part of the 900-token mandatory pre-load. They are post-question and optional.

## What this does NOT cover

Domain schemas, join key formats, and unstructured field inventories are in kb/domain/. Agent failure corrections are in kb/corrections/. DAB benchmark scoring and evaluation methodology are in kb/evaluation/.

---

Token count: ~330 tokens
Last verified: 2026-04-11
