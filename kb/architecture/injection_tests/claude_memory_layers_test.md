# Injection test — claude_memory_layers.md

## Document under test
`kb/architecture/claude_memory_layers.md`

## Test questions

### Question 1
"What is the purpose of MEMORY.md in Claude Code's memory system and what token limit applies to it?"

Required concepts:
- MEMORY.md is a small index file not a knowledge document
- It lists every other KB document by name with a one-sentence description
- The agent reads MEMORY.md first at session start
- MEMORY.md is approximately 200 tokens
- Growing MEMORY.md beyond 200 tokens defeats its purpose as an index

Forbidden contradictions:
- Stating MEMORY.md contains the actual knowledge content

---

### Question 2
"What are session transcripts in Claude Code's memory system and why are they never pre-loaded?"

Required concepts:
- Session transcripts are logs of past agent runs
- They record queries, tools, and results
- They are never pre-loaded into context
- The agent searches them only on demand
- Context window budget management in QueryEngine.ts enforces this

Forbidden contradictions:
- Stating session transcripts are pre-loaded at session start

---

## Test result

**Run timestamp:** 2026-04-11 14:44 UTC
**Document:** claude_memory
### Q1: 85/100
**Actual:** Based on the document, MEMORY.md serves as the **Index Layer** (Layer 1) in Claude Code's three-layer memory architecture.

**Purpose of MEMORY.md:**
- Acts as an entry point for context loading
- Functions as a lightweight pointer index (~150 characters per entry)
- Works like a table of contents that points to topic files rather than containing content itself
- Provides mandatory pre-load information at every session start

**Token limit:**
MEMORY.md has a **strict cap of ~200 tokens**.

This token budget constraint is part of the system's approach to solving "context entropy" by treating memory as an external system rather than part of the context window, allowing the agent to maintain organized access to information without overwhelming the context with unnecessary details.
---
### Q2: 75/100
**Actual:** Based on the document, session transcripts in Claude Code's memory system are:

**What they are:**
- **Layer 3** of the three-layer memory architecture
- Located in `.claude/sessions/`
- Searchable records of past interactions
- Part of the "interaction memory" component

**Why they are never pre-loaded:**
Session transcripts are never pre-loaded to prevent "context entropy" - the tendency for long agent sessions to become confused. The document indicates that:

1. They are loaded only "when needed" - the agent searches them on-demand rather than loading them at session start
2. There is strict "never-pre-load discipline for transcripts" enforced by `src/QueryEngine.ts`
3. This is part of treating memory as an "external system" rather than part of the context window

This approach preserves the context window for active work while still allowing access to historical interaction data when specifically required, preventing the confusion that comes from having too much historical context loaded simultaneously.
---