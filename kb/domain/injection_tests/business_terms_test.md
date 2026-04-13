# Injection test — business_terms.md

## Document under test
`kb/domain/business_terms.md`

## Why this test is critical
business_terms.md is the domain glossary injected as Layer 5 (Institutional Knowledge) into the agent's context. If the agent cannot derive correct business term definitions from this document alone, it will apply wrong metric definitions — the single highest-frequency failure mode in DAB (FM2 + FM5). Every wrong definition produces a wrong answer that looks correct.

---

## Test questions

### Question 1
"A DAB query asks for the repeat purchase rate in a retail dataset. What is the correct definition of repeat purchase rate, and what is the common wrong assumption an agent would make?"

Required concepts:
- Repeat purchase rate is customers with two or more purchases divided by total unique customers in the same time window
- It is a ratio of customers not a ratio of transactions
- The common wrong assumption is total purchases divided by total customers
- A time window must be specified or verified before computing

Forbidden contradictions:
- Stating that repeat purchase rate is total purchases divided by total customers
- Stating that it counts transactions rather than customers

---

### Question 2
"A query references BRCA patients in the PANCANCER Atlas dataset. What does BRCA mean in this context, which database and column should be used to filter for BRCA patients, and what is the dangerous misinterpretation an agent could make?"

Required concepts:
- BRCA stands for Breast Invasive Carcinoma in the PANCANCER Atlas context
- Filter for BRCA patients using the disease type column in PostgreSQL
- The dangerous misinterpretation is confusing it with the BRCA gene

Forbidden contradictions:
- Stating that BRCA refers to the BRCA gene
- Stating that BRCA is filtered in the DuckDB molecular database

---

### Question 3
"A query asks for the latest release version of an NPM package in the Deps Dev dataset. How should the agent determine which version is the latest, what is the wrong approach, and which database holds GitHub star counts for packages?"

Required concepts:
- The latest release version is determined by the UpstreamPublishedAt date not by the version string
- The wrong approach is sorting by semantic version number to find the highest version
- GitHub stars are in the DuckDB project_database not in the SQLite package database

Forbidden contradictions:
- Stating that the latest version is the highest semantic version number
- Stating that version sorting determines the latest release

---

### Question 4
"A query asks about intraday volatility for stock indices in the Asia region. What is the correct formula for intraday volatility, which database holds the OHLC trade data, and where does the agent find which indices belong to the Asia region?"

Required concepts:
- Intraday volatility is calculated as High minus Low divided by Open for each trading day then averaged over the period
- Asia region is determined by the Exchange field in the SQLite index_info table
- The exchange names must be mapped to regions because Asia may not be stored literally as a value
- Trade data with OHLC values is in DuckDB not SQLite

Forbidden contradictions:
- Stating that intraday volatility is the standard deviation of closing prices
- Stating that the region is stored directly in the trade data

---

### Question 5
"A query asks about the category of articles and the region of publication in the AG News dataset. Which database holds each piece of information, what are the only valid category values, is a cross-database join required, and what key is used for that join?"

Required concepts:
- Category is stored in the MongoDB articles collection with exactly four valid values Sports Business Science/Technology and World
- Region is stored in the SQLite article_metadata table not in MongoDB
- A cross-database join on article_id is required to combine category and region data
- The agent should not assume other categories exist beyond the four listed

Forbidden contradictions:
- Stating that region is stored in MongoDB
- Stating that category is stored in SQLite
- Listing categories other than Sports Business Science/Technology and World

---

## Test result

**Run timestamp:** 2026-04-13 12:11 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/domain/business_terms.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** A DAB query asks for the repeat purchase rate in a retail dataset. What is the correct definition of repeat purchase rate, and what is the common wrong assumption an agent would make?

**Concepts found (4/4):**
  - [x] Repeat purchase rate is customers with two or more purchases divided by total unique customers in the same time window
  - [x] It is a ratio of customers not a ratio of transactions
  - [x] The common wrong assumption is total purchases divided by total customers
  - [x] A time window must be specified or verified before computing

**Actual answer:**
According to the document, the correct definition of repeat purchase rate is:

(Customers with >=2 purchases in time window) / (Total unique customers in same window). Ratio of customers, not transactions. CRITICAL: Always verify the time window before computing.

The common wrong assumption is:

Total purchases / total customers

**Grader reasoning:** The answer includes all required concepts and does not contain any forbidden contradictions.

---

### Question 2 — PASS (100/100)

**Question:** A query references BRCA patients in the PANCANCER Atlas dataset. What does BRCA mean in this context, which database and column should be used to filter for BRCA patients, and what is the dangerous misinterpretation an agent could make?

**Concepts found (3/3):**
  - [x] BRCA stands for Breast Invasive Carcinoma in the PANCANCER Atlas context
  - [x] Filter for BRCA patients using the disease type column in PostgreSQL
  - [x] The dangerous misinterpretation is confusing it with the BRCA gene

**Actual answer:**
Based solely on the provided document:

*   **Meaning:** BRCA stands for Breast Invasive Carcinoma.
*   **Database and Column:** The `disease_type` column in the PostgreSQL clinical data table should be used to filter for BRCA patients.
*   **Dangerous Misinterpretation:** Confusing BRCA with the BRCA gene.

**Grader reasoning:** All required concepts are present and there are no contradictions.

---

### Question 3 — PASS (100/100)

**Question:** A query asks for the latest release version of an NPM package in the Deps Dev dataset. How should the agent determine which version is the latest, what is the wrong approach, and which database holds GitHub star counts for packages?

**Concepts found (3/3):**
  - [x] The latest release version is determined by the UpstreamPublishedAt date not by the version string
  - [x] The wrong approach is sorting by semantic version number to find the highest version
  - [x] GitHub stars are in the DuckDB project_database not in the SQLite package database

**Actual answer:**
*   **Correct way to determine the latest release version:** Sort by the `UpstreamPublishedAt` date.
*   **Wrong approach:** Sorting by the highest semantic version number.
*   **Database holding GitHub star counts for packages:** DuckDB `project_database`.

**Grader reasoning:** All required concepts are present and there are no contradictions, resulting in a perfect score.

---

### Question 4 — PASS (100/100)

**Question:** A query asks about intraday volatility for stock indices in the Asia region. What is the correct formula for intraday volatility, which database holds the OHLC trade data, and where does the agent find which indices belong to the Asia region?

**Concepts found (4/4):**
  - [x] Intraday volatility is calculated as High minus Low divided by Open for each trading day then averaged over the period
  - [x] Asia region is determined by the Exchange field in the SQLite index_info table
  - [x] The exchange names must be mapped to regions because Asia may not be stored literally as a value
  - [x] Trade data with OHLC values is in DuckDB not SQLite

**Actual answer:**
Here's the answer based on the provided document:

*   **Intraday volatility formula:** (High - Low) / Open for each trading day, averaged over the requested period.
*   **Database for OHLC trade data:** DuckDB.
*   **Location of Asia region indices:** Determined by the `Exchange` field in the SQLite `index_info` table. The agent needs to map exchange names to regions, as "Asia" may not be stored literally as a value.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, so the score is 100.

---

### Question 5 — PASS (100/100)

**Question:** A query asks about the category of articles and the region of publication in the AG News dataset. Which database holds each piece of information, what are the only valid category values, is a cross-database join required, and what key is used for that join?

**Concepts found (4/4):**
  - [x] Category is stored in the MongoDB articles collection with exactly four valid values Sports Business Science/Technology and World
  - [x] Region is stored in the SQLite article_metadata table not in MongoDB
  - [x] A cross-database join on article_id is required to combine category and region data
  - [x] The agent should not assume other categories exist beyond the four listed

**Actual answer:**
*   **Category Database:** MongoDB `articles` collection
*   **Region Database:** SQLite `article_metadata` table
*   **Valid Category Values:** Sports, Business, Science/Technology, and World
*   **Cross-Database Join Required:** Yes
*   **Join Key:** `article_id`

**Grader reasoning:** All required concepts are present and no forbidden contradictions are present, resulting in a perfect score.

---
