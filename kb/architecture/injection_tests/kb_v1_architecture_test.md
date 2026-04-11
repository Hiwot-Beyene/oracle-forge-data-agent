# Injection test — kb_v1_architecture.md

## Document under test
`kb/architecture/kb_v1_architecture.md`

## Why this test is critical
kb_v1_architecture.md describes the Oracle Forge KB structure and the Karpathy method discipline. If the agent cannot derive the correct KB organization and quality rules from this document alone, it risks loading untested documents or misunderstanding the knowledge base structure.

---

## Test questions

### Question 1
"What are the four KB subdirectories in the Oracle Forge project and what does each one contain?"

Required concepts:
- kb/architecture/ contains documents about how the agent itself works including memory architecture tool scoping and context loading
- kb/domain/ contains documents about the data including schemas join keys unstructured fields and business terms
- kb/evaluation/ contains documents about scoring and the benchmark including DAB query format and failure categories
- kb/corrections/ contains the running structured log of agent failures with entry format query that failed then what was wrong then correct approach

Forbidden contradictions:
- Omitting any of the four subdirectories
- Stating that corrections are stored in kb/domain/

---

### Question 2
"What is the Karpathy method and what are the key rules that govern it?"

Required concepts:
- The Karpathy discipline is removal not accumulation
- Every document must be minimal and precise
- Every document must pass an injection test before committing
- A document that has not passed an injection test must not be loaded by the agent
- Remove everything the LLM already knows from pretraining
- Only include content specific to DAB these databases and this agent
- A KB that grows without being tested becomes noise that degrades the agent
- The test for every sentence is whether the agent reading only that sentence could take the correct action

Forbidden contradictions:
- Stating that documents can be loaded without passing injection tests
- Stating that accumulation is preferred over removal
- Stating that general knowledge should be included in the KB

---

### Question 3
"What is the six-step injection test protocol and what is the critical constraint about what other documents can be in the context window during the test?"

Required concepts:
- Step 1 copy the full text of the document
- Step 2 open a completely fresh LLM session with no other context and no system prompt
- Step 3 paste the document as the only content the LLM has seen
- Step 4 ask the test question written at the bottom of the document
- Step 5 grade the answer where correct is PASS and wrong or incomplete is FAIL
- Step 6 write the result to kb/architecture/injection_tests/document_name_test.md
- The test cannot be run with other documents in the context window

Forbidden contradictions:
- Stating that other documents can be in the context during the test
- Stating that the test can use a system prompt

---

### Question 4
"Why is MEMORY.md capped at the smallest token budget, what is its only job, when is it loaded, what happens if it grows beyond that cap, and what should be done with content that does not belong in MEMORY.md?"

Required concepts:
- MEMORY.md is capped at approximately 200 tokens because it is a pointer not a topic document
- Its only job is to list what other documents exist and what each contains in one sentence
- It is loaded at every session start before the question arrives
- If MEMORY.md grows beyond 200 tokens it becomes a topic document masquerading as an index
- Growing MEMORY.md wastes mandatory context budget before any question-specific loading begins
- Content that belongs in a topic file must be moved to that file not added to MEMORY.md

Forbidden contradictions:
- Stating that MEMORY.md should contain detailed topic knowledge
- Stating that MEMORY.md has no token limit

---

### Question 5
"What is the mandatory pre-load token budget, what is the per-document breakdown of the 900 tokens, what is the optional post-question maximum, and what is the total maximum across a full session?"

Required concepts:
- Mandatory pre-load total is approximately 900 tokens
- The 900 tokens breaks down as tool_scoping.md 300 plus corrections log 400 plus MEMORY.md 200
- Optional post-question maximum is approximately 700 tokens
- Total maximum across a full session is approximately 1600 tokens

Forbidden contradictions:
- Stating mandatory pre-load is more than 900 tokens
- Stating total maximum is less than 1600 tokens

## Test result

**Run timestamp:** 2026-04-11 17:47 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/architecture/kb_v1_architecture.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** What are the four KB subdirectories in the Oracle Forge project and what does each one contain?

**Concepts found (4/4):**
  - [x] kb/architecture/ contains documents about how the agent itself works including memory architecture tool scoping and context loading
  - [x] kb/domain/ contains documents about the data including schemas join keys unstructured fields and business terms
  - [x] kb/evaluation/ contains documents about scoring and the benchmark including DAB query format and failure categories
  - [x] kb/corrections/ contains the running structured log of agent failures with entry format query that failed then what was wrong then correct approach

**Actual answer:**
kb/architecture/ contains documents about how the agent works (memory system, tool scoping, context loading). kb/domain/ contains documents about the data (schemas, join keys, business terms). kb/evaluation/ contains documents about scoring and the benchmark. kb/corrections/ contains the running log of agent failures and their fixes, read at every session start.

**Grader reasoning:** The answer includes all four required concepts about the KB subdirectories without contradictions.

---

### Question 2 — PASS (100/100)

**Question:** What is the Karpathy method and what are the key rules that govern it?

**Concepts found (8/8):**
  - [x] The Karpathy discipline is removal not accumulation
  - [x] Every document must be minimal and precise
  - [x] Every document must pass an injection test before committing
  - [x] A document that has not passed an injection test must not be loaded by the agent
  - [x] Remove everything the LLM already knows from pretraining
  - [x] Only include content specific to DAB these databases and this agent
  - [x] A KB that grows without being tested becomes noise that degrades the agent
  - [x] The test for every sentence is whether the agent reading only that sentence could take the correct action

**Actual answer:**
The Karpathy method is **removal, not accumulation**. The key rules are:

1.  Every document must be minimal and precise.
2.  Every document must pass an injection test before committing.
3.  A document that has not passed an injection test must not be loaded by the agent under any circumstances.
4.  It shrinks documents by removing what is not proven to work.
5.  Remove everything the LLM already knows from pretraining. Only include content specific to DAB, these databases, and this agent. Nothing general.
6.  A KB that grows without being tested becomes noise that degrades the agent rather than helping it.
7.  The test for every sentence: if the agent read only this sentence with no other context, could it take the correct action? If no — rewrite it or cut it.
8.  Documents without a passing injection test result are treated as non-existent and must not be loaded by the agent.

**Grader reasoning:** All required concepts are clearly present in the actual answer and there are no forbidden contradictions.

---

### Question 3 — PASS (100/100)

**Question:** What is the six-step injection test protocol and what is the critical constraint about what other documents can be in the context window during the test?

**Concepts found (7/7):**
  - [x] Step 1 copy the full text of the document
  - [x] Step 2 open a completely fresh LLM session with no other context and no system prompt
  - [x] Step 3 paste the document as the only content the LLM has seen
  - [x] Step 4 ask the test question written at the bottom of the document
  - [x] Step 5 grade the answer where correct is PASS and wrong or incomplete is FAIL
  - [x] Step 6 write the result to kb/architecture/injection_tests/document_name_test.md
  - [x] The test cannot be run with other documents in the context window

**Actual answer:**
The six-step injection test protocol is:

1. Copy the full text of the document.
2. Open a completely fresh LLM session — no other context, no system prompt.
3. Paste the document as the only content the LLM has seen.
4. Ask the test question written at the bottom of the document.
5. Grade: correct answer = PASS. Wrong or incomplete = FAIL.
6. Write result to kb/architecture/injection\_tests/[document\_name]\_test.md.

The critical constraint is that the test cannot be run with other documents in the context window. The document being tested must be the only thing the model sees.

**Grader reasoning:** All required concepts are present, and no forbidden contradictions are found, resulting in a perfect score.

---

### Question 4 — PASS (100/100)

**Question:** Why is MEMORY.md capped at the smallest token budget, what is its only job, when is it loaded, what happens if it grows beyond that cap, and what should be done with content that does not belong in MEMORY.md?

**Concepts found (6/6):**
  - [x] MEMORY.md is capped at approximately 200 tokens because it is a pointer not a topic document
  - [x] Its only job is to list what other documents exist and what each contains in one sentence
  - [x] It is loaded at every session start before the question arrives
  - [x] If MEMORY.md grows beyond 200 tokens it becomes a topic document masquerading as an index
  - [x] Growing MEMORY.md wastes mandatory context budget before any question-specific loading begins
  - [x] Content that belongs in a topic file must be moved to that file not added to MEMORY.md

**Actual answer:**
Based on the provided document:

*   **Why is MEMORY.md capped at the smallest token budget?** It is a pointer, not a topic document. Every token it consumes comes directly out of the mandatory pre-load budget.
*   **What is its only job?** To list what other documents exist and what each one contains in one sentence.
*   **When is it loaded?** At every session start before the question arrives.
*   **What happens if it grows beyond that cap?** It becomes a topic document masquerading as an index, wasting mandatory context budget before any question-specific loading has started.
*   **What should be done with content that does not belong in MEMORY.md?** It must be moved to the appropriate topic file.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, resulting in a perfect score.

---

### Question 5 — PASS (100/100)

**Question:** What is the mandatory pre-load token budget, what is the per-document breakdown of the 900 tokens, what is the optional post-question maximum, and what is the total maximum across a full session?

**Concepts found (4/4):**
  - [x] Mandatory pre-load total is approximately 900 tokens
  - [x] The 900 tokens breaks down as tool_scoping.md 300 plus corrections log 400 plus MEMORY.md 200
  - [x] Optional post-question maximum is approximately 700 tokens
  - [x] Total maximum across a full session is approximately 1600 tokens

**Actual answer:**
*   **Mandatory pre-load total:** ~900 tokens.
*   **Breakdown**: tool\_scoping.md 300 + corrections/log.md 400 + MEMORY.md 200.
*   **Optional post-question maximum:** ~700 tokens.
*   **Total maximum across a full session:** ~1,600 tokens.

**Grader reasoning:** All required concepts are present, and no forbidden contradictions were found, resulting in a perfect score.

---
