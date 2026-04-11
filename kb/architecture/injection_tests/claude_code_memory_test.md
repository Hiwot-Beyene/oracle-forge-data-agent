# Injection test — claude_code_memory.md

## Document under test
`kb/architecture/claude_code_memory.md`

## Why this test is critical
claude_code_memory.md describes the agent's own memory architecture. If the agent cannot derive correct memory loading decisions from this document alone, it will mismanage its own context across sessions.

---

## Test questions

### Question 1
"What are the three memory layers in Claude Code's memory architecture, what does each one do, and why are session transcripts never pre-loaded?"

Required concepts:
- Layer 1 is MEMORY.md which is a small index file of approximately 200 tokens loaded first at session start
- MEMORY.md lists every other KB document by name with a one-sentence description
- Layer 2 is topic files of approximately 300 to 400 tokens each loaded on demand
- Topic files contain actual knowledge for specific subjects and are loaded only when relevant to the current question
- Layer 3 is session transcripts which are searched but never pre-loaded
- Searching transcripts is cheap but pre-loading them is expensive

Forbidden contradictions:
- Stating that session transcripts are pre-loaded
- Stating that all topic files are loaded upfront
- Stating that MEMORY.md is a knowledge document rather than an index

---

### Question 2
"What is the autoDream consolidation pattern, when does it run, what does it do to topic files after consolidation, and what are the three trigger thresholds?"

Required concepts:
- autoDream is a background process that runs after sessions end not during sessions
- It consolidates learnings from the session back into topic files
- It removes old superseded information from topic files
- After consolidation the topic file is smaller and more precise than before
- User corrects the same pattern 3 or more times triggers write to MEMORY.md
- Agent successfully uses a pattern 5 or more times triggers promote to a topic file
- Topic file grows beyond 500 words triggers split into subtopics

Forbidden contradictions:
- Stating that autoDream runs during sessions
- Stating that autoDream makes topic files larger

---

### Question 3
"What is the Oracle Forge equivalent of autoDream and how does it work?"

Required concepts:
- After agent runs review kb/corrections/log.md
- Absorb verified fixes into the relevant kb/domain/ documents
- Remove absorbed entries from the corrections log
- This is the manual Oracle Forge equivalent of the autoDream loop

Forbidden contradictions:
- Stating that Oracle Forge uses automated autoDream
- Stating that corrections are kept in the log permanently

---

### Question 4
"Why is MEMORY.md capped at approximately 200 tokens and what happens if it grows beyond that?"

Required concepts:
- MEMORY.md is approximately 200 tokens and this limit is deliberate
- Growing MEMORY.md beyond 200 tokens defeats its purpose as an index
- It becomes a topic document masquerading as an index
- It wastes mandatory context budget before any question-specific loading begins

Forbidden contradictions:
- Stating that MEMORY.md should contain detailed knowledge
- Stating that MEMORY.md has no token limit

---

### Question 5
"What is the tool scoping philosophy described in this document and why does the Oracle Forge agent use separate tools per database type?"

Required concepts:
- Each tool has a single tight responsibility with one tool one responsibility one domain boundary
- A tool that does one thing precisely is more reliable than a tool doing multiple things loosely
- Tight domain boundaries make failures diagnosable and recoverable
- This is why the Oracle Forge agent uses separate tools per database type not a single query database tool

Forbidden contradictions:
- Stating that one general tool is preferred
- Stating that tool overlap is acceptable

## Test result

**Run timestamp:** 2026-04-11 17:47 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/architecture/claude_code_memory.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** What are the three memory layers in Claude Code's memory architecture, what does each one do, and why are session transcripts never pre-loaded?

**Concepts found (6/6):**
  - [x] Layer 1 is MEMORY.md which is a small index file of approximately 200 tokens loaded first at session start
  - [x] MEMORY.md lists every other KB document by name with a one-sentence description
  - [x] Layer 2 is topic files of approximately 300 to 400 tokens each loaded on demand
  - [x] Topic files contain actual knowledge for specific subjects and are loaded only when relevant to the current question
  - [x] Layer 3 is session transcripts which are searched but never pre-loaded
  - [x] Searching transcripts is cheap but pre-loading them is expensive

**Actual answer:**
The three memory layers in Claude Code's memory architecture are:

1.  **MEMORY.md index:** A small index file (~200 tokens) that lists every other KB document by name with a one-sentence description of what that document contains. The agent reads MEMORY.md first at session start to decide which topic files to load.
2.  **Topic files:** These contain the actual knowledge for a specific subject and are loaded only when the MEMORY.md index indicates they are relevant to the current question.
3.  **Session transcripts:** Logs of past agent runs, including queries asked, tools called, results, and final answers.

Session transcripts are never pre-loaded into context because pre-loading is expensive, and most sessions do not need them. The agent searches transcripts only when a new question closely resembles a past one, because searching is cheap, while pre-loading is expensive.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found.

---

### Question 2 — PASS (100/100)

**Question:** What is the autoDream consolidation pattern, when does it run, what does it do to topic files after consolidation, and what are the three trigger thresholds?

**Concepts found (7/7):**
  - [x] autoDream is a background process that runs after sessions end not during sessions
  - [x] It consolidates learnings from the session back into topic files
  - [x] It removes old superseded information from topic files
  - [x] After consolidation the topic file is smaller and more precise than before
  - [x] User corrects the same pattern 3 or more times triggers write to MEMORY.md
  - [x] Agent successfully uses a pattern 5 or more times triggers promote to a topic file
  - [x] Topic file grows beyond 500 words triggers split into subtopics

**Actual answer:**
The autoDream consolidation pattern is a background process that runs after sessions end. It consolidates learnings from the session back into the relevant topic files and removes old, superseded information from topic files. After consolidation, the topic file is smaller and more precise than before the session.

The three consolidation trigger thresholds are:

*   User corrects the same pattern 3+ times → write to MEMORY.md
*   Agent successfully uses a pattern 5+ times → promote to a topic file
*   Topic file grows beyond 500 words → split into subtopics

**Grader reasoning:** All required concepts are present and no forbidden contradictions are present.

---

### Question 3 — PASS (100/100)

**Question:** What is the Oracle Forge equivalent of autoDream and how does it work?

**Concepts found (4/4):**
  - [x] After agent runs review kb/corrections/log.md
  - [x] Absorb verified fixes into the relevant kb/domain/ documents
  - [x] Remove absorbed entries from the corrections log
  - [x] This is the manual Oracle Forge equivalent of the autoDream loop

**Actual answer:**
The Oracle Forge equivalent of autoDream is a manual process of absorbing verified corrections from `kb/corrections/log.md` into the relevant `kb/domain/` documents after each agent run, and then removing the absorbed entries from the corrections log.

**Grader reasoning:** All required concepts are correctly identified in the answer, and there are no forbidden contradictions.

---

### Question 4 — PASS (100/100)

**Question:** Why is MEMORY.md capped at approximately 200 tokens and what happens if it grows beyond that?

**Concepts found (4/4):**
  - [x] MEMORY.md is approximately 200 tokens and this limit is deliberate
  - [x] Growing MEMORY.md beyond 200 tokens defeats its purpose as an index
  - [x] It becomes a topic document masquerading as an index
  - [x] It wastes mandatory context budget before any question-specific loading begins

**Actual answer:**
MEMORY.md is capped at approximately 200 tokens because growing beyond that defeats its purpose as an index. It becomes a topic document masquerading as an index and wastes mandatory context budget before any question-specific loading begins.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, so the score is 100.

---

### Question 5 — PASS (100/100)

**Question:** What is the tool scoping philosophy described in this document and why does the Oracle Forge agent use separate tools per database type?

**Concepts found (4/4):**
  - [x] Each tool has a single tight responsibility with one tool one responsibility one domain boundary
  - [x] A tool that does one thing precisely is more reliable than a tool doing multiple things loosely
  - [x] Tight domain boundaries make failures diagnosable and recoverable
  - [x] This is why the Oracle Forge agent uses separate tools per database type not a single query database tool

**Actual answer:**
The tool scoping philosophy is that each tool has a single tight responsibility - one tool, one responsibility, one domain boundary. A tool that does one thing precisely is more reliable than a tool doing multiple things loosely. Tight domain boundaries make failures diagnosable and recoverable. This is why the Oracle Forge agent uses separate tools per database type, instead of a single "query database" tool that switches internally.

**Grader reasoning:** All required concepts are clearly present and no forbidden contradictions are present.

---
