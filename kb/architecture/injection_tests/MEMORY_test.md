# Injection test — MEMORY.md

## Document under test
`kb/architecture/MEMORY.md`

## Why this test is critical
MEMORY.md is the first document loaded at every session start. If the agent cannot derive correct loading decisions from this document alone, every session starts with a broken context chain.

---

## Test questions

### Question 1
"I am starting a new session. A user has asked a question about the yelp dataset. In what order do I load documents, what is the mandatory pre-load token budget, and what happens if the corrections log is missing?"

Required concepts:
- tool_scoping.md is loaded first before the question arrives
- corrections/log.md last 10 entries is loaded second immediately after tool_scoping
- If corrections log is missing log the message and continue do not stop
- MEMORY.md is loaded third
- These three steps complete before the question is received
- Mandatory pre-load total is approximately 900 tokens covering only steps 1 through 3
- The yelp dataset schema load happens after the question arrives and is not part of the 900 token mandatory budget
- kb/domain/schemas.md for the yelp section is loaded after the question is received

Forbidden contradictions:
- Stating the mandatory pre-load is 1300 tokens
- Stating the yelp schema load is included in the mandatory pre-load budget
- Stating the loading order is optional

---

### Question 2
"A user asks a question that requires understanding how the agent's own memory system works. Which document do I load, what specific topics does it cover including how session transcripts are handled, and is it loaded on demand or always pre-loaded?"

Required concepts:
- Load claude_code_memory.md
- It contains Claude Code's three-layer memory architecture
- It explains how MEMORY.md index works
- It explains how topic files are loaded on demand
- It explains how session transcripts are searched but never pre-loaded
- It contains the autoDream consolidation pattern
- Load it on demand when the agent needs to understand its own memory architecture

Forbidden contradictions:
- Stating to load openai_agent_context.md for this question
- Stating to load tool_scoping.md for this question

---

### Question 3
"A user asks about why the agent uses separate database tools instead of one general query tool. Which document contains the answer, what does it say about the tool design philosophy, and is it already loaded or does it need to be loaded on demand?"

Required concepts:
- The answer is in tool_scoping.md
- tool_scoping.md explains the tool scoping philosophy that each tool has a single tight responsibility
- tool_scoping.md is mandatory and is already loaded as step 1 from session start
- tool_scoping.md is already in context when any question arrives

Forbidden contradictions:
- Stating tool_scoping.md is optional
- Stating tool_scoping.md needs to be loaded on demand for this question

---

### Question 4
"A user's question involves an ambiguous business term not recognisable from the schema. What do I load, is it mandatory or optional, what token budget does it use, what step number is it in the loading order, and what triggers its loading?"

Required concepts:
- Load kb/domain/business_terms.md
- It is optional not mandatory
- Token budget is approximately 300 tokens
- Load it when the question uses ambiguous business language
- It is step 7 in the loading order triggered by detected ambiguity in the question

Forbidden contradictions:
- Stating business_terms.md is mandatory
- Stating business_terms.md is part of the 900 token mandatory pre-load

---

### Question 5
"What is the total token budget for the mandatory pre-load, what is the per-document breakdown of that 900 tokens, what is the maximum optional budget, what does the optional budget cover, and what is the total maximum across a full session?"

Required concepts:
- Mandatory pre-load is approximately 900 tokens
- The 900 tokens breaks down as tool_scoping.md 300 plus corrections log 400 plus MEMORY.md 200
- Maximum optional budget is approximately 700 tokens
- Total maximum across a full session is approximately 1600 tokens
- The optional budget covers post-question loads not the mandatory pre-load

Forbidden contradictions:
- Stating mandatory pre-load is more than 900 tokens by including schema loads
- Stating total maximum is less than 1600 tokens
- Omitting the per-document breakdown of the 900-token mandatory total

---

## Test result

**Run timestamp:** 2026-04-11 17:46 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/architecture/MEMORY.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** I am starting a new session. A user has asked a question about the yelp dataset. In what order do I load documents, what is the mandatory pre-load token budget, and what happens if the corrections log is missing?

**Concepts found (8/8):**
  - [x] tool_scoping.md is loaded first before the question arrives
  - [x] corrections/log.md last 10 entries is loaded second immediately after tool_scoping
  - [x] If corrections log is missing log the message and continue do not stop
  - [x] MEMORY.md is loaded third
  - [x] These three steps complete before the question is received
  - [x] Mandatory pre-load total is approximately 900 tokens covering only steps 1 through 3
  - [x] The yelp dataset schema load happens after the question arrives and is not part of the 900 token mandatory budget
  - [x] kb/domain/schemas.md for the yelp section is loaded after the question is received

**Actual answer:**
Here's the breakdown based on the document provided:

**Document loading order:**

1.  `kb/architecture/tool_scoping.md`
2.  `kb/corrections/log.md` (last 10 entries)
3.  `kb/architecture/MEMORY.md`
4.  Receive the question.
5.  Identify which dataset(s) are involved.
6.  Load `kb/domain/schemas.md` for those datasets.
7.  If ambiguous business language detected, load `kb/domain/business_terms.md`.
8.  Answer the question

**Mandatory pre-load token budget:** ~900 tokens.

**What happens if the corrections log is missing:** Log the message "corrections log not yet created", continue, do not stop.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, resulting in a perfect score.

---

### Question 2 — PASS (100/100)

**Question:** A user asks a question that requires understanding how the agent's own memory system works. Which document do I load, what specific topics does it cover including how session transcripts are handled, and is it loaded on demand or always pre-loaded?

**Concepts found (7/7):**
  - [x] Load claude_code_memory.md
  - [x] It contains Claude Code's three-layer memory architecture
  - [x] It explains how MEMORY.md index works
  - [x] It explains how topic files are loaded on demand
  - [x] It explains how session transcripts are searched but never pre-loaded
  - [x] It contains the autoDream consolidation pattern
  - [x] Load it on demand when the agent needs to understand its own memory architecture

**Actual answer:**
Based on the provided document:

You should load `claude_code_memory.md`.

It covers Claude Code's three-layer memory architecture, including how the agent's own context loading and memory system works. Specifically, it details:

1.  MEMORY.md index (a small file that lists all topic files with one-sentence descriptions).
2.  Topic files loaded on demand when relevant to the current question.
3.  Session transcripts searched but never pre-loaded.

It also covers the autoDream consolidation pattern.

This document is loaded "on demand".

**Grader reasoning:** The answer includes all required concepts and no forbidden contradictions, thus earning a score of 100.

---

### Question 3 — PASS (100/100)

**Question:** A user asks about why the agent uses separate database tools instead of one general query tool. Which document contains the answer, what does it say about the tool design philosophy, and is it already loaded or does it need to be loaded on demand?

**Concepts found (4/4):**
  - [x] The answer is in tool_scoping.md
  - [x] tool_scoping.md explains the tool scoping philosophy that each tool has a single tight responsibility
  - [x] tool_scoping.md is mandatory and is already loaded as step 1 from session start
  - [x] tool_scoping.md is already in context when any question arrives

**Actual answer:**
The document that contains the answer is tool_scoping.md. It says the tool scoping philosophy is that each tool has a single tight responsibility — one tool, one database type, one query dialect. A tool that does one thing precisely is more reliable than a tool doing multiple things loosely. This document is already loaded.

**Grader reasoning:** All required concepts are present and there are no contradictions.

---

### Question 4 — PASS (100/100)

**Question:** A user's question involves an ambiguous business term not recognisable from the schema. What do I load, is it mandatory or optional, what token budget does it use, what step number is it in the loading order, and what triggers its loading?

**Concepts found (5/5):**
  - [x] Load kb/domain/business_terms.md
  - [x] It is optional not mandatory
  - [x] Token budget is approximately 300 tokens
  - [x] Load it when the question uses ambiguous business language
  - [x] It is step 7 in the loading order triggered by detected ambiguity in the question

**Actual answer:**
Based on the document:

*   **What to load:** `kb/domain/business_terms.md`
*   **Mandatory or optional:** Optional
*   **Token budget:** ~300 tokens
*   **Step number in loading order:** Step 7
*   **Trigger for loading:** Ambiguous business language detected that is not resolvable from the schema.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, resulting in a perfect score.

---

### Question 5 — PASS (100/100)

**Question:** What is the total token budget for the mandatory pre-load, what is the per-document breakdown of that 900 tokens, what is the maximum optional budget, what does the optional budget cover, and what is the total maximum across a full session?

**Concepts found (5/5):**
  - [x] Mandatory pre-load is approximately 900 tokens
  - [x] The 900 tokens breaks down as tool_scoping.md 300 plus corrections log 400 plus MEMORY.md 200
  - [x] Maximum optional budget is approximately 700 tokens
  - [x] Total maximum across a full session is approximately 1600 tokens
  - [x] The optional budget covers post-question loads not the mandatory pre-load

**Actual answer:**
Based on the provided document:

*   The total token budget for the mandatory pre-load is ~900 tokens.
*   The per-document breakdown of the 900 tokens is:
    *   tool_scoping.md = 300 tokens
    *   corrections/log.md last 10 entries = 400 tokens
    *   MEMORY.md = 200 tokens
*   The maximum optional budget is ~700 tokens.
*   The optional budget covers schemas and business\_terms combined.
*   The total maximum across a full session is ~1,600 tokens.

**Grader reasoning:** All required concepts are present, and no forbidden contradictions are present; the answer receives a perfect score.

---
