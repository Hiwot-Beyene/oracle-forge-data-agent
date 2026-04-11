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

## Test result

**Run timestamp:** 2026-04-11 14:45 UTC
**Document:** tool_scoping
### Q1: 100/100
**Actual:** Based on the document, the agent uses separate tools per database type instead of one general tool because of the **Core Philosophy: Tight Domain Boundaries**.

The key reasons are:

1. **Single Tight Responsibility**: Each tool has a single tight responsibility. A tool that does one thing precisely is more reliable than a tool trying to do multiple things loosely.

2. **Diagnosability**: When a tool fails, the agent knows exactly which one and why.

3. **Key Benefits of Named Tools over Raw SQL Execution**:
   - **Query tracing**: Essential for the evaluation harness
   - **Automatic translation**: Handles PostgreSQL vs. SQLite vs. DuckDB dialects
   - **Failure recovery**: The tool returns structured errors, enabling the agent to auto-correct

The document specifically states that this approach enables better reliability and precise error identification compared to having one general database tool that tries to handle multiple database types loosely.
---
### Q2: 100/100
**Actual:** Based on the document, the Zero-Row Rule states:

**"Do not return a zero-row result to the user without investigation."**

When a query returns no rows, the agent must check these three things before reporting zero rows:

1. **Check Join Keys**: Verify if types match (e.g., int vs string) or if padding is needed.

2. **Check Filter Conditions**: Verify if dates or status codes were too restrictive.

3. **Check Table Selection**: Ensure the correct "source of truth" table was picked.

Only after these checks fail to find an error can the agent report zero rows to the user.
---