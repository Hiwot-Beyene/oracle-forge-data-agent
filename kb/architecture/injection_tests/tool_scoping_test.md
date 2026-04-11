# Injection test — tool_scoping.md

## Document under test
`kb/architecture/tool_scoping.md`

## Why this test is critical
tool_scoping.md is the second mandatory document loaded at every session start. If the agent cannot derive correct tool routing from this document alone, every database query call will go to the wrong tool or use the wrong dialect.

---

## Test questions

### Question 1
"A query requires customer revenue from PostgreSQL and their support ticket count from MongoDB. Which tools do I call, in what order, and how do I combine the results?"

Required concepts:
- Call query_db for PostgreSQL revenue data
- Use standard SQL syntax for PostgreSQL
- Call query_db separately for MongoDB ticket count
- Use MongoDB aggregation pipeline syntax for MongoDB not SQL
- Call execute_python to merge the two result sets in Python
- Never attempt a cross-database join at the SQL level
- Sub-queries go to each database separately before merging

Forbidden contradictions:
- Stating to use SQL syntax for MongoDB
- Stating to join across databases at the query level
- Stating to use a different tool than query_db for database queries

---

### Question 2
"I need to query a DuckDB dataset. What query dialect do I use and what functions are available that differ from standard PostgreSQL SQL?"

Required concepts:
- Use analytical SQL with DuckDB extensions
- DuckDB supports UNNEST
- DuckDB supports LIST_AGG
- DuckDB supports STRUCT
- DuckDB supports columnar functions
- Do not use PostgreSQL-specific syntax in DuckDB
- Database file path is defined in the dataset db_config.yaml

Forbidden contradictions:
- Stating DuckDB uses MongoDB aggregation pipeline syntax
- Stating DuckDB uses identical syntax to PostgreSQL with no differences

---

### Question 3
"What is the purpose of the return_answer tool, when exactly should I use it, and what should I never do with it?"

Required concepts:
- return_answer terminates the agent loop
- return_answer records the final answer
- It is the last tool called in any successful agent run
- Use it only when the answer is verified and complete
- Do not call return_answer with an unverified or suspicious result

Forbidden contradictions:
- Stating return_answer executes database queries
- Stating return_answer can be called at any point during execution
- Stating return_answer is optional

---

### Question 4
"A query returns zero rows. According to the tool scoping document, what is the exact sequence of steps I must follow?"

Required concepts:
- Do not return the zero-row result to the user
- Do not call return_answer with the zero-row result
- Investigate the cause of the failure
- Check whether join keys have different formats across databases
- Check whether the correct database tool was called for the database type
- Adjust the approach and resolve the identified cause
- Use execute_python to merge results from separate database calls rather than attempting cross-database joins
- Only call return_answer after the retried result is verified and non-suspicious

Forbidden contradictions:
- Stating to return the zero-row result as the final answer
- Stating cross-database SQL joins are acceptable
- Stating return_answer should be called immediately after zero rows

---

## Test result

**Run timestamp:** 2026-04-11 12:29 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/tool_scoping.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** A query requires customer revenue from PostgreSQL and their support ticket count from MongoDB. Which tools do I call, in what order, and how do I combine the results?

**Concepts found (7/7):**
  - [x] Call query_db for PostgreSQL revenue data
  - [x] Use standard SQL syntax for PostgreSQL
  - [x] Call query_db separately for MongoDB ticket count
  - [x] Use MongoDB aggregation pipeline syntax for MongoDB not SQL
  - [x] Call execute_python to merge the two result sets in Python
  - [x] Never attempt a cross-database join at the SQL level
  - [x] Sub-queries go to each database separately before merging

**Actual answer:**
Based on the document, here's the correct approach for this cross-database query:

**Tools to call and order:**

1. **`query_db`** - Get customer revenue from PostgreSQL
   - Use standard SQL (PostgreSQL 17.9) syntax
   - Query the revenue data from the appropriate tables

2. **`query_db`** - Get support ticket count from MongoDB  
   - Use MongoDB aggregation pipeline JSON syntax (NOT SQL)
   - Structure as pipeline arrays: `[{"$match": {...}}, {"$group": {...}}]`

3. **`execute_python`** - Merge the results
   - Fetch results from both database calls into Python variables
   - Perform the data merging/joining in Python code
   - Handle any join key format differences (e.g., integer IDs in PostgreSQL vs string IDs in MongoDB)

4. **`return_answer`** - Return the final merged result
   - Only call this after verifying the result is complete and non-suspicious

**Key points:**
- Do NOT attempt cross-database joins at the SQL level
- Use separate `query_db` calls for each database type with their respective query dialects
- Always merge results using `execute_python` rather than trying to join across databases in SQL
- Never use `execute_python` to run database queries - only use it for data transformation and merging

**Grader reasoning:** All seven required concepts are clearly present and no forbidden contradictions were found in the answer.

---

### Question 2 — PASS (100/100)

**Question:** I need to query a DuckDB dataset. What query dialect do I use and what functions are available that differ from standard PostgreSQL SQL?

**Concepts found (7/7):**
  - [x] Use analytical SQL with DuckDB extensions
  - [x] DuckDB supports UNNEST
  - [x] DuckDB supports LIST_AGG
  - [x] DuckDB supports STRUCT
  - [x] DuckDB supports columnar functions
  - [x] Do not use PostgreSQL-specific syntax in DuckDB
  - [x] Database file path is defined in the dataset db_config.yaml

**Actual answer:**
Based on the document, for querying a DuckDB dataset:

**Query dialect:** Analytical SQL with DuckDB extensions

**Tool to use:** `query_db`

**Functions available that differ from standard PostgreSQL SQL:**
- `UNNEST`
- `LIST_AGG` 
- `STRUCT`
- Columnar functions (specific functions not detailed in the document)

**Additional notes:**
- DuckDB is efficient for aggregations over large datasets
- It's file-based with no server required
- The database file path is defined in db_config.yaml
- You should use DuckDB-native functions and NOT use PostgreSQL-specific syntax

The document emphasizes using DuckDB's native analytical capabilities rather than trying to apply PostgreSQL syntax.

**Grader reasoning:** All seven required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---

### Question 3 — PASS (100/100)

**Question:** What is the purpose of the return_answer tool, when exactly should I use it, and what should I never do with it?

**Concepts found (5/5):**
  - [x] return_answer terminates the agent loop
  - [x] return_answer records the final answer
  - [x] It is the last tool called in any successful agent run
  - [x] Use it only when the answer is verified and complete
  - [x] Do not call return_answer with an unverified or suspicious result

**Actual answer:**
Based on the document, here is the information about the `return_answer` tool:

## Purpose
The `return_answer` tool is used to "terminate the agent loop and record the final answer." It is described as "the last tool called in any successful agent run."

## When exactly to use it
- Only when "the answer is verified and complete"
- After you have a verified and non-suspicious result
- As the final step in a successful agent execution

## What you should never do with it
- **Never call it with an unverified or suspicious result**
- **Never call it with zero-row results** - the document explicitly states "Do not call `return_answer` with the zero-row result" because "A zero-row result is a failure signal, not an answer"
- **Never return zero-row results to the user** - you must investigate and retry first

The document emphasizes that if you get zero rows or suspicious results, you should investigate the cause, adjust your approach, retry (potentially using `execute_python` to merge results from separate database calls), and only call `return_answer` after the retried result is verified and non-suspicious.

**Grader reasoning:** All five required concepts are clearly present in the actual answer with no forbidden contradictions found.

---

### Question 4 — PASS (100/100)

**Question:** A query returns zero rows. According to the tool scoping document, what is the exact sequence of steps I must follow?

**Concepts found (8/8):**
  - [x] Do not return the zero-row result to the user
  - [x] Do not call return_answer with the zero-row result
  - [x] Investigate the cause of the failure
  - [x] Check whether join keys have different formats across databases
  - [x] Check whether the correct database tool was called for the database type
  - [x] Adjust the approach and resolve the identified cause
  - [x] Use execute_python to merge results from separate database calls rather than attempting cross-database joins
  - [x] Only call return_answer after the retried result is verified and non-suspicious

**Actual answer:**
According to the tool scoping document, when a query returns zero rows, the exact sequence of steps you must follow is:

1. **Do not return the zero-row result to the user and do not call `return_answer` with it.**

2. **Investigate the cause:** check whether join keys have different formats across databases (e.g. integer in PostgreSQL vs "CUST-00123" string in MongoDB). Check whether the correct database tool was called for the database type (e.g. SQL syntax sent to MongoDB).

3. **Adjust the approach** — resolve the join key format mismatch or switch to the correct tool.

4. **Retry using `execute_python` to merge results from separate database calls** rather than attempting cross-database joins at the SQL level.

5. **Only call `return_answer` after the retried result is verified and non-suspicious.**

The document emphasizes that a zero-row result is a failure signal, not an answer, and must not be returned to the user or passed to `return_answer`.

**Grader reasoning:** All required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---
