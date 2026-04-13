# Injection test — schemas.md

## Document under test
`kb/domain/schemas.md`

## Why this test is critical
schemas.md documents what columns MEAN in business context — not just their data types. If the agent cannot derive correct column semantics from this document alone, it will select the wrong column for a query (FM1, FM3), join on the wrong field, or misinterpret a column's business meaning. Raw schema introspection shows VARCHAR but this file tells the agent what that VARCHAR actually contains.

---

## Test questions

### Question 1
"In the Google Local dataset, what is the difference between the name column in the PostgreSQL business_description table and the name column in the SQLite review table? Why is this distinction critical for joining?"

Required concepts:
- The name column in PostgreSQL business_description contains the business name
- The name column in SQLite review contains the reviewer name not the business name
- The correct join key between the two tables is gmap_id not name
- Confusing the two name columns would produce a wrong join and incorrect results

Forbidden contradictions:
- Stating that review.name contains the business name
- Stating that name is the correct join key between the two tables

---

### Question 2
"In the PANCANCER Atlas dataset, what is the difference between days_to_birth and age_at_initial_pathologic_diagnosis, how would you compute age from days_to_birth, which field should the agent prefer, and which database contains these clinical fields?"

Required concepts:
- days_to_birth is a negative integer representing days from birth to diagnosis
- To compute age from days_to_birth use the absolute value divided by 365.25
- age_at_initial_pathologic_diagnosis is the direct age field as an integer
- The agent should prefer age_at_initial_pathologic_diagnosis as it is the direct age field
- Clinical data including both fields is in PostgreSQL not DuckDB

Forbidden contradictions:
- Stating that days_to_birth is a positive number
- Stating that age data is in the DuckDB molecular database

---

### Question 3
"A query requires book review ratings and book category information from the Book Reviews dataset. Which database holds which information, what is the rating scale, is a cross-database join required, and what does the verified_purchase column in the review table actually mean?"

Required concepts:
- Book category and language information is in the PostgreSQL books table
- Review data including rating text and helpful_vote is in the SQLite review table
- The verified_purchase column indicates whether the reviewer actually purchased the book
- The rating scale is 1.0 to 5.0 per individual review not per book
- A cross-database join is required to combine book metadata with review data

Forbidden contradictions:
- Stating that book category is in the SQLite review table
- Stating that review ratings are in the PostgreSQL books table

---

### Question 4
"In the Deps Dev dataset, a query asks for the latest version of a package. Which column determines the latest version, what are the JSON-encoded columns that require special parsing and what does each contain, and which database type holds package data versus project data?"

Required concepts:
- The UpstreamPublishedAt column determines the latest version by publication date not the Version string
- The JSON-encoded columns requiring parsing are Licenses and Advisories and Links
- Licenses contains license identifiers as a JSON array and Advisories contains security advisory records as a JSON array
- Package data is in the SQLite packageinfo table and project data is in DuckDB

Forbidden contradictions:
- Stating that the Version column determines the latest release
- Stating that Licenses is a plain text field

---

### Question 5
"The Stock Market dataset has 2754 tables in DuckDB. What columns are in the SQLite stockinfo table, what does the ETF column mean, which column is an unstructured text field, what does DuckDB contain, and what is the authoritative source for resolving a company name to its ticker?"

Required concepts:
- The SQLite stockinfo table contains Symbol Listing Exchange Market Category ETF Nasdaq Traded and Company Description columns
- The ETF column indicates whether the security is an Exchange-Traded Fund and should be filtered out when querying individual stocks
- The authoritative source for resolving company name to ticker is the SQLite stockinfo table
- Company Description is an unstructured text field containing company business descriptions
- DuckDB contains per-ticker trade tables with OHLCV data

Forbidden contradictions:
- Stating that company name to ticker resolution happens in DuckDB
- Stating that ETFs should be included when querying individual stocks unless explicitly asked

---

## Test result

**Run timestamp:** 2026-04-13 12:11 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/domain/schemas.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** In the Google Local dataset, what is the difference between the name column in the PostgreSQL business_description table and the name column in the SQLite review table? Why is this distinction critical for joining?

**Concepts found (4/4):**
  - [x] The name column in PostgreSQL business_description contains the business name
  - [x] The name column in SQLite review contains the reviewer name not the business name
  - [x] The correct join key between the two tables is gmap_id not name
  - [x] Confusing the two name columns would produce a wrong join and incorrect results

**Actual answer:**
According to the document, in the Google Local dataset:

*   The `name` column in the PostgreSQL `business_description` table represents the **business name**.
*   The `name` column in the SQLite `review` table represents the **reviewer name**.

The distinction is critical for joining because joining the tables using the wrong `name` column would be incorrect. The correct join should be on `gmap_id` (the Google Maps unique ID) to link businesses to their reviews, not on the name of the business and name of the reviewer which would be incorrect.

**Grader reasoning:** The answer correctly identifies the content of each name column, the correct join key, and the problem with using the wrong name column for joining.

---

### Question 2 — PASS (100/100)

**Question:** In the PANCANCER Atlas dataset, what is the difference between days_to_birth and age_at_initial_pathologic_diagnosis, how would you compute age from days_to_birth, which field should the agent prefer, and which database contains these clinical fields?

**Concepts found (5/5):**
  - [x] days_to_birth is a negative integer representing days from birth to diagnosis
  - [x] To compute age from days_to_birth use the absolute value divided by 365.25
  - [x] age_at_initial_pathologic_diagnosis is the direct age field as an integer
  - [x] The agent should prefer age_at_initial_pathologic_diagnosis as it is the direct age field
  - [x] Clinical data including both fields is in PostgreSQL not DuckDB

**Actual answer:**
Based on the provided document for the PANCANCER Atlas dataset:

*   **Difference:** `days_to_birth` is the number of days from birth to diagnosis, represented as a negative integer. `age_at_initial_pathologic_diagnosis` is the patient's age at the time of diagnosis.
*   **Computation of Age from days_to_birth:** `Age = abs(days_to_birth) / 365.25`
*   **Preferred Field:** The agent should prefer `age_at_initial_pathologic_diagnosis` as it is a direct age field.
*   **Database:** These clinical fields are located in the PostgreSQL `clinical_info` table.

**Grader reasoning:** The answer contains all required concepts and no forbidden contradictions, so it receives a perfect score.

---

### Question 3 — PASS (100/100)

**Question:** A query requires book review ratings and book category information from the Book Reviews dataset. Which database holds which information, what is the rating scale, is a cross-database join required, and what does the verified_purchase column in the review table actually mean?

**Concepts found (5/5):**
  - [x] Book category and language information is in the PostgreSQL books table
  - [x] Review data including rating text and helpful_vote is in the SQLite review table
  - [x] The verified_purchase column indicates whether the reviewer actually purchased the book
  - [x] The rating scale is 1.0 to 5.0 per individual review not per book
  - [x] A cross-database join is required to combine book metadata with review data

**Actual answer:**
Based on the document:

*   **Review ratings:** SQLite (`review_query.db`)
*   **Book category:** PostgreSQL (`bookreview_db`)
*   **Rating scale:** 1.0 to 5.0
*   **Cross-database join required:** Yes
*   **verified_purchase meaning:** Whether the reviewer bought the book (1=verified, 0=not)

**Grader reasoning:** All required concepts are present and no contradictions are found.

---

### Question 4 — PASS (100/100)

**Question:** In the Deps Dev dataset, a query asks for the latest version of a package. Which column determines the latest version, what are the JSON-encoded columns that require special parsing and what does each contain, and which database type holds package data versus project data?

**Concepts found (4/4):**
  - [x] The UpstreamPublishedAt column determines the latest version by publication date not the Version string
  - [x] The JSON-encoded columns requiring parsing are Licenses and Advisories and Links
  - [x] Licenses contains license identifiers as a JSON array and Advisories contains security advisory records as a JSON array
  - [x] Package data is in the SQLite packageinfo table and project data is in DuckDB

**Actual answer:**
Based on the document:

*   The `UpstreamPublishedAt` column should be used to determine the latest version of a package. Sort by date, not by version string within the "Version" column.
*   The JSON-encoded columns are:
    *   `Licenses`: Contains license identifiers as a JSON array (e.g., `["MIT", "Apache-2.0"]`).
    *   `Advisories`: Contains security advisory records as a JSON array.
    *   `Links`: Contains URLs (homepage, repo) as a JSON structure.
*   Package data is in the SQLite `packageinfo` table, and project data is in DuckDB.

**Grader reasoning:** The response contains all required concepts and no contradictions.

---

### Question 5 — PASS (100/100)

**Question:** The Stock Market dataset has 2754 tables in DuckDB. What columns are in the SQLite stockinfo table, what does the ETF column mean, which column is an unstructured text field, what does DuckDB contain, and what is the authoritative source for resolving a company name to its ticker?

**Concepts found (5/5):**
  - [x] The SQLite stockinfo table contains Symbol Listing Exchange Market Category ETF Nasdaq Traded and Company Description columns
  - [x] The ETF column indicates whether the security is an Exchange-Traded Fund and should be filtered out when querying individual stocks
  - [x] The authoritative source for resolving company name to ticker is the SQLite stockinfo table
  - [x] Company Description is an unstructured text field containing company business descriptions
  - [x] DuckDB contains per-ticker trade tables with OHLCV data

**Actual answer:**
Here's the answer based solely on the provided document:

*   **Columns in the SQLite stockinfo table:** Nasdaq Traded, Symbol, Listing Exchange, Market Category, ETF, Round Lot Size, Test Issue, Financial Status, NextShares, and Company Description.

*   **Meaning of the ETF column:** Y/N - indicates whether the stock is an Exchange Traded Fund.

*   **Unstructured text field:** Company Description.

*   **What DuckDB contains:** Per-ticker trade tables with OHLCV data (date, open, high, low, close, adjusted_close, volume).

*   **Authoritative source for resolving a company name to its ticker:** The SQLite stockinfo table.

**Grader reasoning:** All required concepts are present, and no forbidden contradictions are found, thus earning a perfect score.

---
