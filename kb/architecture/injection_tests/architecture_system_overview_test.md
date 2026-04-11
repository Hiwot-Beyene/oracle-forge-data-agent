# Injection test — architecture_system_overview.md

## Document under test
`kb/architecture/architecture_system_overview.md`

## Test questions

### Question 1
"What are the four KB subdirectories and what does each one contain?"

Required concepts:
- kb/architecture/ contains documents about how the agent works
- kb/domain/ contains documents about the data (schemas, join keys)
- kb/evaluation/ contains documents about scoring and benchmark
- kb/corrections/ contains the self-learning log (log.md)

Forbidden contradictions:
- Missing any of the four subdirectories

---

### Question 2
"What is the Karpathy Method and what is its primary rule for documentation?"

Required concepts:
- Karpathy discipline is removal, not accumulation
- Every document must be minimal and precise
- Remove anything the LLM knows from pretraining
- Test every sentence: can the agent take correct action with only this sentence?

---

## Test result

**Run timestamp:** 2026-04-11 14:44 UTC
**Document:** system_overview
### Q1: 100/100
**Actual:** Based on the document, the four KB subdirectories are:

## kb/architecture/
Contains documents about how the agent itself works: the memory architecture, tool scoping rules, context loading order, and this structural overview. Documents here are written for the agent, about the agent. They change when the agent architecture changes.

## kb/domain/
Contains documents about the data: schema descriptions per DAB dataset, join key formats, and business term definitions. Documents here change when datasets are loaded or new failure patterns reveal schema misunderstandings.

## kb/evaluation/
Contains documents about how the agent is scored: DAB query format, pass@1 scoring, and failure taxonomy.

## kb/corrections/
`kb/corrections/log.md` is the self-learning loop. It is a running structured log of agent failures written by Drivers after every failure. The agent reads the last 10 entries at session start.
---
### Q2: 100/100
**Actual:** According to the document, the Karpathy Method is a documentation discipline with the primary rule of **removal, not accumulation**.

The method emphasizes:
- **Minimum Content, Maximum Precision** - Every document must be minimal and precise
- **Injection Test requirement** - Every document must pass an Injection Test before committing
- **Remove redundancy** - Remove everything the LLM already knows from pretraining; include only DAB-specific knowledge
- **Actionability test** - The test for every sentence is: "If the agent read only this sentence with no other context, could it take the correct action?"

The core philosophy is about creating documentation that is deliberately sparse and precise rather than comprehensive and verbose.
---