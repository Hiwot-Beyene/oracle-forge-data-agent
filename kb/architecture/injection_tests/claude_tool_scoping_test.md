# Injection test — claude_tool_scoping.md

## Document under test
`kb/architecture/claude_tool_scoping.md`

## Test questions

### Question 1
"Why does the agent use separate tools per database type instead of one general tool?"

Required concepts:
- Each tool has a single tight responsibility
- A tool with one precise purpose is more reliable
- When a tool fails the agent knows exactly which one and why
- Tight domain boundaries make failures diagnosable
- Tight domain boundaries make failures recoverable

Forbidden contradictions:
- Stating fewer tools are better for reliability

---

### Question 2
"What is the Zero-Row Rule and what three things must the agent check before reporting zero rows?"

Required concepts:
- Do not return zero-row result to user without investigation
- Check join keys (int vs string, padding)
- Check filter conditions (restrictive dates/status)
- Check table selection (correct source of truth)

Forbidden contradictions:
- Stating zero rows should be reported immediately

---

### Question 3
"What are the Cross-Database Merge Protocols when a query spans two different database engines?"

Required concepts:
- Route sub-queries to each database separately
- Fetch raw results into Python variables
- Merge results using execute_python
- Do NOT attempt cross-database joins at the SQL level

Forbidden contradictions:
- Suggesting SQL-level joins across database engines are allowed

---

## Test result

**Run timestamp:** 2026-04-11 16:42 UTC
**Document:** tool_scoping
### Q1: 100/100
**Concepts found:**
  - [x] Each tool has a single tight responsibility
  - [x] A tool with one precise purpose is more reliable
  - [x] When a tool fails the agent knows exactly which one and why
  - [x] Tight domain boundaries make failures diagnosable
  - [x] Tight domain boundaries make failures recoverable
**Concepts missing:**
**Actual answer:**
Based on the document, the agent uses separate tools per database type instead of one general tool because of the **Core Philosophy: Tight Domain Boundaries**.

The key reasons are:

1. **Reliability**: A tool with one precise purpose is more reliable than a tool doing multiple things loosely.

2. **Diagnosability**: When a tool fails, the agent knows exactly which one and why. Tight domain boundaries make failures diagnosable.

3. **Recoverability**: Tight domain boundaries make failures recoverable — the agent knows exactly what to fix.

The document emphasizes that "Each tool has a **single tight responsibility**. A tool that does one thing precisely is more reliable than a tool trying to do multiple things loosely."

Additionally, using named tools (rather than raw SQL execution) enables:
- **Query tracing**: Essential for the evaluation harness
- **Automatic translation**: Handles PostgreSQL vs. SQLite vs. DuckDB dialects  
- **Failure recovery**: The tool returns structured errors, enabling the agent to auto-correct

This is why the Oracle Forge DAB engine uses separate tools per database type (like `query_postgres_[dataset]` and `query_mongo_[collection]`) rather than one general database tool.
**Grader reasoning:** All five required concepts are explicitly present in the answer with direct quotes and clear explanations, and no forbidden contradictions are found.
---
### Q2: 100/100
**Concepts found:**
  - [x] Do not return zero-row result to user without investigation
  - [x] Check join keys (int vs string, padding)
  - [x] Check filter conditions (restrictive dates/status)
  - [x] Check table selection (correct source of truth)
**Concepts missing:**
**Actual answer:**
Based on the document, the Zero-Row Rule is:

**"Do not return a zero-row result to the user without investigation."**

When a query returns no rows, the agent must check these three things before reporting zero rows:

1. **Check Join Keys**: Verify if types match (e.g., int vs string) or if padding is needed.

2. **Check Filter Conditions**: Verify if dates or status codes were too restrictive.

3. **Check Table Selection**: Ensure the correct "source of truth" table was picked.

Only after these checks fail to find an error can the agent report zero rows to the user.
**Grader reasoning:** All four required concepts are clearly present in the answer with specific details matching the checklist, and no forbidden contradictions exist.
---
### Q3: 100/100
**Concepts found:**
  - [x] Route sub-queries to each database separately
  - [x] Fetch raw results into Python variables
  - [x] Merge results using execute_python
  - [x] Do NOT attempt cross-database joins at the SQL level
**Concepts missing:**
**Actual answer:**
According to the document, when a query spans two different database engines (e.g., PostgreSQL and MongoDB), the Cross-Database Merge Protocols are:

1. **Separate Queries:** Route sub-queries to each database separately via the designated tool.

2. **Fetch Locally:** Fetch the raw results from each into Python variables.

3. **No SQL Joins:** Merge results using `execute_python`. **Do NOT attempt cross-database joins at the SQL level.**

4. **Finalize:** Only after merging and validating python-side should the agent return the final answer.
**Grader reasoning:** All four required concepts are clearly present in the answer and no forbidden contradictions exist.
---