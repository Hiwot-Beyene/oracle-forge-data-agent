# Injection test — join_key_glossary.md

## Document under test
`kb/domain/join_key_glossary.md`

## Why this test is critical
join_key_glossary.md documents how join keys differ across databases for each DAB dataset. If the agent cannot derive the correct join key format and normalization from this document alone, cross-database joins will return zero rows — a silent failure that produces wrong answers (FM4). This is DAB Hard Requirement 2.

---

## Test questions

### Question 1
"A query requires joining customer data from PostgreSQL (format CUST-00123) with MongoDB data (format 123). What should the agent do before attempting the join, what normalization steps should be applied, and what pandas code pattern resolves the format mismatch?"

Required concepts:
- Strip the non-numeric prefix using regex to remove characters like CUST-
- Cast the result to integer so both sides have the same type
- The pandas pattern is df column str replace with regex for non-digit characters then astype int
- Sample 5 values from each side before attempting the full join to verify the format

Forbidden contradictions:
- Stating to join without normalization
- Stating that the formats will match without any transformation

---

### Question 2
"A cross-database join between PostgreSQL business descriptions and SQLite reviews in the Google Local dataset returns zero rows. What is the correct join key, what is a dangerous wrong key to use, and what is the recovery protocol?"

Required concepts:
- The correct join key is gmap_id which exists in both PostgreSQL business_description and SQLite review tables
- The dangerous wrong key is name because review.name is the reviewer name not the business name
- The zero-row recovery protocol starts with sampling 5 values from each side of the join key
- Then check types to see if both are the same type string versus int
- Then check format for prefixes case differences whitespace and padding
- If still zero rows after normalization log to KB v3 and report LOW confidence

Forbidden contradictions:
- Stating to join on the name field
- Stating that review.name contains the business name

---

### Question 3
"The PANCANCER Atlas dataset requires joining data across two databases. What is the join key, what is its format, what format issue might occur between the databases, and how should the agent normalize it?"

Required concepts:
- The join key is patient_id or bcr_patient_barcode in TCGA barcode format TCGA-XX-XXXX
- A format issue may occur because TCGA barcodes can be 12-char versus 16-char between the two databases
- The normalization is to truncate both sides to the shared prefix length

Forbidden contradictions:
- Stating that both databases use the same barcode length without verification
- Stating that clinical data is in DuckDB

---

### Question 4
"The Stock Market dataset has stock metadata in SQLite and trade data in DuckDB with 2754 tables. How does the agent resolve a company name to its trade data, what specific column is the join key, and what is unusual about the DuckDB structure?"

Required concepts:
- Resolve the company name to a ticker symbol by querying the SQLite stockinfo table then query the matching DuckDB table by name
- The ticker symbol in stockinfo.Symbol is the join key that connects SQLite to DuckDB trade data
- The unusual structure is that DuckDB may have one table per ticker symbol resulting in 2754 separate tables

Forbidden contradictions:
- Stating that DuckDB has a single unified trade table
- Stating that the company name can be used directly to query DuckDB

---

### Question 5
"The CRM Arena Pro dataset has up to six databases. What are the databases, what join key format issue exists with Salesforce-style IDs, how should the agent handle the ID mismatch, and how should cross-DB results be combined?"

Required concepts:
- The six databases are SQLite core_crm and products_orders and territory plus DuckDB sales_pipeline and activities plus PostgreSQL support
- Salesforce IDs can be 15-char case-insensitive or 18-char case-sensitive format
- If there is a mismatch between 15-char and 18-char IDs use the first 15 characters as the case-insensitive portion
- Cross-DB joins require querying each database separately normalizing Salesforce-style IDs and merging stepwise in pandas

Forbidden contradictions:
- Stating that all six databases use the same ID format
- Stating to attempt SQL-level joins across the databases

---

## Test result

**Run timestamp:** 2026-04-13 12:11 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/domain/join_key_glossary.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** A query requires joining customer data from PostgreSQL (format CUST-00123) with MongoDB data (format 123). What should the agent do before attempting the join, what normalization steps should be applied, and what pandas code pattern resolves the format mismatch?

**Concepts found (4/4):**
  - [x] Strip the non-numeric prefix using regex to remove characters like CUST-
  - [x] Cast the result to integer so both sides have the same type
  - [x] The pandas pattern is df column str replace with regex for non-digit characters then astype int
  - [x] Sample 5 values from each side before attempting the full join to verify the format

**Actual answer:**
Here's how the agent should handle the customer data join based on the provided document:

**1. Before Attempting the Join:**

*   **Look up the dataset in the glossary:** While the exact customer dataset isn't named "customer data," the agent should look for a dataset involving both PostgreSQL and MongoDB (if available. None are available). Or use the General Normalization Patterns as the general guidelines indicates.
*   **Check the format of the join key in BOTH sources:** Verify the customer ID format in both PostgreSQL and MongoDB matches the described pattern (`CUST-00123` vs. `123`).
*   **Sample 5 values from each side:** Query PostgreSQL and MongoDB separately and extract five sample customer IDs from each resulting DataFrame. Use these samples to visually confirm the suspected format difference.

**2. Normalization Steps:**

*   **Normalization:** Use the "Prefixed ID" normalization pattern.

**3. Pandas Code Pattern:**

```python
# Strip prefix and cast
df['normalized_id'] = df['raw_id'].str.replace(r'^[A-Z]+-', '', regex=True).astype(int)
```

**Explanation:**

*   The code first uses `.str.replace(r'^[A-Z]+-', '', regex=True)` to remove the prefix `CUST-` from the customer IDs in the PostgreSQL data. The `regex=True` argument enables regular expression matching to handle any number of letters before the hyphen.
*   Then, `.astype(int)` converts the cleaned customer IDs to integers, ensuring that both sides of the join have the same data type.

**Grader reasoning:** All required concepts are present and no contradictions were found, so the score is 100.

---

### Question 2 — PASS (100/100)

**Question:** A cross-database join between PostgreSQL business descriptions and SQLite reviews in the Google Local dataset returns zero rows. What is the correct join key, what is a dangerous wrong key to use, and what is the recovery protocol?

**Concepts found (6/6):**
  - [x] The correct join key is gmap_id which exists in both PostgreSQL business_description and SQLite review tables
  - [x] The dangerous wrong key is name because review.name is the reviewer name not the business name
  - [x] The zero-row recovery protocol starts with sampling 5 values from each side of the join key
  - [x] Then check types to see if both are the same type string versus int
  - [x] Then check format for prefixes case differences whitespace and padding
  - [x] If still zero rows after normalization log to KB v3 and report LOW confidence

**Actual answer:**
Based on the document:

*   **Correct Join Key:** `gmap_id`
*   **Dangerous Wrong Key:** `name` (because `review.name` may be the reviewer's name, not the business name)
*   **Recovery Protocol:**
    1.  **Sample both sides:** Print 5 sample values of the join key from each DataFrame.
    2.  **Check types:** Are both the same type (string vs int)?
    3.  **Check format:** Look for prefixes, case differences, whitespace, padding.
    4.  **Check this glossary:** Is there a known normalization for this dataset?
    5.  **Apply normalization:** Use the pattern from this glossary (Verify — strip whitespace if needed).
    6.  **Retry once:** If still zero rows after normalization, log to KB v3 and report LOW confidence.
    7.  **Log the fix:** Record the normalization that worked in KB v3 for future runs.

**Grader reasoning:** All required concepts are present in the actual answer, and no forbidden contradictions are found, so the score is 100.

---

### Question 3 — PASS (100/100)

**Question:** The PANCANCER Atlas dataset requires joining data across two databases. What is the join key, what is its format, what format issue might occur between the databases, and how should the agent normalize it?

**Concepts found (3/3):**
  - [x] The join key is patient_id or bcr_patient_barcode in TCGA barcode format TCGA-XX-XXXX
  - [x] A format issue may occur because TCGA barcodes can be 12-char versus 16-char between the two databases
  - [x] The normalization is to truncate both sides to the shared prefix length

**Actual answer:**
According to the document:

*   **Join Key:** `patient_id` (or `bcr_patient_barcode`)
*   **Format:** TCGA barcode format: `TCGA-XX-XXXX`
*   **Format Issue:** TCGA barcodes can be 12-char versus 16-char.
*   **Normalization:** Truncate to shared prefix if needed.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are present, resulting in a score of 100.

---

### Question 4 — PASS (100/100)

**Question:** The Stock Market dataset has stock metadata in SQLite and trade data in DuckDB with 2754 tables. How does the agent resolve a company name to its trade data, what specific column is the join key, and what is unusual about the DuckDB structure?

**Concepts found (3/3):**
  - [x] Resolve the company name to a ticker symbol by querying the SQLite stockinfo table then query the matching DuckDB table by name
  - [x] The ticker symbol in stockinfo.Symbol is the join key that connects SQLite to DuckDB trade data
  - [x] The unusual structure is that DuckDB may have one table per ticker symbol resulting in 2754 separate tables

**Actual answer:**
Based on the document:

*   The agent resolves a company name to its trade data by **resolving the company name to a ticker symbol by querying the SQLite stockinfo table then query the matching DuckDB table by name**.
*   The specific column that is the join key is **`stockinfo.Symbol` (SQLite)**.
*   The unusual structure about the DuckDB database is that it **may have one table per ticker symbol resulting in 2754 separate tables**.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, so the score is 100.

---

### Question 5 — PASS (100/100)

**Question:** The CRM Arena Pro dataset has up to six databases. What are the databases, what join key format issue exists with Salesforce-style IDs, how should the agent handle the ID mismatch, and how should cross-DB results be combined?

**Concepts found (4/4):**
  - [x] The six databases are SQLite core_crm and products_orders and territory plus DuckDB sales_pipeline and activities plus PostgreSQL support
  - [x] Salesforce IDs can be 15-char case-insensitive or 18-char case-sensitive format
  - [x] If there is a mismatch between 15-char and 18-char IDs use the first 15 characters as the case-insensitive portion
  - [x] Cross-DB joins require querying each database separately normalizing Salesforce-style IDs and merging stepwise in pandas

**Actual answer:**
According to the document:

The CRM Arena Pro dataset has six databases: SQLite (core_crm, products_orders, and territory), DuckDB (sales_pipeline and activities), and PostgreSQL (support).

A format issue exists with Salesforce-style IDs: they can be 15-character (case-insensitive) or 18-character (case-sensitive).

If there is a mismatch between 15-char and 18-char IDs, the agent should use the first 15 characters as the case-insensitive portion.

Cross-DB results should be combined by querying each database separately, normalizing Salesforce-style IDs, and merging stepwise in pandas.

**Grader reasoning:** All required concepts are present and no forbidden contradictions were found, so the score is 100.

---
