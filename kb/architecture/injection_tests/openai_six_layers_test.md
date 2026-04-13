# Injection test — openai_six_layers.md

## Document under test
`kb/architecture/openai_six_layers.md`

## Test questions

### Question 1
"What is Layer 5 in OpenAI's six-layer architecture and what is the Oracle Forge equivalent?"

Required concepts:
- Layer 5 is the Learning Memory (self-correction loop)
- Stores corrections and nuances from previous conversations
- Performance: 22 minutes dropped to 1:22 with memory
- Oracle Forge equivalent is kb/corrections/log.md
- Reads the last 10 entries at session start

Forbidden contradictions:
- Stating Layer 5 is human-curated documentation

---

### Question 2
"How does the agent handle a join between PostgreSQL and MongoDB according to the DAB failure scenarios?"

Required concepts:
- PostgreSQL uses integers for IDs
- MongoDB uses strings (e.g., CUST-00123)
- Layer 5 must document zero-padding or formatting rules
- Problem is a Join Key Mismatch

Forbidden contradictions:
- Stating both use identical ID formats

---

### Question 3
"What is the Closed-Loop Self-Correction Pattern and how does it differ from error handling?"

Required concepts:
- Error handling reacts to exceptions raised by the system
- Self-correction evaluates reasoning quality even when no exception is raised
- Catches plausible but wrong answers before returning

Forbidden contradictions:
- Stating self-correction is identical to error handling

---

## Test result

**Run timestamp:** 2026-04-11 16:42 UTC
**Document:** openai_context
### Q1: 100/100
**Concepts found:**
  - [x] Layer 5 is the Learning Memory (self-correction loop)
  - [x] Stores corrections and nuances from previous conversations
  - [x] Performance: 22 minutes dropped to 1:22 with memory
  - [x] Oracle Forge equivalent is kb/corrections/log.md
  - [x] Reads the last 10 entries at session start
**Concepts missing:**
**Actual answer:**
Based on the document, Layer 5 in OpenAI's six-layer architecture is **Learning Memory (self-correction loop)**.

**What Layer 5 provides:**
- Stores corrections and nuances from previous conversations 
- Applies them automatically to future requests
- Reads the last 10 entries at session start

**Oracle Forge equivalent:**
The Oracle Forge equivalent is **Learning Memory (self-correction loop)** implemented via `kb/corrections/log.md` (which reads the last 10 entries at session start).

**Performance impact:** 
The document notes that OpenAI found a query taking 22 minutes without memory dropped to just 1 minute 22 seconds with the self-correction loop enabled.
**Grader reasoning:** All five required concepts are clearly and explicitly present in the answer with no forbidden contradictions.
---
### Q2: 100/100
**Concepts found:**
  - [x] PostgreSQL uses integers for IDs
  - [x] MongoDB uses strings (e.g., CUST-00123)
  - [x] Layer 5 must document zero-padding or formatting rules
  - [x] Problem is a Join Key Mismatch
**Concepts missing:**
**Actual answer:**
According to the DAB failure scenarios section in the document, the agent handles joins between PostgreSQL and MongoDB by addressing the **Join Key Mismatch** issue through Layer 5 (Learning Memory).

Specifically:

- **The Problem**: PostgreSQL uses integers for join keys, while MongoDB uses strings (e.g., `CUST-00123`)
- **The Solution**: Layer 5 (Learning Memory) must document the zero-padding or formatting rule needed to properly match keys between the two systems

The document indicates this is handled through the Learning Memory system (implemented via `kb/corrections/log.md`), which stores corrections and formatting rules from previous conversations and applies them automatically to future requests. This allows the agent to learn the proper key formatting transformations needed to successfully join data between PostgreSQL's integer keys and MongoDB's string-based keys.
**Grader reasoning:** All four required concepts are clearly present in the answer and no forbidden contradictions were found.
---
### Q3: 100/100
**Concepts found:**
  - [x] Error handling reacts to exceptions raised by the system
  - [x] Self-correction evaluates reasoning quality even when no exception is raised
  - [x] Catches plausible but wrong answers before returning
**Concepts missing:**
**Actual answer:**
Based on the document, the Closed-Loop Self-Correction Pattern is a quality evaluation mechanism that differs fundamentally from traditional error handling in the following ways:

## What it IS:
- **Quality Evaluation:** The pattern evaluates the quality of the agent's own reasoning even when no system exception is raised
- **Proactive Checking:** It checks if results are plausible before returning them, even when the answer appears correct
- **Implemented via:** `self_corrector.py` in the system

## How it Differs from Error Handling:

**Error Handling:**
- Reacts to exceptions raised by the system
- Only activates when something breaks or fails
- Handles technical failures and system errors

**Self-Correction Pattern:**
- Evaluates reasoning quality regardless of system exceptions
- Catches scenarios where "an answer that looks correct but uses the wrong table will not trigger an exception"
- Focuses on logical correctness rather than technical failures

## The Key Rule:
The document emphasizes that an answer using the wrong data source can appear completely valid from a technical standpoint (no errors thrown), but be fundamentally incorrect. The self-correction pattern catches this by evaluating whether the result makes sense contextually before delivering it to the user.

This pattern is part of Layer 5 (Learning Memory) in the six-layer architecture and contributes to significant performance improvements - the document notes query times dropped from 22 minutes to 1 minute 22 seconds when this self-correction loop was enabled.
**Grader reasoning:** All three required concepts are clearly present in the answer with explicit explanations of how error handling reacts to system exceptions, how self-correction evaluates quality without exceptions, and how it catches plausible but wrong answers.
---