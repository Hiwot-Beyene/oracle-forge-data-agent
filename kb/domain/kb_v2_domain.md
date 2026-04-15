# kb/domain/kb_v2_domain.md

# KB v2 — Domain Knowledge Base

_The Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.5 — Full paper alignment (arxiv 2603.20576). Model comparison, exploration ratio, Patents unsolved, FM4 extraction hierarchy added._

---

## SECTION A: DataAgentBench (DAB) Overview

_Source: arxiv.org/abs/2603.20576 — UC Berkeley EPIC + PromptQL Hasura, March 2026_

### Benchmark Facts

- **54 queries** across **12 datasets**, **9 domains**, **4 database systems**
- Domains: news articles, e-commerce, CRM/sales, software engineering, local business, music, financial markets, medical research, patents/IP
- Database systems: PostgreSQL, MongoDB, SQLite, DuckDB — **often multiple in the same query**
- Property distribution: all 54 require multi-DB; 47/54 require text transformation; 26/54 have ill-formatted join keys; 30/54 need domain knowledge
- **50 trials per query** to measure both pass@1 and pass@k accuracy
- **1,147 annotated trajectories** analyzed for failure mode classification
- Best pass@50: **69%** — agents CAN solve more queries given enough attempts, proving the bottleneck is reliability not capability
- **Patents dataset: completely unsolved** — 0% pass@1 across ALL models and ALL trials

### Model Comparison (Paper Table 3 — 50 trials/query)

| Model | pass@1 | pass@50 | Total Cost | Cost per 1% Accuracy |
|-------|--------|---------|------------|---------------------|
| Gemini-3-Pro | **38%** | 69% | $1,355 | $35.66 |
| GPT-5.2 | 36% | 67% | $1,089 | $30.25 |
| Gemini-2.5-Flash | 33% | 63% | $83 | $2.52 |
| GPT-5-mini | 30% | 56% | **$67** | $2.23 |
| Kimi-K2 | 28% | 54% | $146 | $5.21 |

**Cost-efficiency insight:** GPT-5-mini achieves 30% at $67 total. Gemini-3-Pro costs 20x more ($1,355) for only 8% more accuracy. For development iterations, use a cheap model; reserve expensive models for final benchmark runs.

### Scaffolded Systems (Paper Table 7)

| System | pass@1 | Key Advantage |
|--------|--------|---------------|
| PromptQL + Gemini-3.1-Pro | **54.3%** | Semantic layer + metadata curation |
| PromptQL + Claude-Opus-4.6 | 50.8% | Same scaffold, different model |
| ReAct baseline + Claude-Opus-4.6 | 44% | No semantic layer |
| Frontier model (no scaffold) | ~38% | Raw model capability |

The gap between 38% (no scaffold) and 54% (PromptQL) is the **"engineering gap"** we close with context engineering.

### Why the Gap Exists

The 38% ceiling is not a model capability problem. It is a context problem. Agents fail because:

1. They cannot find the right table across systems
2. They do not know what business terms mean in this specific dataset
3. They cannot resolve inconsistent join keys across databases
4. They have no memory of prior corrections

---

## SECTION B: The Four Hard Requirements — Technical Breakdown

### Hard Requirement 1 — Multi-Database Integration

**What it means:** A single query may require data from PostgreSQL AND MongoDB AND SQLite in the same session.

**What must work:**

- Query routing: agent must identify which database holds which data
- Dialect switching: SQL (PostgreSQL/SQLite) vs. MongoDB aggregation pipelines vs. DuckDB analytical SQL
- Result merging: combine outputs from different systems into a single coherent answer

**Known failure pattern:** Agent defaults to SQL syntax when hitting MongoDB → query fails silently or returns wrong result.

**Fix pattern:** Explicit DB-type detection in agent system prompt. For each tool call, prepend DB type. Example routing logic:

```
IF entity is in transactions     → PostgreSQL
IF entity is in product_reviews  → MongoDB
IF entity is in lookup_tables    → SQLite
IF entity is analytical-heavy    → DuckDB
```

**Agent system prompt injection (add to AGENT.md):**

```
When querying data, first identify the database system hosting the target table.
Use SQL syntax ONLY for PostgreSQL, SQLite, DuckDB.
Use MongoDB aggregation pipeline syntax for MongoDB collections.
Never assume all tables are in the same database.
```

---

### Hard Requirement 2 — Ill-Formatted Join Keys

**What it means:** The same entity (customer, product) is represented differently across databases.

**Common patterns observed in DAB:**

| Entity       | DB A format   | DB B format | Resolution                                  |
| ------------ | ------------- | ----------- | ------------------------------------------- |
| Customer ID  | `CUST-00123`  | `123`       | Strip prefix, zero-pad                      |
| Product code | `SKU_ABC_001` | `ABC-001`   | Remove prefix, replace underscore with dash |
| Phone number | `+1-555-0100` | `5550100`   | Strip country code and separators           |
| Date         | `2024-01-15`  | `20240115`  | Cast to integer or parse                    |

**Agent instruction template:**

```
Before joining tables across databases, inspect sample values from both join key columns.
If formats differ, apply normalization:
- Strip non-numeric prefixes (CUST-, SKU_, etc.)
- Normalize phone numbers to digits only
- Cast dates to consistent format
Log the normalization applied to KB v3.
```

**Shared utility:** `join_key_resolver` in `utils/oracle_forge_utils.py`

---

### Hard Requirement 3 — Unstructured Text Transformation

**What it means:** Some queries require extracting structured facts from free-text fields.

**Examples from DAB domains:**

- Telecom: extract complaint category from free-text support notes
- Healthcare: extract diagnosis codes from clinical notes
- Retail: extract sentiment/product attributes from reviews

**Connection to Week 3:** The extraction pipeline from Week 3 (Document Intelligence Refinery) should be wrapped as a reusable tool here.

**Approach:**

1. Identify unstructured fields in schema introspection
2. Sample values to understand format
3. Apply LLM extraction with structured output schema
4. Join extracted data back to the main query

**Agent instruction template:**

```
If a query requires information buried in a text field (notes, descriptions, comments):
1. Sample 10 values from the field to understand content
2. Write an extraction prompt for the specific information needed
3. Apply extraction to relevant rows
4. Store structured result in a temporary table or variable
5. Use structured result in the main query
```

---

### Hard Requirement 4 — Domain Knowledge

**What it means:** Correct answers require knowing things that are NOT in the schema.

**DAB domain term glossary (seed — expand as you discover more):**

| Term                  | Domain          | Correct Definition                                                                    | Common Wrong Assumption                     |
| --------------------- | --------------- | ------------------------------------------------------------------------------------- | ------------------------------------------- |
| Churn                 | Telecom/SaaS    | Customer who cancelled or became inactive (dataset-specific — always verify)          | Any customer who didn't purchase this month |
| Active account        | Finance/Telecom | Status code = specific values (dataset-specific). Never infer from field name         | Any account with status != 'closed'         |
| Repeat purchase rate  | Retail          | Customers with ≥2 purchases / total customers, in time window                         | Total purchases / total customers           |
| Pass@1                | Benchmarking    | Fraction of queries correct on the first attempt (single trial)                       | Average accuracy across all trials          |
| Fiscal year           | Finance         | May NOT be Jan-Dec. Always verify fiscal year boundaries before applying time filters | Calendar year Jan 1 – Dec 31                |
| Support ticket volume | CRM             | Count of tickets opened in period — clarify if resolved/unresolved matters            | Simple count of all ticket rows             |

**Agent instruction template:**

```
Before using any business metric in a query:
1. Check the KB domain glossary for the correct definition
2. If not in KB, add a sub-query to inspect sample data and infer the definition
3. State the definition assumed in your answer so it can be verified
4. Log new definitions discovered to KB v3
```

---

## SECTION C: Database-Specific Query Patterns

### PostgreSQL

```sql
-- Schema introspection
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public' ORDER BY table_name;

-- Sample values for join key inspection
SELECT customer_id FROM table_name LIMIT 5;

-- Ill-formatted key normalization example
SELECT REGEXP_REPLACE(customer_id, '[^0-9]', '', 'g')::int AS normalized_id
FROM transactions;
```

### MongoDB (Aggregation Pipeline)

```javascript
// Schema inference (sample documents)
db.collection.findOne();

// Aggregation with filter
db.support_tickets.aggregate([
  { $match: { status: "open" } },
  { $project: { customer_id: 1, notes: 1 } },
  { $limit: 10 },
]);

// Key normalization in pipeline
db.collection.aggregate([
  {
    $addFields: {
      normalized_id: {
        $toLower: {
          $replaceAll: {
            input: "$customer_id",
            find: "CUST-",
            replacement: "",
          },
        },
      },
    },
  },
]);
```

### SQLite

```sql
-- Schema introspection
SELECT name, sql FROM sqlite_master WHERE type='table';
PRAGMA table_info(table_name);
```

### DuckDB

```sql
-- Schema introspection
DESCRIBE table_name;
SHOW TABLES;

-- Read from multiple file types
SELECT * FROM 'data/*.parquet';
SELECT * FROM 'data/*.csv';

-- Analytical aggregations (DuckDB strength)
SELECT date_trunc('quarter', date_col) as quarter,
       COUNT(DISTINCT customer_id) as unique_customers
FROM transactions
GROUP BY 1 ORDER BY 1;
```

---

## SECTION D: Cross-Database Join Pattern

**Standard pattern for joining data across two DB systems:**

```python
# Step 1: Query each DB separately
result_pg    = query_postgresql("SELECT customer_id, purchase_count FROM transactions")
result_mongo = query_mongodb("support_tickets", pipeline)

# Step 2: Normalize join keys
result_pg['normalized_id']    = result_pg['customer_id'].str.replace('CUST-', '').astype(int)
result_mongo['normalized_id'] = result_mongo['customer_id'].str.replace('C', '').astype(int)

# Step 3: Merge in Python/pandas
merged = result_pg.merge(result_mongo, on='normalized_id', how='left')

# Step 4: Log the normalization applied
log_to_corrections(
    "customer_id join: PG format CUST-XXXX, Mongo format CXXXX. Strip prefix, cast to int."
)
```

---

## SECTION E: Known DAB Failure Modes (from paper Section 3.3, n=1,147 annotated trajectories)

**Key statistic: 85% of incorrect answers are FM2 + FM4. Agents usually find the right data — they fail at planning or implementing.**

| FM Code | Paper Definition | % of Failures | Description |
| ------- | ---------------- | ------------- | ----------- |
| FM1 | Fails before planning | varies | Agent makes no attempt. Returns null tool-call (Gemini-2.5-Flash: 63.4%) or refuses ("I cannot join across databases"). |
| FM2 | Incorrect plan | ~40% | Logical plan is wrong — even perfect execution cannot produce correct answer. E.g., averaging per-book ratings then averaging across books instead of averaging all reviews directly. |
| FM3 | Incorrect data selection | ~15% | Correct plan but wrong table/column chosen. E.g., checking `description` for language when it is in `details`. |
| FM4 | Incorrect implementation | ~45% | Correct plan + correct data, but code is wrong. Dominant sub-pattern: regex-only text extraction (see below). |
| FM5 | Runtime error | rare | API failures, token limits, timeouts, 100-call limit. Rare except for Kimi-K2 (6.6%). |

**FM4 critical sub-pattern — regex-only text extraction:**
All tested agents use regex exclusively for extracting structured values from free text. None attempt NLP, NER, dateutil, or LLM-based extraction. This causes:
- **0% pass@1 on patents** — regex cannot parse "dated 5th March 2019" or "March the 18th, 2019"
- **PANCANCER gender misclassification** — regex `MALE` matches inside `FEMALE`
- **bookreview year errors** — year-extraction regex matches ISBN segments

**Paper recommendation:** Expose dedicated extraction tools (date parsers, NER taggers, LLM-based extraction) alongside SQL and Python execution.

### Completely Unsolved Datasets

| Dataset | pass@1 (best model) | Why It Fails |
|---------|---------------------|--------------|
| **Patents** | **0%** across all models, all trials | Date extraction from >20 variant formats; CPC hierarchy navigation; 5GB SQLite file requires efficient filtered queries |
| stockindex (partial) | Very low | Exchange-to-region mapping not in schema; requires domain knowledge |

**Patents** is the single hardest dataset in DAB. Any agent that solves even 1 Patents query would be a novel research contribution.

---

## SECTION F: Tool Usage Balance (Paper Section 3.2)

**Key finding:** Across all models, **~20% of tool calls are exploration** (schema inspection, sampling, listing tables). Deviation in either direction hurts performance.

| Exploration Ratio | Effect |
|-------------------|--------|
| <15% | Agent dives into queries without understanding schema → FM3 (wrong data source) |
| ~20% | **Optimal** — enough exploration to find right tables, then efficient execution |
| >30% | Agent wastes token budget on exploration, runs out of iterations before answering |

**Practical rules for the agent:**
1. **First 2-3 tool calls** of any query should be `list_db` or schema introspection — understand what tables exist and what columns they have
2. **Sample 5 values** from join key columns before any cross-DB join (catches format mismatches early)
3. **Stop exploring** once you have identified the target tables and confirmed column names — execute the query
4. **Budget:** aim for 3-5 exploration calls out of every 15-20 total calls per query

---

## SECTION G: Agent Context File Template (AGENT.md seed)

```markdown
# Data Agent Context

## Connected Databases

- PostgreSQL: [host/db] — contains: transactions, customers, orders
- MongoDB: [host/db] — contains: support_tickets, product_reviews
- SQLite: [path] — contains: lookup tables, reference data
- DuckDB: [path] — contains: analytical datasets, parquet files

## Database Routing Rules

[Populated by schema introspection tool at startup]

## Key Business Definitions

[Populated from KB v2 domain glossary]

## Known Join Key Formats

[Populated from KB v2 ill-formatted key table + v3 corrections log]

## Self-Correction Rules

1. If a query returns zero rows, STOP and inspect join keys before retrying
2. If a query returns unexpected nulls, check DB dialect compatibility
3. If a business term is ambiguous, check KB before assuming
4. Log every failure and fix to KB v3

## Response Format

Always include: query used, database queried, any normalization applied, confidence level
```

---

_CHANGELOG: v1.5 updated April 14 2026. Paper alignment: (1) Added model comparison table with costs (Paper Table 3). (2) Added scaffolded systems comparison (Paper Table 7). (3) Added exploration ratio ~20% optimal (Paper Section 3.2). (4) Added Patents completely unsolved finding. (5) Added pass@50 = 69% and 1,147 trajectory count. (6) Renumbered sections: new Section F (Tool Usage Balance), old Section F → Section G._
_TODO for Drivers: fill in actual DB connection strings; update routing table after schema introspection tool runs; add discovered domain terms to Section D glossary._
