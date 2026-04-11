# Injection test — claude_autodream.md

## Document under test
`kb/architecture/claude_autodream.md`

## Test questions

### Question 1
"What is autoDream, when does it run, what does it do to topic files, and how is it implemented for Oracle Forge?"

Required concepts:
- autoDream is a background process
- It runs after sessions end not during sessions
- It reviews what was learned during the session
- It consolidates learnings back into topic files
- It removes old superseded information
- The topic file after consolidation is smaller and more precise
- For Oracle Forge it reviews the corrections log after agent runs

Forbidden contradictions:
- Stating autoDream runs during a live session

---

## Test result

**Run timestamp:** 2026-04-11 16:41 UTC
**Document:** claude_autodream
### Q1: 100/100
**Concepts found:**
  - [x] autoDream is a background process
  - [x] It runs after sessions end not during sessions
  - [x] It reviews what was learned during the session
  - [x] It consolidates learnings back into topic files
  - [x] It removes old superseded information
  - [x] The topic file after consolidation is smaller and more precise
  - [x] For Oracle Forge it reviews the corrections log after agent runs
**Concepts missing:**
**Actual answer:**
Based on the document, here's what I can tell you about autoDream:

**What is autoDream:**
autoDream is a background process that consolidates memory and learned information.

**When it runs:**
It runs **after** sessions end — never during a live session.

**What it does to topic files:**
- It reviews what was learned during the session (corrections, query patterns, business terms) and consolidates them back into the relevant topic files
- It removes old, superseded information using a "DAB Mechanism"
- The topic file after consolidation is **provably smaller and more precise** than before the session
- It prevents the knowledge base from expanding indefinitely by pruning outdated or inaccurate information

**How it's implemented for Oracle Forge:**
- It reviews the corrections log after agent runs
- It specifically reviews the `kb/corrections/log.md` log
- It absorbs verified fixes during the next "dream" cycle
- It removes those entries from the log once they're merged into topic files
- If a correction makes a topic file more accurate, it gets merged; this prevents the KB from growing into noise

The key principle is that "Knowledge is a garden, not a dumpster" — pruning outdated information is as important as adding new facts to prevent the agent from becoming confused by conflicting rules.
**Grader reasoning:** All seven required concepts are clearly present in the answer and no forbidden contradictions were found.
---