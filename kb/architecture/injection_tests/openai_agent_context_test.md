# Injection test — openai_agent_context.md

## Document under test
`kb/architecture/openai_agent_context.md`

## Why this test is critical
openai_agent_context.md describes the six-layer context architecture from OpenAI's data agent. The Oracle Forge agent implements at least three of these layers. If the agent cannot derive the correct layer order and purpose from this document alone, it will misunderstand context layering strategy.

---

## Test questions

### Question 1
"What are all six layers of OpenAI's context architecture in order and what is the Oracle Forge equivalent for each?"

Required concepts:
- Layer 1 is schema metadata and historical queries with Oracle Forge equivalent list_db tool output
- Layer 2 is human-curated expert descriptions with Oracle Forge equivalent kb/domain/schemas.md
- Layer 3 is Codex Enrichment which is code-level table definitions
- Layer 4 is institutional knowledge with Oracle Forge equivalent kb/domain/business_terms.md
- Layer 5 is learning memory with Oracle Forge equivalent kb/corrections/log.md
- Layer 6 is runtime context or live schema inspection with Oracle Forge equivalent execute_python plus query_db fallback

Forbidden contradictions:
- Stating the layers in the wrong order
- Omitting any of the six layers

---

### Question 2
"What is Codex Enrichment Layer 3, how does it work, and why is it a breakthrough?"

Required concepts:
- Codex Enrichment is Layer 3
- It is a daily asynchronous process not real-time and not triggered at query time
- Codex crawls the codebase that generates each data table and derives deeper definitions from the pipeline code
- From the code it infers upstream and downstream dependencies ownership granularity and join keys
- Pipeline logic captures filtering assumptions invisible in schemas
- The breakthrough is reading the code that generates the table not just the table schema
- Many tables look identical in SQL schema but differ critically in actual data content

Forbidden contradictions:
- Stating that Codex Enrichment runs in real-time at query time
- Stating that Codex reads only the SQL schema

---

### Question 3
"What is Layer 5 learning memory, what is the measured impact, what is the Oracle Forge equivalent, how many log entries are read at session start, and what is the log entry format?"

Required concepts:
- Layer 5 is the learning memory
- The agent stores corrections and nuances discovered in previous conversations
- It applies those corrections automatically to future requests
- A query that took over 22 minutes without memory dropped to 1 minute 22 seconds with memory
- Oracle Forge equivalent is kb/corrections/log.md
- The log is a structured log of query that failed then what was wrong then correct approach
- The agent reads the last 10 entries at every session start not all entries

Forbidden contradictions:
- Stating that all entries are read not just the last 10
- Stating that learning memory has no measurable impact

---

### Question 4
"What is the closed-loop self-correction pattern, how is it different from error handling, and why can a wrong answer avoid triggering any system exception?"

Required concepts:
- The agent evaluates its own intermediate results during execution not only at the end
- If an intermediate result looks wrong the agent investigates and does not return the result
- The agent adjusts its approach and retries without surfacing the failure to the user
- Error handling reacts to exceptions raised by the system
- Self-correction evaluates the quality of the agent's own reasoning even when no exception is raised
- A wrong answer that looks correct will not trigger any system exception

Forbidden contradictions:
- Stating that self-correction is the same as error handling
- Stating that the agent returns wrong-looking intermediate results to the user

---

### Question 5
"What are the three engineering lessons from OpenAI and what does each mean?"

Required concepts:
- Lesson 1 is tool consolidation matters meaning overlapping tools with redundant functionality confuse the agent
- Lesson 2 is less prescriptive prompting meaning rigid step-by-step instructions push the agent down wrong paths
- Lesson 3 is code reveals what metadata hides meaning pipeline logic contains filtering assumptions not in table schemas
- Higher-level guidance combined with model reasoning produces more robust results than rigid scripts

Forbidden contradictions:
- Stating that more prescriptive prompting is better
- Stating that overlapping tools are acceptable

## Test result

**Run timestamp:** 2026-04-11 17:47 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/architecture/openai_agent_context.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** What are all six layers of OpenAI's context architecture in order and what is the Oracle Forge equivalent for each?

**Concepts found (6/6):**
  - [x] Layer 1 is schema metadata and historical queries with Oracle Forge equivalent list_db tool output
  - [x] Layer 2 is human-curated expert descriptions with Oracle Forge equivalent kb/domain/schemas.md
  - [x] Layer 3 is Codex Enrichment which is code-level table definitions
  - [x] Layer 4 is institutional knowledge with Oracle Forge equivalent kb/domain/business_terms.md
  - [x] Layer 5 is learning memory with Oracle Forge equivalent kb/corrections/log.md
  - [x] Layer 6 is runtime context or live schema inspection with Oracle Forge equivalent execute_python plus query_db fallback

**Actual answer:**
Here are the six layers of OpenAI's context architecture in order, along with the Oracle Forge equivalents when available based on the document:

*   **Layer 1** — Schema metadata and historical queries. Oracle Forge equivalent: `list_db` tool output.
*   **Layer 2** — Human-curated expert descriptions. Oracle Forge equivalent: `kb/domain/schemas.md` written by Intelligence Officers from `db_description.txt` and `db_description_with_hint.txt`.
*   **Layer 3** — Codex Enrichment (code-level table definitions). No Oracle Forge equivalent is explicitly stated.
*   **Layer 4** — Institutional knowledge. Oracle Forge equivalent: `kb/domain/business_terms.md`.
*   **Layer 5** — Learning memory. Oracle Forge equivalent: `kb/corrections/log.md`.
*   **Layer 6** — Runtime context (live schema inspection). Oracle Forge equivalent: `execute_python` + `query_db` fallback via `list_db`.

**Grader reasoning:** All six layers of OpenAI's context architecture and their corresponding Oracle Forge equivalents are correctly identified and listed in the correct order, so the answer receives a perfect score.

---

### Question 2 — PASS (100/100)

**Question:** What is Codex Enrichment Layer 3, how does it work, and why is it a breakthrough?

**Concepts found (7/7):**
  - [x] Codex Enrichment is Layer 3
  - [x] It is a daily asynchronous process not real-time and not triggered at query time
  - [x] Codex crawls the codebase that generates each data table and derives deeper definitions from the pipeline code
  - [x] From the code it infers upstream and downstream dependencies ownership granularity and join keys
  - [x] Pipeline logic captures filtering assumptions invisible in schemas
  - [x] The breakthrough is reading the code that generates the table not just the table schema
  - [x] Many tables look identical in SQL schema but differ critically in actual data content

**Actual answer:**
Codex Enrichment is Layer 3 in OpenAI's six-layer context architecture. It is a daily asynchronous process where Codex crawls the codebase that generates each data table. From that code, it infers upstream and downstream dependencies, ownership, granularity, and join keys. It is a breakthrough because it finds differences in tables that look identical in their SQL schema but differ critically in actual data content by reading the code that generates the table. Pipeline logic captures filtering assumptions invisible in schemas.

**Grader reasoning:** The answer contains all required concepts and no forbidden contradictions, resulting in a perfect score.

---

### Question 3 — PASS (100/100)

**Question:** What is Layer 5 learning memory, what is the measured impact, what is the Oracle Forge equivalent, how many log entries are read at session start, and what is the log entry format?

**Concepts found (7/7):**
  - [x] Layer 5 is the learning memory
  - [x] The agent stores corrections and nuances discovered in previous conversations
  - [x] It applies those corrections automatically to future requests
  - [x] A query that took over 22 minutes without memory dropped to 1 minute 22 seconds with memory
  - [x] Oracle Forge equivalent is kb/corrections/log.md
  - [x] The log is a structured log of query that failed then what was wrong then correct approach
  - [x] The agent reads the last 10 entries at every session start not all entries

**Actual answer:**
Based on the document:

*   **Layer 5 learning memory:** The agent stores corrections and nuances discovered in previous conversations and applies those corrections automatically to future requests.
*   **Measured impact:** A query that took over 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled.
*   **Oracle Forge equivalent:** `kb/corrections/log.md` - structured log of `[query that failed] → [what was wrong] → [correct approach]`.
*   **Log entries read at session start:** The agent reads the last 10 entries at every session start.
*   **Log entry format:** `[query that failed] → [what was wrong] → [correct approach]`.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found.

---

### Question 4 — PASS (100/100)

**Question:** What is the closed-loop self-correction pattern, how is it different from error handling, and why can a wrong answer avoid triggering any system exception?

**Concepts found (6/6):**
  - [x] The agent evaluates its own intermediate results during execution not only at the end
  - [x] If an intermediate result looks wrong the agent investigates and does not return the result
  - [x] The agent adjusts its approach and retries without surfacing the failure to the user
  - [x] Error handling reacts to exceptions raised by the system
  - [x] Self-correction evaluates the quality of the agent's own reasoning even when no exception is raised
  - [x] A wrong answer that looks correct will not trigger any system exception

**Actual answer:**
The closed-loop self-correction pattern involves the agent evaluating its own intermediate results during execution, not just at the end. If an intermediate result seems wrong (e.g., zero rows from an expected join), the agent investigates and adjusts its approach without surfacing the failure to the user.

This differs from error handling because error handling reacts to exceptions raised by the system, while self-correction evaluates the quality of the agent's own reasoning even when no exception is raised.

A wrong answer that looks correct will not trigger any system exception because the wrong result is indistinguishable from a correct one at the system level. Self-correction catches it by checking whether the result is plausible.

**Grader reasoning:** All six required concepts are clearly present in the answer, and no forbidden contradictions are found, so the score is 100.

---

### Question 5 — PASS (100/100)

**Question:** What are the three engineering lessons from OpenAI and what does each mean?

**Concepts found (4/4):**
  - [x] Lesson 1 is tool consolidation matters meaning overlapping tools with redundant functionality confuse the agent
  - [x] Lesson 2 is less prescriptive prompting meaning rigid step-by-step instructions push the agent down wrong paths
  - [x] Lesson 3 is code reveals what metadata hides meaning pipeline logic contains filtering assumptions not in table schemas
  - [x] Higher-level guidance combined with model reasoning produces more robust results than rigid scripts

**Actual answer:**
Here are the three engineering lessons from OpenAI, as described in the document:

1.  **Tool consolidation matters:** Overlapping tools with redundant functionality confuse the agent. Restrict to one tool per database type with tight domain boundaries.
2.  **Less prescriptive prompting:** Rigid step-by-step instructions pushed the agent down wrong paths when the situation did not match the script. Higher-level guidance combined with model reasoning produces more robust results.
3.  **Code reveals what metadata hides:** Pipeline logic contains filtering assumptions that never surface in table schemas. Crawling the codebase that generates tables provides more useful context than reading the tables themselves. Reading a table schema tells you column names. Reading the code that generates the table tells you what was filtered, transformed, and assumed.

**Grader reasoning:** All required concepts are present in the answer, and no contradictions are found.

---
