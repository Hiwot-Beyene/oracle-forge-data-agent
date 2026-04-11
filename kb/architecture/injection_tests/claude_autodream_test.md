# Injection test — claude_autodream.md

## Document under test
`kb/architecture/claude_autodream.md`

## Test questions

### Question 1
"What is autoDream, when does it run, and what does it do to topic files?"

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

**Run timestamp:** 2026-04-11 14:44 UTC
**Document:** claude_autodream
### Q1: 85/100
**Actual:** Based on the document, autoDream is a background process with the following characteristics:

**What it is:** autoDream is a background process that consolidates memory and learning.

**When it runs:** It runs **after** sessions end — never during a live session.

**What it does to topic files:** 
- It reviews what was learned during sessions (corrections, query patterns, business terms)
- It consolidates this information back into the relevant topic files
- It removes old, superseded information
- The result is that topic files become **smaller and more precise** than before the session
- It verifies corrections in "dream" cycles and merges accurate corrections while pruning outdated or inaccurate information

The key mechanism prevents knowledge bases from growing indefinitely into noise by treating "knowledge as a garden, not a dumpster" - meaning it actively prunes and refines information rather than just accumulating it.
---