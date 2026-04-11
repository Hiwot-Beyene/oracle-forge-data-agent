# Injection test — kb_v1_architecture.md

## Document under test
`kb/architecture/kb_v1_architecture.md`

## Why this test is critical
This document defines the rules governing the entire KB system. If the agent cannot derive the correct subdirectory for a given type of knowledge, it loads the wrong file and wastes context budget on irrelevant content.

---

## Test questions

### Question 1
"What are the four KB subdirectories in the Oracle Forge project and what type of information belongs in each one?"

Required concepts:
- kb/architecture/ contains documents about how the agent itself works including memory architecture and tool scoping rules
- kb/architecture/ documents change when the agent architecture changes not when datasets change
- kb/domain/ contains documents about the data the agent works with including schemas and join key formats and business term definitions
- kb/domain/ documents change when datasets are loaded or failure patterns reveal schema misunderstandings
- kb/evaluation/ contains documents about how the agent is scored and what the benchmark requires including DAB query format and pass at 1 scoring
- kb/corrections/ contains the running structured log of agent failures read at every session start
- kb/corrections/log.md is the self-learning loop written by Drivers after every observed failure

Forbidden contradictions:
- Stating agent architecture documents belong in kb/domain/
- Stating business term definitions belong in kb/architecture/

---

### Question 2
"An Intelligence Officer wants to add a new document to the KB. What are the exact six steps of the injection test protocol they must follow before committing?"

Required concepts:
- Step 1 copy the full text of the document
- Step 2 open a completely fresh LLM session with no other context and no system prompt
- Step 3 paste the document as the only content the LLM has seen
- Step 4 ask the test question written at the bottom of the document
- Step 5 grade the result as PASS if correct and FAIL if wrong or incomplete
- Step 6 write the result to kb/architecture/injection_tests/document_name_test.md
- Documents without a test result have not been validated and must not be loaded by the agent

Forbidden contradictions:
- Stating fewer than 6 steps in the protocol
- Stating untested documents can be loaded by the agent
- Stating the test can be run with other documents in the context window

---

### Question 3
"What is the Karpathy discipline and what is the core difference between this discipline and standard documentation practice?"

Required concepts:
- The Karpathy discipline is removal not accumulation
- Every document must be minimal and precise
- Every document must pass an injection test before committing
- Standard documentation grows over time by adding more content
- The Karpathy discipline requires removing everything the LLM already knows from pretraining
- Only include content specific to DAB these databases and this agent
- A KB that grows without being tested becomes noise that degrades the agent
- The test for every sentence is whether the agent reading only that sentence could take the correct action

Forbidden contradictions:
- Stating the Karpathy discipline encourages adding comprehensive content for completeness
- Stating documents do not need testing before use

---

### Question 4
"Which document has the smallest token budget, what is that budget, and why is it deliberately kept that small?"

Required concepts:
- MEMORY.md has the smallest token budget
- The budget is approximately 200 tokens
- MEMORY.md is loaded at every session start before the question arrives
- MEMORY.md is a pointer not a topic document
- Its only job is to list what other documents exist and what each one contains in one sentence
- Every token it consumes comes from the mandatory pre-load budget before any question-specific loading begins
- If MEMORY.md grows beyond 200 tokens it becomes a topic document masquerading as an index
- Growing MEMORY.md wastes mandatory context budget before any question-specific loading has started
- Any content that belongs in a topic file must be moved to that file not added to MEMORY.md

Forbidden contradictions:
- Stating tool_scoping.md has the smallest token budget
- Stating MEMORY.md can grow freely without affecting session performance

---

## Test result

**Run timestamp:** 2026-04-11 12:31 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/kb_v1_architecture.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** What are the four KB subdirectories in the Oracle Forge project and what type of information belongs in each one?

**Concepts found (7/7):**
  - [x] kb/architecture/ contains documents about how the agent itself works including memory architecture and tool scoping rules
  - [x] kb/architecture/ documents change when the agent architecture changes not when datasets change
  - [x] kb/domain/ contains documents about the data the agent works with including schemas and join key formats and business term definitions
  - [x] kb/domain/ documents change when datasets are loaded or failure patterns reveal schema misunderstandings
  - [x] kb/evaluation/ contains documents about how the agent is scored and what the benchmark requires including DAB query format and pass at 1 scoring
  - [x] kb/corrections/ contains the running structured log of agent failures read at every session start
  - [x] kb/corrections/log.md is the self-learning loop written by Drivers after every observed failure

**Actual answer:**
Based on the document, the four KB subdirectories in the Oracle Forge project are:

## kb/architecture/
Contains documents about how the agent itself works: the memory architecture, tool scoping rules, context loading order, and structural overview. These documents are written for the agent about the agent. They change when the agent architecture changes, not when DAB datasets change.

## kb/domain/
Contains documents about the data the agent works with: schema descriptions per DAB dataset, join key formats across database systems, unstructured field inventory, and business term definitions. These documents change when datasets are loaded, when new failure patterns reveal schema misunderstandings, or when domain terms are corrected.

## kb/evaluation/
Contains documents about how the agent is scored and what the benchmark requires: DAB query format, pass@1 scoring method, submission requirements, the four DAB failure categories, and what each failure category looks like in agent behavior.

## kb/corrections/
Contains `log.md`, which is the self-learning loop - a running structured log of agent failures written by Drivers after every observed agent failure. The agent reads the last 10 entries at session start, and Intelligence Officers prune outdated entries when newer ones supersede them.

**Grader reasoning:** All seven required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---

### Question 2 — PASS (100/100)

**Question:** An Intelligence Officer wants to add a new document to the KB. What are the exact six steps of the injection test protocol they must follow before committing?

**Concepts found (7/7):**
  - [x] Step 1 copy the full text of the document
  - [x] Step 2 open a completely fresh LLM session with no other context and no system prompt
  - [x] Step 3 paste the document as the only content the LLM has seen
  - [x] Step 4 ask the test question written at the bottom of the document
  - [x] Step 5 grade the result as PASS if correct and FAIL if wrong or incomplete
  - [x] Step 6 write the result to kb/architecture/injection_tests/document_name_test.md
  - [x] Documents without a test result have not been validated and must not be loaded by the agent

**Actual answer:**
According to the injection test protocol in the document, the exact six steps are:

1. Copy the full text of the document.
2. Open a completely fresh LLM session (no other context, no system prompt).
3. Paste the document as the only content the LLM has seen.
4. Ask the test question written at the bottom of the document.
5. Grade: correct answer = PASS. Wrong or incomplete = FAIL.
6. Write result to kb/architecture/injection_tests/[document_name]_test.md.

The document emphasizes that "A document that has not been injection-tested must not be loaded by the agent under any circumstances" and "A document without a test result in its test file has not been validated and must not be loaded by the agent."

**Grader reasoning:** All seven required concepts are clearly present in the actual answer with accurate details and no forbidden contradictions are found.

---

### Question 3 — PASS (100/100)

**Question:** What is the Karpathy discipline and what is the core difference between this discipline and standard documentation practice?

**Concepts found (8/8):**
  - [x] The Karpathy discipline is removal not accumulation
  - [x] Every document must be minimal and precise
  - [x] Every document must pass an injection test before committing
  - [x] Standard documentation grows over time by adding more content
  - [x] The Karpathy discipline requires removing everything the LLM already knows from pretraining
  - [x] Only include content specific to DAB these databases and this agent
  - [x] A KB that grows without being tested becomes noise that degrades the agent
  - [x] The test for every sentence is whether the agent reading only that sentence could take the correct action

**Actual answer:**
Based on the document, the Karpathy discipline is **removal, not accumulation**. Every document must be minimal and precise, and must pass an injection test before committing.

The core difference between the Karpathy discipline and standard documentation practice is:

- **Standard documentation practice**: grows over time by adding more content
- **Karpathy method**: does the opposite - it shrinks documents by removing what is not proven to work

The Karpathy method requires removing everything the LLM already knows from pretraining and only including content specific to DAB, these databases, and this agent — nothing general. The principle is that a KB that grows without being tested becomes noise that degrades the agent.

The test for every sentence is: if the agent read only this sentence with no other context, could it take the correct action? If no — rewrite it or cut it.

**Grader reasoning:** All eight required concepts are clearly present in the actual answer with no forbidden contradictions.

---

### Question 4 — PASS (100/100)

**Question:** Which document has the smallest token budget, what is that budget, and why is it deliberately kept that small?

**Concepts found (9/9):**
  - [x] MEMORY.md has the smallest token budget
  - [x] The budget is approximately 200 tokens
  - [x] MEMORY.md is loaded at every session start before the question arrives
  - [x] MEMORY.md is a pointer not a topic document
  - [x] Its only job is to list what other documents exist and what each one contains in one sentence
  - [x] Every token it consumes comes from the mandatory pre-load budget before any question-specific loading begins
  - [x] If MEMORY.md grows beyond 200 tokens it becomes a topic document masquerading as an index
  - [x] Growing MEMORY.md wastes mandatory context budget before any question-specific loading has started
  - [x] Any content that belongs in a topic file must be moved to that file not added to MEMORY.md

**Actual answer:**
Based on the document, **MEMORY.md** has the smallest token budget at **~200 tokens**.

It is deliberately kept that small because:

1. **It's a pointer, not a topic document** - Its only job is to list what other documents exist and what each one contains in one sentence

2. **It's loaded at every session start before the question arrives** - Every token it consumes comes directly out of the mandatory pre-load budget before any question-specific loading has begun

3. **Growing beyond ~200 tokens defeats its purpose** - If it grows larger, it starts functioning as a topic document masquerading as an index, wastes mandatory context budget on information that belongs in topic files, and becomes something the agent needs to read carefully rather than scan quickly to decide what to load next

The document emphasizes "Keep it small on purpose" and states that any content that belongs in a topic file must be moved to that file, not added to MEMORY.md.

**Grader reasoning:** All nine required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---
