# Injection test — openai_agent_context.md

## Document under test
`kb/architecture/openai_agent_context.md`

## Why this test is critical
This document contains the six-layer architecture that justifies the Oracle Forge agent's mandatory context layers. If the agent cannot map each layer to its Oracle Forge equivalent from this document alone, it will skip loading critical layers under failure conditions.

---

## Test questions

### Question 1
"What is Layer 5 in OpenAI's six-layer context architecture, what problem does it solve, what was the measured performance impact, and what is the Oracle Forge equivalent?"

Required concepts:
- Layer 5 is the learning memory
- It stores corrections and nuances from previous conversations
- It applies those corrections automatically to future requests
- It solves the problem of repeated failures across sessions
- Without memory a specific query took over 22 minutes
- With memory enabled that same query dropped to 1 minute and 22 seconds
- The Oracle Forge equivalent is kb/corrections/log.md
- The corrections log format is query that failed then what was wrong then correct approach
- The agent reads the last 10 entries at every session start

Forbidden contradictions:
- Stating Layer 5 is Codex Enrichment
- Stating the Oracle Forge equivalent is kb/domain/schemas.md
- Stating memory had no measurable performance impact

---

### Question 2
"What is Codex Enrichment, which layer number is it, and what does it reveal that basic schema metadata cannot?"

Required concepts:
- Codex Enrichment is Layer 3
- It is a daily asynchronous process
- Codex crawls the codebase that generates each data table
- It derives each table's meaning from the pipeline code itself
- Pipeline logic captures upstream and downstream dependencies
- Pipeline logic captures ownership granularity and join keys
- Pipeline logic captures filtering assumptions that never appear in schema metadata
- Example: code may reveal a table filters to only US users before aggregating invisible in the schema
- Many tables look identical in schema but differ critically in actual data content

Forbidden contradictions:
- Stating Codex Enrichment is Layer 1 or Layer 2
- Stating schema metadata alone reveals filtering assumptions
- Stating Codex Enrichment is a real-time process not a daily one

---

### Question 3
"What is the closed-loop self-correction pattern and how does it differ from standard error handling?"

Required concepts:
- The agent evaluates its own intermediate results during execution not only at the end
- If a result looks wrong such as zero rows from an expected join the agent investigates
- The agent adjusts its approach and retries without returning the suspicious result to the user
- The agent carries the correction forward as a log entry so the same mistake does not recur
- Standard error handling reacts to exceptions raised by the system
- Self-correction evaluates quality of reasoning even when no exception is raised
- A wrong answer that looks correct will not trigger an exception but self-correction catches it

Forbidden contradictions:
- Stating self-correction and error handling are the same thing
- Stating the agent returns zero-row results and lets the user investigate

---

### Question 4
"What is the core problem OpenAI's data agent architecture exists to solve and how does this apply to the DataAgentBench challenge?"

Required concepts:
- The core problem is that finding the right table is the hardest sub-problem not query generation
- Many tables look similar on the surface but differ critically in data content
- One table might include only logged-in users while another includes everyone
- Without layered context the agent picks the wrong table and produces a wrong answer that looks correct
- DataAgentBench contains multiple databases with similarly-named tables with different semantics
- DAB has inconsistently-formatted join keys across database systems
- DAB has domain-specific business terms not derivable from the schema
- The six-layer architecture exists to give the agent context to distinguish these cases

Forbidden contradictions:
- Stating query generation syntax is the hardest sub-problem
- Stating wrong table selection always produces an obvious error

---

### Question 5
"What are the three engineering lessons OpenAI documented from building their data agent?"

Required concepts:
- Tool consolidation matters and overlapping tools with redundant functionality confuse the agent
- Restrict to one tool per database type with tight domain boundaries
- Less prescriptive prompting works better than rigid step-by-step instructions
- Rigid instructions pushed the agent down wrong paths when situation did not match the script
- Higher-level guidance combined with model reasoning produces more robust results
- Code reveals what metadata hides because pipeline logic contains filtering assumptions invisible in schemas
- Crawling the codebase that generates tables provides more useful context than reading table schemas

Forbidden contradictions:
- Stating more tools with overlapping functions improve reliability
- Stating rigid step-by-step prompting outperforms higher-level guidance

---

## Test result

**Run timestamp:** 2026-04-11 12:30 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/openai_agent_context.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** What is Layer 5 in OpenAI's six-layer context architecture, what problem does it solve, what was the measured performance impact, and what is the Oracle Forge equivalent?

**Concepts found (9/9):**
  - [x] Layer 5 is the learning memory
  - [x] It stores corrections and nuances from previous conversations
  - [x] It applies those corrections automatically to future requests
  - [x] It solves the problem of repeated failures across sessions
  - [x] Without memory a specific query took over 22 minutes
  - [x] With memory enabled that same query dropped to 1 minute and 22 seconds
  - [x] The Oracle Forge equivalent is kb/corrections/log.md
  - [x] The corrections log format is query that failed then what was wrong then correct approach
  - [x] The agent reads the last 10 entries at every session start

**Actual answer:**
Based on the document, Layer 5 in OpenAI's six-layer context architecture is **Learning memory (self-correction loop)**.

**What it does:** The agent stores corrections and nuances discovered in previous conversations and applies them automatically to future requests. For example: "The join between the customer table and the transaction table requires zero-padding the customer ID to 5 digits."

**Problem it solves:** It reduces repeated failures from the same mistake by maintaining institutional memory of what went wrong and how it was corrected.

**Measured performance impact:** According to OpenAI's measurements, a query that took 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled. The document states that "Memory is non-negotiable."

**Oracle Forge equivalent:** The equivalent is `kb/corrections/log.md` — a running structured log of `[query that failed] → [what was wrong] → [correct approach]`. The agent reads the last 10 entries at every session start (not all entries, only the last 10).

**Grader reasoning:** All nine required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---

### Question 2 — PASS (100/100)

**Question:** What is Codex Enrichment, which layer number is it, and what does it reveal that basic schema metadata cannot?

**Concepts found (9/9):**
  - [x] Codex Enrichment is Layer 3
  - [x] It is a daily asynchronous process
  - [x] Codex crawls the codebase that generates each data table
  - [x] It derives each table's meaning from the pipeline code itself
  - [x] Pipeline logic captures upstream and downstream dependencies
  - [x] Pipeline logic captures ownership granularity and join keys
  - [x] Pipeline logic captures filtering assumptions that never appear in schema metadata
  - [x] Example: code may reveal a table filters to only US users before aggregating invisible in the schema
  - [x] Many tables look identical in schema but differ critically in actual data content

**Actual answer:**
According to the document, Codex Enrichment is Layer 3 of OpenAI's six-layer context architecture.

Codex Enrichment is a daily asynchronous background process (not real-time) where Codex crawls the codebase that generates each data table and derives a deeper definition from the pipeline code itself.

What Codex Enrichment reveals that basic schema metadata cannot:

1. **Upstream and downstream dependencies** - facts that never appear in SQL schema metadata or column names
2. **Ownership and granularity information**
3. **Join keys** - critical connection information not visible in schemas
4. **Filtering assumptions** - example: the code reveals that a table filters to only US users before aggregating, which is invisible in the schema
5. **Freshness guarantees** - pipeline logic captures these guarantees that are invisible in schemas
6. **Pipeline logic and transformations** - what was filtered, transformed, and assumed during data generation

The document emphasizes that "Many tables look identical in their schema but differ critically in actual data content" and that "crawling the codebase that generates tables provides more useful context than reading the tables themselves." While reading table schema only tells you column names, reading the code that generates the table reveals the underlying business logic and data processing assumptions.

**Grader reasoning:** All required concepts are clearly present and no forbidden contradictions were found.

---

### Question 3 — PASS (100/100)

**Question:** What is the closed-loop self-correction pattern and how does it differ from standard error handling?

**Concepts found (7/7):**
  - [x] The agent evaluates its own intermediate results during execution not only at the end
  - [x] If a result looks wrong such as zero rows from an expected join the agent investigates
  - [x] The agent adjusts its approach and retries without returning the suspicious result to the user
  - [x] The agent carries the correction forward as a log entry so the same mistake does not recur
  - [x] Standard error handling reacts to exceptions raised by the system
  - [x] Self-correction evaluates quality of reasoning even when no exception is raised
  - [x] A wrong answer that looks correct will not trigger an exception but self-correction catches it

**Actual answer:**
Based on the document, the closed-loop self-correction pattern is when the agent evaluates its own intermediate results during execution — not only at the end. This evaluation happens mid-execution after every tool call that returns data.

If an intermediate result looks wrong — such as zero rows from an expected join, a count that seems too high, or a metric that contradicts a known baseline — the agent does not return the result. Instead, it investigates by checking the join keys, filter conditions, and whether the correct table was selected. Then it adjusts its approach and retries. It carries the finding forward as a correction log entry so the same mistake does not recur.

The key difference from standard error handling is:

**Error handling** reacts to exceptions raised by the system — it responds to technical failures or system errors.

**Self-correction** evaluates the quality of the agent's own reasoning even when no exception is raised. It catches wrong answers that look correct but are actually incorrect. As the document states: "A wrong answer that looks correct will not trigger any system exception, but self-correction catches it by checking whether the result is plausible."

The Oracle Forge agent implements this pattern in `self_corrector.py`.

**Grader reasoning:** All seven required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---

### Question 4 — PASS (100/100)

**Question:** What is the core problem OpenAI's data agent architecture exists to solve and how does this apply to the DataAgentBench challenge?

**Concepts found (8/8):**
  - [x] The core problem is that finding the right table is the hardest sub-problem not query generation
  - [x] Many tables look similar on the surface but differ critically in data content
  - [x] One table might include only logged-in users while another includes everyone
  - [x] Without layered context the agent picks the wrong table and produces a wrong answer that looks correct
  - [x] DataAgentBench contains multiple databases with similarly-named tables with different semantics
  - [x] DAB has inconsistently-formatted join keys across database systems
  - [x] DAB has domain-specific business terms not derivable from the schema
  - [x] The six-layer architecture exists to give the agent context to distinguish these cases

**Actual answer:**
According to the document, the core problem OpenAI's data agent architecture exists to solve is that **finding the right table is the hardest sub-problem — not query generation**. 

The specific issue is that many tables look similar on the surface but differ critically in their actual data content and semantics. For example:
- One table includes only logged-in users, another includes everyone
- One captures only first-party traffic, another captures everything

Without layered context, the agent picks the wrong table and produces a wrong answer that looks correct. Critically, no SQL error fires — the answer simply uses the wrong data.

This applies directly to the DataAgentBench (DAB) challenge in three specific ways:

1. **Similar table names with different semantics**: DAB has multiple databases with similarly-named tables that have different meanings

2. **Inconsistent data formats**: DAB has inconsistently-formatted join keys across database systems — a customer ID might be an integer in PostgreSQL but a "CUST-00123" string in MongoDB

3. **Domain-specific business logic**: DAB has domain-specific business terms that are not derivable from the schema alone — for example, "active customer" means purchased in the last 90 days, not just row existence

The six-layer architecture exists specifically to give the agent the context needed to distinguish these three categories of problems before attempting to answer queries, preventing the silent failures that occur when technically correct SQL queries run against the wrong data sources.

**Grader reasoning:** All eight required concepts are clearly present in the actual answer with no forbidden contradictions.

---

### Question 5 — PASS (100/100)

**Question:** What are the three engineering lessons OpenAI documented from building their data agent?

**Concepts found (7/7):**
  - [x] Tool consolidation matters and overlapping tools with redundant functionality confuse the agent
  - [x] Restrict to one tool per database type with tight domain boundaries
  - [x] Less prescriptive prompting works better than rigid step-by-step instructions
  - [x] Rigid instructions pushed the agent down wrong paths when situation did not match the script
  - [x] Higher-level guidance combined with model reasoning produces more robust results
  - [x] Code reveals what metadata hides because pipeline logic contains filtering assumptions invisible in schemas
  - [x] Crawling the codebase that generates tables provides more useful context than reading table schemas

**Actual answer:**
According to the document, OpenAI documented three key engineering lessons from building their data agent:

1. **Tool consolidation matters**: Overlapping tools confuse the agent. The solution is to restrict to one tool per database type with tight domain boundaries — following the same principle as Claude Code's tool scoping philosophy.

2. **Less prescriptive prompting**: Rigid step-by-step instructions pushed the agent down wrong paths when the situation didn't match the script. Higher-level guidance plus model reasoning produces more robust results.

3. **Code reveals what metadata hides**: Pipeline logic contains assumptions that never surface in table schemas. Crawling the codebase that generates tables provides more useful context than reading the tables themselves — reading the table schema tells you column names; reading the code that generates the table tells you what was filtered, transformed, and assumed.

**Grader reasoning:** All seven required concepts are clearly present in the answer and no forbidden contradictions were found.

---
