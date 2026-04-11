# Injection test — tool_scoping.md

## Document under test
`kb/architecture/tool_scoping.md`

## Why this test is critical
tool_scoping.md is the first document loaded at every session start (step 1). If the agent cannot derive correct tool routing from this document alone, every database query is at risk of using the wrong tool or dialect.

---

## Test questions

### Question 1
"A user asks a question that requires customer purchase data from PostgreSQL and support ticket counts from MongoDB. Which tools do I call, what dialect does each use, how do I combine the results, and what is the most important rule about cross-database queries?"

Required concepts:
- Call query_db for PostgreSQL using standard SQL dialect
- Call query_db for MongoDB using aggregation pipeline JSON not SQL syntax
- Use execute_python to merge the two result sets in Python
- Do NOT attempt cross-database joins at the SQL level and route sub-queries to each database separately

Forbidden contradictions:
- Stating to use SQL syntax for MongoDB
- Stating to use a single cross-database join at the SQL level
- Stating to use execute_python to run database queries

---

### Question 2
"A query against MongoDB returns zero rows. What does a zero-row result mean, what specific causes should I investigate, and what is the correct sequence of actions according to the zero-row rule?"

Required concepts:
- Do not return the zero-row result to the user
- Do not call return_answer with the zero-row result
- A zero-row result is a failure signal not an answer
- Investigate the cause by checking join key format mismatches across databases
- Check whether the correct query dialect was used such as SQL syntax sent to MongoDB
- Adjust the approach and retry using execute_python to merge results from separate database calls
- Only call return_answer after the retried result is verified and non-suspicious

Forbidden contradictions:
- Stating to return the zero-row result as the answer
- Stating to call return_answer with the zero-row result

---

### Question 3
"What is the tool scoping philosophy, what specific tool usage prohibitions does it impose, and why does the agent use separate database tools instead of one general query tool?"

Required concepts:
- Each tool has a single tight responsibility
- A tool that does one thing precisely is more reliable than a tool handling multiple database types in one call
- Never use execute_python to run database queries and never use query_db to do data transformation
- Overlap between tools causes agent confusion and harder-to-diagnose failures

Forbidden contradictions:
- Stating that one general tool is preferred
- Stating that execute_python should be used for database queries

---

### Question 4
"What are the four agent tools available in every session and when should each be used?"

Required concepts:
- query_db executes read-only queries against any configured database for primary data retrieval
- list_db lists available databases and their tables or collections for schema discovery
- execute_python runs Python code in a Docker sandbox for data transformation and cross-DB result merging
- return_answer terminates the agent loop and records the final answer only when the answer is verified and complete

Forbidden contradictions:
- Stating that execute_python should be used for database queries
- Stating that return_answer can be called with an unverified result

---

### Question 5
"What query dialect and special syntax considerations apply to SQLite versus DuckDB?"

Required concepts:
- SQLite uses SQLite SQL dialect
- SQLite has no JSON operators and must use json_extract instead
- SQLite has no ILIKE and must use LOWER col LIKE LOWER pattern instead
- DuckDB uses analytical SQL with DuckDB extensions
- DuckDB supports UNNEST LIST_AGG STRUCT and columnar functions
- Do not use PostgreSQL-specific syntax in DuckDB

Forbidden contradictions:
- Stating that SQLite supports JSON operators like arrow notation
- Stating that SQLite supports ILIKE
- Stating to use PostgreSQL syntax in DuckDB

## Test result

**Run timestamp:** 2026-04-11 17:47 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/architecture/tool_scoping.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** A user asks a question that requires customer purchase data from PostgreSQL and support ticket counts from MongoDB. Which tools do I call, what dialect does each use, how do I combine the results, and what is the most important rule about cross-database queries?

**Concepts found (4/4):**
  - [x] Call query_db for PostgreSQL using standard SQL dialect
  - [x] Call query_db for MongoDB using aggregation pipeline JSON not SQL syntax
  - [x] Use execute_python to merge the two result sets in Python
  - [x] Do NOT attempt cross-database joins at the SQL level and route sub-queries to each database separately

**Actual answer:**
1.  Call `query_db` for the PostgreSQL purchase data. It uses Standard SQL (PostgreSQL 17.9) as its query dialect.
2.  Call `query_db` for the MongoDB support ticket counts. It uses MongoDB aggregation pipeline JSON as its query dialect.
3.  Use `execute_python` to merge the two result sets in Python.
4.  The most important rule about cross-database queries is: Do NOT attempt cross-database joins at the SQL level.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, resulting in a perfect score.

---

### Question 2 — PASS (100/100)

**Question:** A query against MongoDB returns zero rows. What does a zero-row result mean, what specific causes should I investigate, and what is the correct sequence of actions according to the zero-row rule?

**Concepts found (7/7):**
  - [x] Do not return the zero-row result to the user
  - [x] Do not call return_answer with the zero-row result
  - [x] A zero-row result is a failure signal not an answer
  - [x] Investigate the cause by checking join key format mismatches across databases
  - [x] Check whether the correct query dialect was used such as SQL syntax sent to MongoDB
  - [x] Adjust the approach and retry using execute_python to merge results from separate database calls
  - [x] Only call return_answer after the retried result is verified and non-suspicious

**Actual answer:**
A zero-row result is a failure signal, not an answer. You should investigate the following potential causes: check whether join keys have different formats across databases, and check whether the correct database tool was called for the database type (e.g. SQL syntax was incorrectly sent to MongoDB).

The correct sequence of actions is:
1. Do not return the zero-row result to the user and do not call `return_answer` with it.
2. Investigate the cause: check whether join keys have different formats across databases (e.g. integer in PostgreSQL vs "CUST-00123" string in MongoDB). Check whether the correct database tool was called for the database type (e.g. SQL syntax sent to MongoDB).
3. Adjust the approach — resolve the join key format mismatch or switch to the correct tool.
4. Retry using `execute_python` to merge results from separate database calls rather than attempting cross-database joins at the SQL level.
5. Only call `return_answer` after the retried result is verified and non-suspicious.

**Grader reasoning:** All required concepts are clearly present in the actual answer, and there are no forbidden contradictions.

---

### Question 3 — PASS (100/100)

**Question:** What is the tool scoping philosophy, what specific tool usage prohibitions does it impose, and why does the agent use separate database tools instead of one general query tool?

**Concepts found (4/4):**
  - [x] Each tool has a single tight responsibility
  - [x] Never use execute_python to run database queries and never use query_db to do data transformation
  - [x] A tool that does one thing precisely is more reliable than a tool handling multiple database types in one call
  - [x] Overlap between tools causes agent confusion and harder-to-diagnose failures

**Actual answer:**
According to the document, the tool scoping philosophy is that each tool has a single, tight responsibility.

Specific tool usage prohibitions it imposes are:
*   Never use `execute_python` to run database queries – use `query_db` for that.
*   Never use `query_db` to do data transformation – use `execute_python` for that.

The agent uses separate database tools because a tool that does one thing precisely is more reliable than a tool that tries to handle multiple database types in one call. Overlap between tools causes agent confusion and harder-to-diagnose failures.

**Grader reasoning:** All required concepts are present and there are no forbidden contradictions, therefore the score is 100.

---

### Question 4 — PASS (100/100)

**Question:** What are the four agent tools available in every session and when should each be used?

**Concepts found (4/4):**
  - [x] query_db executes read-only queries against any configured database for primary data retrieval
  - [x] list_db lists available databases and their tables or collections for schema discovery
  - [x] execute_python runs Python code in a Docker sandbox for data transformation and cross-DB result merging
  - [x] return_answer terminates the agent loop and records the final answer only when the answer is verified and complete

**Actual answer:**
The four agent tools available in every session are:

*   `query_db`: Used for primary data retrieval by executing read-only queries against any configured database.
*   `list_db`: Used for schema discovery at session start by listing available databases and their tables/collections.
*   `execute_python`: Used for data transformation and cross-DB result merging by running Python code in a Docker sandbox.
*   `return_answer`: Used when the answer is verified and complete to terminate the agent loop and record the final answer.

**Grader reasoning:** All required concepts are clearly present and no forbidden contradictions were found.

---

### Question 5 — PASS (100/100)

**Question:** What query dialect and special syntax considerations apply to SQLite versus DuckDB?

**Concepts found (6/6):**
  - [x] SQLite uses SQLite SQL dialect
  - [x] SQLite has no JSON operators and must use json_extract instead
  - [x] SQLite has no ILIKE and must use LOWER col LIKE LOWER pattern instead
  - [x] DuckDB uses analytical SQL with DuckDB extensions
  - [x] DuckDB supports UNNEST LIST_AGG STRUCT and columnar functions
  - [x] Do not use PostgreSQL-specific syntax in DuckDB

**Actual answer:**
SQLite: SQLite SQL dialect. No JSON operators — use `json_extract(column, '$.field')` instead. No `ILIKE` — use `LOWER(col) LIKE LOWER(?)`.
DuckDB: Analytical SQL with DuckDB extensions dialect. Supports `UNNEST`, `LIST_AGG`, `STRUCT`, and columnar functions. Use DuckDB-native functions — do not use PostgreSQL-specific syntax.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are present.

---
