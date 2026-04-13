# Claude Code — Tool Scoping Philosophy

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: Claude Code npm leak, March 31 2026_

### Core Philosophy: Tight Domain Boundaries

Each tool has a **single tight responsibility**. A tool that does one thing precisely is more reliable than a tool trying to do multiple things loosely.
- **Reliability**: A tool with one precise purpose is more reliable than a tool doing multiple things.
- **Diagnosability**: When a tool fails, the agent knows exactly which one and why. Tight domain boundaries make failures diagnosable.
- **Recoverability**: Tight domain boundaries make failures recoverable — the agent knows exactly what to fix.
- **Source Logic**: `src/Tool.ts` (~29K lines) defines the base type with input schema (Zod validation), permission models, and execution logic.

### Database Tool Routing

For the Oracle Forge DAB engine, we use separate tools per database type rather than one general tool.

| Engine | Tool to Use | Query Dialect |
| :--- | :--- | :--- |
| **PostgreSQL** | `query_db` | Standard SQL |
| **MongoDB** | `query_db` | MQL (JSON) |
| **SQLite** | `query_db` | SQLite SQL |
| **DuckDB** | `query_db` | MotherDuck SQL |

### The Zero-Row Rule
**Do not return a zero-row result to the user without investigation.**
If a query returns no rows, the agent must:
1. **Check Join Keys**: Verify if types match (e.g., int vs string) or if padding is needed.
2. **Check Filter Conditions**: Verify if dates or status codes were too restrictive.
3. **Check Table Selection**: Ensure the correct "source of truth" table was picked.
Only after these checks fail to find an error can the agent report zero rows.

### Cross-Database Merge Protocols
When a query spans two different database engines (e.g., PostgreSQL and MongoDB):
1. **Separate Queries:** Route sub-queries to each database separately via the designated tool.
2. **Fetch Locally:** Fetch the raw results from each into Python variables.
3. **No SQL Joins:** Merge results using `execute_python`. **Do NOT attempt cross-database joins at the SQL level.**
4. **Finalize:** Only after merging and validating python-side should the agent return the final answer.

### Required MCP Tools for DAB

1. `query_postgres_[dataset]` — one tool per PostgreSQL database
2. `query_mongo_[collection]` — one tool per MongoDB collection
3. `extract_structured_text` — unstructured field parser (Week 3 module)
4. `resolve_join_key` — format normalizer for cross-DB joins

### Key Insight

**Do not give the agent raw SQL execution. Give it named tools.** This enables:
- **Query tracing**: Essential for the evaluation harness.
- **Automatic translation**: Handles PostgreSQL vs. SQLite vs. DuckDB dialects.
- **Failure recovery**: The tool returns structured errors, enabling the agent to auto-correct.

---
### ⚙️ Injection Test Verification
- **Test Question:** "Why does the agent use separate tools per database type instead of one general tool?"
- **Expected Outcome:** Identify reliability and diagnosability as core reasons for tight domain boundaries.
- **Last Status:** ✅ PASS (100/100)
- **Verified On:** 2026-04-11
- **Test Specification:** claude_tool_scoping_test.md
