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

**Run timestamp:** 2026-04-11 16:41 UTC
**Document:** claude_memory
### Q1: 100/100
**Concepts found:**
  - [x] MEMORY.md is a small index file not a knowledge document
  - [x] It lists every other KB document by name with a one-sentence description
  - [x] The agent reads MEMORY.md first at session start
  - [x] MEMORY.md is approximately 200 tokens
  - [x] Growing MEMORY.md beyond 200 tokens defeats its purpose as an index
**Concepts missing:**
**Actual answer:**
Based on the document, MEMORY.md serves as the **Index Layer** in Claude Code's three-layer memory architecture with the following purpose and limits:

## Purpose of MEMORY.md:
- **Entry point for context loading** - acts as a lightweight pointer index
- **Lists every other KB document by name with a one-sentence description** 
- **Decision-making tool** - the agent reads MEMORY.md first at session start to decide which topic files to load next
- Functions like a **table of contents** - pointing to topic files rather than containing content itself

## Token Limit:
- **~200 tokens (strict cap)**
- The document explicitly states that "Growing it beyond this defeats its purpose as an index"
- Each entry is kept to approximately ~150 characters per entry to maintain the lightweight nature

The key insight is that MEMORY.md treats memory as an external system rather than part of the context window, helping solve "context entropy" by providing efficient navigation to relevant knowledge without bloating the context.
**Grader reasoning:** All five required concepts are clearly present in the answer and no forbidden contradictions exist.
---
### Q2: 100/100
**Concepts found:**
  - [x] Session transcripts are logs of past agent runs
  - [x] They record queries, tools, and results
  - [x] They are never pre-loaded into context
  - [x] The agent searches them only on demand
  - [x] Context window budget management in QueryEngine.ts enforces this
**Concepts missing:**
**Actual answer:**
Based on the document, session transcripts in Claude Code's memory system are:

**What they are:**
- Located in `.claude/sessions/`
- Searchable records of past interactions
- Logs of past agent runs that record exactly which queries were asked, which tools were called, and what results came back

**Why they are never pre-loaded:**
- **Cost Logic**: Searching is cheap, while pre-loading is expensive
- **Context Rule**: Session transcripts are never pre-loaded into context to prevent context window bloat by avoiding unnecessary injections of historical data
- **When loaded**: The agent searches them only when a new question closely resembles a past one (on-demand basis)
- **Enforcement**: `src/QueryEngine.ts` enforces this never-pre-load discipline

This design prevents "context entropy" by keeping the context window clean while still allowing access to historical information when specifically needed through search rather than automatic loading.
**Grader reasoning:** All five required concepts are clearly present in the answer and no forbidden contradictions exist.
---