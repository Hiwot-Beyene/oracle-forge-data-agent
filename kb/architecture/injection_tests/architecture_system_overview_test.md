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

Forbidden contradictions:
- Stating the method encourages adding maximum context

---

### Question 3
"How does the agent use Worktree Sub-Agent Spawn Modes?"

Required concepts:
- Uses git worktrees to achieve process isolation
- Multiple trial runs of the same query run in isolation
- Results are aggregated by the execution harness after trials finish
- Never test destructive modifications directly in the primary workspace

Forbidden contradictions:
- Missing the rule on where to test destructive modifications

---

## Test result

**Run timestamp:** 2026-04-11 16:41 UTC
**Document:** system_overview
### Q1: 100/100
**Concepts found:**
  - [x] kb/architecture/ contains documents about how the agent works
  - [x] kb/domain/ contains documents about the data (schemas, join keys)
  - [x] kb/evaluation/ contains documents about scoring and benchmark
  - [x] kb/corrections/ contains the self-learning log (log.md)
**Concepts missing:**
**Actual answer:**
Based on the document, the four KB subdirectories are:

## kb/architecture/
Contains documents about how the agent itself works: the memory architecture, tool scoping rules, context loading order, and structural overview. Documents here are written for the agent, about the agent. They change when the agent architecture changes.

## kb/domain/
Contains documents about the data: schema descriptions per DAB dataset, join key formats, and business term definitions. Documents here change when datasets are loaded or new failure patterns reveal schema misunderstandings.

## kb/evaluation/
Contains documents about how the agent is scored: DAB query format, pass@1 scoring, and failure taxonomy.

## kb/corrections/
Contains `kb/corrections/log.md` which is the self-learning loop. It is a running structured log of agent failures written by Drivers after every failure. The agent reads the last 10 entries at session start.
**Grader reasoning:** All four required concepts are clearly present in the answer with accurate descriptions of each KB subdirectory's contents.
---
### Q2: 100/100
**Concepts found:**
  - [x] Karpathy discipline is removal, not accumulation
  - [x] Every document must be minimal and precise
  - [x] Remove anything the LLM knows from pretraining
  - [x] Test every sentence: can the agent take correct action with only this sentence?
**Concepts missing:**
**Actual answer:**
Based on the document, the Karpathy Method is a documentation discipline focused on **removal, not accumulation**. 

Its primary rule is **minimum content, maximum precision** - meaning every document must be minimal and precise while removing everything the LLM already knows from pretraining and including only DAB-specific knowledge.

The method includes these key requirements:
- Every document must pass an **Injection Test** before committing
- The test for every sentence is: "If the agent read only this sentence with no other context, could it take the correct action?"
- Remove everything the LLM already knows from pretraining; include only DAB-specific knowledge

The philosophy is explicitly about disciplined removal rather than accumulating more content.
**Grader reasoning:** All four required concepts are clearly present in the answer with accurate explanations and no forbidden contradictions.
---
### Q3: 100/100
**Concepts found:**
  - [x] Uses git worktrees to achieve process isolation
  - [x] Multiple trial runs of the same query run in isolation
  - [x] Results are aggregated by the execution harness after trials finish
  - [x] Never test destructive modifications directly in the primary workspace
**Concepts missing:**
**Actual answer:**
According to the document, the agent uses Worktree Sub-Agent Spawn Modes in the following way:

The agent uses git worktrees to achieve **process isolation for parallel experiments** with three key functions:

1. **Isolated Testing:** Multiple trial runs of the same query run in isolation (using `src/tools/EnterWorktreeTool.ts`) to prevent state corruption

2. **Aggregation:** Results from these isolated trials are aggregated by the execution harness after trials finish

3. **Safety Rule:** The agent never tests destructive modifications directly in the primary workspace - it always spawns a sub-agent into an isolated worktree

This follows the "Claude Code Pattern" and ensures that experimental or potentially harmful operations don't corrupt the main working environment while still allowing parallel testing and experimentation.
**Grader reasoning:** All four required concepts are clearly present in the answer with specific details and no forbidden contradictions exist.
---