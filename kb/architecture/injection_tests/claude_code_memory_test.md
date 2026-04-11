# Injection test — claude_code_memory.md

## Document under test
`kb/architecture/claude_code_memory.md`

## Why this test is critical
This document is the conceptual model for how the Oracle Forge agent structures its own memory. If the agent cannot correctly describe the three layers and autoDream from this document alone, it will make incorrect decisions about what to load, when to load it, and what to consolidate.

---

## Test questions

### Question 1
"What is the purpose of MEMORY.md in Claude Code's memory system and what token limit applies to it?"

Required concepts:
- MEMORY.md is a small index file not a knowledge document
- It lists every other KB document by name with a one-sentence description
- The agent reads MEMORY.md first at session start
- MEMORY.md is used to decide which topic files to load next
- MEMORY.md is approximately 200 tokens
- Growing MEMORY.md beyond 200 tokens defeats its purpose as an index

Forbidden contradictions:
- Stating MEMORY.md contains the actual knowledge content
- Stating MEMORY.md is loaded on demand not at session start

---

### Question 2
"What is autoDream, when does it run, and what does it do to topic files?"

Required concepts:
- autoDream is a background process
- It runs after sessions end not during sessions
- It reviews what was learned during the session
- It consolidates learnings back into the relevant topic files
- It removes old superseded information from topic files
- The topic file after consolidation is smaller and more precise than before
- It is implemented in src/tasks/DreamTask and src/services/autoDream in the Claude Code source
- For Oracle Forge it means reviewing the corrections log after agent runs and absorbing verified fixes into domain documents

Forbidden contradictions:
- Stating autoDream runs during the session before the agent answers
- Stating autoDream adds content to topic files without removing outdated information

---

### Question 3
"Why does Claude Code use 40 or more tools each with tight domain boundaries instead of fewer general-purpose tools?"

Required concepts:
- Each tool has a single tight responsibility
- A tool with one precise purpose is more reliable than a tool doing multiple things
- When a tool fails the agent knows exactly which tool failed and why
- Tight domain boundaries make failures diagnosable
- Tight domain boundaries make failures recoverable
- This is why Oracle Forge uses separate tools per database type rather than one general query tool

Forbidden contradictions:
- Stating fewer tools are better for reliability
- Stating tool boundaries do not affect failure diagnosis

---

### Question 4
"What are session transcripts in Claude Code's memory system, how are they accessed, and why are they never pre-loaded?"

Required concepts:
- Session transcripts are logs of past agent runs
- They record which queries were asked and what tools were called and what results came back
- They are never pre-loaded into context
- The agent searches them only when a new question closely resembles a past one
- Searching is cheap and pre-loading is expensive
- Context window budget management in QueryEngine.ts enforces the never-pre-load discipline

Forbidden contradictions:
- Stating session transcripts are always pre-loaded at session start
- Stating session transcripts replace topic files

---

## Test result

**Run timestamp:** 2026-04-11 12:30 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/claude_code_memory.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** What is the purpose of MEMORY.md in Claude Code's memory system and what token limit applies to it?

**Concepts found (6/6):**
  - [x] MEMORY.md is a small index file not a knowledge document
  - [x] It lists every other KB document by name with a one-sentence description
  - [x] The agent reads MEMORY.md first at session start
  - [x] MEMORY.md is used to decide which topic files to load next
  - [x] MEMORY.md is approximately 200 tokens
  - [x] Growing MEMORY.md beyond 200 tokens defeats its purpose as an index

**Actual answer:**
Based on the document, MEMORY.md serves as a small index file in Claude Code's Layer 1 memory system. Its purpose is to:

1. **Function as an index** - It lists every other knowledge base document by name with a one-sentence description
2. **Enable efficient knowledge discovery** - The agent reads this file first at session start to know what knowledge is available
3. **Guide selective loading** - It helps the agent decide what to load next based on relevance

The token limit that applies to MEMORY.md is **~200 tokens maximum**. The document emphasizes that it is "never more than ~200 tokens" and states that "growing it beyond this defeats its purpose as an index."

The document describes MEMORY.md as functioning "like a table of contents — pointing to topic files, not containing content itself." It's explicitly noted that MEMORY.md is "not a knowledge document itself" but rather an index that enables the agent to selectively load the appropriate Layer 2 topic files (~300-400 tokens each) on demand.

**Grader reasoning:** All six required concepts are clearly present and no forbidden contradictions were found.

---

### Question 2 — PASS (100/100)

**Question:** What is autoDream, when does it run, and what does it do to topic files?

**Concepts found (8/8):**
  - [x] autoDream is a background process
  - [x] It runs after sessions end not during sessions
  - [x] It reviews what was learned during the session
  - [x] It consolidates learnings back into the relevant topic files
  - [x] It removes old superseded information from topic files
  - [x] The topic file after consolidation is smaller and more precise than before
  - [x] It is implemented in src/tasks/DreamTask and src/services/autoDream in the Claude Code source
  - [x] For Oracle Forge it means reviewing the corrections log after agent runs and absorbing verified fixes into domain documents

**Actual answer:**
Based on the document, autoDream is a background process with the following characteristics:

**What it is:** autoDream is a consolidation process implemented in the `src/tasks/DreamTask/` and `src/services/autoDream/` directories of the Claude Code codebase.

**When it runs:** autoDream runs after sessions end — not during sessions. It operates as a background process.

**What it does to topic files:** autoDream reviews what was learned during the session, including:
- Corrections made
- Successful query patterns  
- New business term definitions discovered

It then consolidates these learnings back into the relevant topic files. Importantly, old, superseded information is removed during this process. The result is that topic files after consolidation are smaller and more precise than before the session.

This consolidation mechanism prevents the knowledge base from growing into noise. For Oracle Forge specifically, this means reviewing the corrections log after agent runs, absorbing verified fixes into domain documents, and then removing those entries from the corrections log once they have been absorbed.

**Grader reasoning:** All eight required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---

### Question 3 — PASS (100/100)

**Question:** Why does Claude Code use 40 or more tools each with tight domain boundaries instead of fewer general-purpose tools?

**Concepts found (6/6):**
  - [x] Each tool has a single tight responsibility
  - [x] A tool with one precise purpose is more reliable than a tool doing multiple things
  - [x] When a tool fails the agent knows exactly which tool failed and why
  - [x] Tight domain boundaries make failures diagnosable
  - [x] Tight domain boundaries make failures recoverable
  - [x] This is why Oracle Forge uses separate tools per database type rather than one general query tool

**Actual answer:**
Based on the document, Claude Code uses 40+ tools with tight domain boundaries because of their tool scoping philosophy that "each tool has a single tight responsibility." The document states this as "the rule — one tool, one responsibility, a named domain boundary."

The specific reasons given are:

1. **Reliability**: "A tool that does one thing precisely is more reliable than a tool that tries to do three things loosely."

2. **Diagnosable failures**: "Tight domain boundaries make failures diagnosable — the agent knows exactly which tool failed."

3. **Recoverable failures**: "Tight domain boundaries make failures recoverable — the agent knows exactly what to fix."

When a tool fails, the agent has precise knowledge of which specific tool failed and why, rather than having to debug a complex general-purpose tool where the failure point could be unclear.

The document provides a concrete example: "This is directly why the Oracle Forge agent uses separate tools per database type rather than a single 'query database' tool that switches internally."

**Grader reasoning:** All six required concepts are clearly present in the actual answer with accurate quotes and explanations, and no forbidden contradictions were found.

---

### Question 4 — PASS (100/100)

**Question:** What are session transcripts in Claude Code's memory system, how are they accessed, and why are they never pre-loaded?

**Concepts found (6/6):**
  - [x] Session transcripts are logs of past agent runs
  - [x] They record which queries were asked and what tools were called and what results came back
  - [x] They are never pre-loaded into context
  - [x] The agent searches them only when a new question closely resembles a past one
  - [x] Searching is cheap and pre-loading is expensive
  - [x] Context window budget management in QueryEngine.ts enforces the never-pre-load discipline

**Actual answer:**
Based on the document, session transcripts in Claude Code's memory system are:

**What they are:** Session transcripts are logs of past agent runs that record which queries were asked, what tools were called, what results came back, and what the final answer was.

**How they are accessed:** They are searched only when a new question closely resembles a past one. The agent never pre-loads them into context but searches them on demand.

**Why they are never pre-loaded:** The document states that "Searching is cheap; pre-loading is expensive." The context window budget management in `src/QueryEngine.ts` enforces this "never-pre-load discipline" for session transcripts. This approach preserves the limited context window space for more immediately relevant information like the MEMORY.md index and on-demand topic files, while still allowing access to historical information when needed through search.

Session transcripts constitute Layer 3 of Claude Code's three-layer memory architecture, with the key principle being that they are accessed reactively through search rather than proactively loaded into context.

**Grader reasoning:** All six required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---
