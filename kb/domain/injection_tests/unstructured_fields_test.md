# Injection test — unstructured_fields.md

## Document under test
`kb/domain/unstructured_fields.md`

## Why this test is critical
unstructured_fields.md is the inventory of all free-text and semi-structured fields across DAB datasets. DAB Hard Requirement 3 (Unstructured Text Transformation) explicitly requires agents to extract structured facts from free-text fields. If the agent cannot determine which fields are unstructured, which database holds them, and what extraction approach to use from this document alone, it will fail every HR3 query — returning raw text instead of structured answers.

---

## Test questions

### Question 1
"A DAB query requires analyzing support articles and call transcripts in the CRM Arena Pro dataset for BANT lead qualification. Which database holds this unstructured field, what does BANT stand for, which tool must the agent use, and what is the difficulty rating?"

Required concepts:
- The unstructured text is in the PostgreSQL crm_support database containing support articles and call transcripts
- BANT stands for Budget Authority Need and Timeline and the extraction must analyze each factor individually
- The agent must use the execute_python tool because SQL alone cannot reliably parse this unstructured text
- This extraction is rated HIGH difficulty in the HR3 coverage map

Forbidden contradictions:
- Stating that the support text is in SQLite or MongoDB
- Stating that SQL alone can extract BANT factors from free text

---

### Question 2
"A query asks whether businesses in the Google Local dataset are open on Sundays and what services they offer. Which fields contain this information, are they free-text or semi-structured, and how should each field be parsed?"

Required concepts:
- The operating hours are in the PostgreSQL business_description.hours field stored as a JSON array
- The services and amenities are in the PostgreSQL business_description.MISC field stored as a JSON object
- Both hours and MISC are semi-structured fields not free-text because they contain JSON encoded as TEXT
- For hours use PostgreSQL json casting or Python json.loads to parse the array
- For MISC use PostgreSQL json arrow notation or Python json.loads to access nested key-value pairs

Forbidden contradictions:
- Stating that hours and MISC are free-text fields requiring NLP
- Stating that hours or MISC are in the SQLite review table

---

### Question 3
"A query requires checking whether GitHub repository README files contain copyright information. Which database holds the README content, where is the repository metadata stored by contrast, what extraction approach should the agent use, and what is the difficulty rating for this extraction?"

Required concepts:
- README content is stored in the DuckDB repo_artifacts.db database
- The extraction approach for copyright detection is regex or case-insensitive keyword search for the word copyright
- This is rated LOW difficulty because it is a simple keyword search not complex NLP
- Repository metadata and language information is in SQLite but README content is in DuckDB

Forbidden contradictions:
- Stating that README content is in the SQLite metadata database
- Stating that copyright detection requires LLM extraction

---

### Question 4
"What is the extraction protocol that the agent should follow when a query requires information from an unstructured field, and what are the five steps?"

Required concepts:
- Step 1 identify the field from the unstructured fields inventory to confirm it exists and which database holds it
- Step 2 sample 10 values from the field to verify the content matches what is documented
- Step 3 choose the extraction method from simple keyword search or counting or structured LLM extraction or JSON parsing
- Step 4 extract and join the results back to other query results on the appropriate key using a pandas DataFrame
- Step 5 log the extraction pattern to KB v3 recording field name extraction method used and success or failure

Forbidden contradictions:
- Stating fewer than five steps in the protocol
- Omitting the sampling step before extraction

---

### Question 5
"Which DAB datasets contain JSON-encoded semi-structured fields that need parsing, what are those specific fields, and what difficulty level are these semi-structured fields rated?"

Required concepts:
- Google Local has hours as a JSON array and MISC as a JSON object both in PostgreSQL business_description
- Deps Dev has Licenses and Advisories and Links as JSON-encoded fields in the SQLite packageinfo table
- Patents has parents and children as JSON arrays in the PostgreSQL cpc_definition table
- All semi-structured JSON fields are rated LOW difficulty because they need parsing not NLP extraction

Forbidden contradictions:
- Stating that JSON fields require LLM extraction
- Omitting any of the three datasets that have JSON-encoded fields

---

## Test result

**Run timestamp:** 2026-04-13 12:11 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/domain/unstructured_fields.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** A DAB query requires analyzing support articles and call transcripts in the CRM Arena Pro dataset for BANT lead qualification. Which database holds this unstructured field, what does BANT stand for, which tool must the agent use, and what is the difficulty rating?

**Concepts found (4/4):**
  - [x] The unstructured text is in the PostgreSQL crm_support database containing support articles and call transcripts
  - [x] BANT stands for Budget Authority Need and Timeline and the extraction must analyze each factor individually
  - [x] The agent must use the execute_python tool because SQL alone cannot reliably parse this unstructured text
  - [x] This extraction is rated HIGH difficulty in the HR3 coverage map

**Actual answer:**
Based solely on the provided document:

*   **Database:** PostgreSQL `crm_support`
*   **BANT stands for:** Budget, Authority, Need, and Timeline.
*   **Tool:** `execute_python`
*   **Difficulty Rating:** HIGH

**Grader reasoning:** All required concepts are clearly present in the actual answer, and there are no forbidden contradictions.

---

### Question 2 — PASS (100/100)

**Question:** A query asks whether businesses in the Google Local dataset are open on Sundays and what services they offer. Which fields contain this information, are they free-text or semi-structured, and how should each field be parsed?

**Concepts found (5/5):**
  - [x] The operating hours are in the PostgreSQL business_description.hours field stored as a JSON array
  - [x] The services and amenities are in the PostgreSQL business_description.MISC field stored as a JSON object
  - [x] Both hours and MISC are semi-structured fields not free-text because they contain JSON encoded as TEXT
  - [x] For hours use PostgreSQL json casting or Python json.loads to parse the array
  - [x] For MISC use PostgreSQL json arrow notation or Python json.loads to access nested key-value pairs

**Actual answer:**
Based on the document:

*   **Open on Sundays:** The `business_description.hours` field in the `googlelocal_db` database contains this information. It is a semi-structured field containing "JSON array of operating hours per day of week" and should be parsed using PostgreSQL `hours::json` or `json_array_elements`, or in Python via `json.loads(hours)`.
*   **Services offered:** The `business_description.MISC` field in the `googlelocal_db` database contains this information. It is a semi-structured field containing "JSON object with business attributes (services, amenities, accessibility)". This field should be parsed using PostgreSQL `MISC::json->>'key'` or in Python via `json.loads(misc)`.

**Grader reasoning:** The answer covers all required concepts and contains no contradictions, so it receives a perfect score.

---

### Question 3 — PASS (100/100)

**Question:** A query requires checking whether GitHub repository README files contain copyright information. Which database holds the README content, where is the repository metadata stored by contrast, what extraction approach should the agent use, and what is the difficulty rating for this extraction?

**Concepts found (4/4):**
  - [x] README content is stored in the DuckDB repo_artifacts.db database
  - [x] The extraction approach for copyright detection is regex or case-insensitive keyword search for the word copyright
  - [x] This is rated LOW difficulty because it is a simple keyword search not complex NLP
  - [x] Repository metadata and language information is in SQLite but README content is in DuckDB

**Actual answer:**
Based on the document:

*   The README content for GitHub repositories is stored in DuckDB `repo_artifacts.db`.
*   Repository metadata and language information is stored in SQLite `repo_metadata.db`.
*   The extraction approach to determine whether GitHub repository README files contain copyright information is regex for the "copyright" keyword.
*   The difficulty rating for this extraction is LOW.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, so the score is 100.

---

### Question 4 — PASS (100/100)

**Question:** What is the extraction protocol that the agent should follow when a query requires information from an unstructured field, and what are the five steps?

**Concepts found (5/5):**
  - [x] Step 1 identify the field from the unstructured fields inventory to confirm it exists and which database holds it
  - [x] Step 2 sample 10 values from the field to verify the content matches what is documented
  - [x] Step 3 choose the extraction method from simple keyword search or counting or structured LLM extraction or JSON parsing
  - [x] Step 4 extract and join the results back to other query results on the appropriate key using a pandas DataFrame
  - [x] Step 5 log the extraction pattern to KB v3 recording field name extraction method used and success or failure

**Actual answer:**
The extraction protocol for unstructured fields consists of five steps:

1.  **IDENTIFY** the field from this inventory → Confirms the field exists and which DB holds it
2.  **SAMPLE** 10 values from the field → Run: SELECT field FROM table LIMIT 10 → Verify the content matches what is documented here
3.  **CHOOSE** extraction method → Simple keyword search: Use SQL LIKE/ILIKE or regex | Counting/length: Use SQL LENGTH() or string functions | Structured extraction: Use `execute_python` with LLM extraction | JSON parsing: Use SQL json functions or Python `json.loads`
4.  **EXTRACT** and join back → Store extraction results in a pandas DataFrame → Join with other query results on the appropriate key
5.  **LOG** the extraction pattern to KB v3 → Record: field name, extraction method used, success/failure

**Grader reasoning:** All five required concepts are present in the answer and there are no forbidden contradictions.

---

### Question 5 — PASS (100/100)

**Question:** Which DAB datasets contain JSON-encoded semi-structured fields that need parsing, what are those specific fields, and what difficulty level are these semi-structured fields rated?

**Concepts found (4/4):**
  - [x] Google Local has hours as a JSON array and MISC as a JSON object both in PostgreSQL business_description
  - [x] Deps Dev has Licenses and Advisories and Links as JSON-encoded fields in the SQLite packageinfo table
  - [x] Patents has parents and children as JSON arrays in the PostgreSQL cpc_definition table
  - [x] All semi-structured JSON fields are rated LOW difficulty because they need parsing not NLP extraction

**Actual answer:**
According to the document, the DAB datasets containing JSON-encoded semi-structured fields that need parsing are:

*   **Google Local**: `business_description.hours` and `business_description.MISC`.
*   **Deps Dev**: `packageinfo.Licenses` and `packageinfo.Advisories`.
*   **Patents**: `cpc_definition.parents` and `cpc_definition.children`.

All of these semi-structured fields are rated as **LOW** difficulty.

**Grader reasoning:** All required concepts are present in the answer and no forbidden contradictions were found, so the score is 100.

---
