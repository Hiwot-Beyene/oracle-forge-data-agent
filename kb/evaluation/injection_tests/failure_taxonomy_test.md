# Injection test — failure_taxonomy.md

## Document under test
`kb/evaluation/failure_taxonomy.md`

## Why this test is critical
failure_taxonomy.md defines the failure categories and modes that the adversarial probe library must cover. If the agent team cannot derive the correct failure classification from this document alone, they will build probes that miss the most common failure modes, focus on rare failures while ignoring FM2+FM4 (which account for 85% of errors), or misunderstand what makes Patents unsolvable.

---

## Test questions

### Question 1
"Which two failure modes account for 85% of all incorrect answers in DAB, what does each mean, and what is the approximate percentage for each?"

Required concepts:
- FM2 incorrect plan accounts for approximately 40 percent of failures
- FM4 incorrect implementation accounts for approximately 45 percent of failures
- FM2 means the logical plan is wrong so even perfect execution cannot produce the correct answer
- FM4 means the plan and data selection are correct but the code implementation is wrong
- Together they account for approximately 85 percent of all incorrect answers

Forbidden contradictions:
- Stating that FM1 or FM3 are the dominant failure modes
- Stating that runtime errors are a major source of failures

---

### Question 2
"What are the known join key format mismatches in DAB for TCGA barcodes and Salesforce IDs, how should each be resolved, and what is the general protocol when a cross-DB join returns zero rows?"

Required concepts:
- TCGA barcodes may be full 28-character in one DB and truncated to 12-character in another resolved by truncating or extending to match
- Salesforce IDs may be 15-character in one DB and 18-character in another resolved by using the 15-character prefix
- When a cross-DB join returns zero rows the agent should stop inspect join key formats from both sides sample values detect the mismatch normalize and retry

Forbidden contradictions:
- Stating that zero rows after a join is an acceptable final result without investigation
- Stating that TCGA barcodes are always the same length across databases

---

### Question 3
"Why did all frontier models score 0% on the Patents dataset, what is the FM4 critical sub-pattern causing this, what specific date format examples show why regex fails, what other datasets are affected by this same regex pattern, and what extraction method should be used instead?"

Required concepts:
- All models scored 0% pass@1 on Patents across all trials
- The FM4 critical sub-pattern is that all tested agents use regex exclusively for text extraction
- Regex cannot handle the more than 20 date format variants in Patents such as dated 5th March 2019 or March the 18th 2019
- The correct extraction methods are dateutil.parser.parse or pd.to_datetime not bare regex
- Additional failures include PANCANCER gender misclassification where regex MALE matches inside FEMALE

Forbidden contradictions:
- Stating that regex is sufficient for patent date extraction
- Stating that some models solved Patents queries

---

### Question 4
"How many adversarial probes are required for the probe library, how many of the four hard requirement categories must be covered, and what six fields must each probe document?"

Required concepts:
- Minimum 15 probes are required
- Minimum 3 of the 4 hard requirement categories must be covered
- Each probe must document query text and failure category and expected failure and observed failure and fix applied and post-fix score

Forbidden contradictions:
- Stating that fewer than 15 probes is acceptable
- Stating that only 1 or 2 categories need coverage

---

### Question 5
"For the domain knowledge gap failure category HR4, what is the correct definition of repeat purchase rate versus the naive interpretation, and what is the dangerous misinterpretation of BRCA in the PANCANCER dataset?"

Required concepts:
- Repeat purchase rate correct definition is customers with 2 or more purchases divided by total unique customers not total purchases divided by total customers
- The naive interpretation of repeat purchase rate is total purchases divided by customers which is wrong
- BRCA in PANCANCER stands for Breast Invasive Carcinoma which is a cancer type abbreviation
- The dangerous misinterpretation is confusing BRCA with the BRCA gene

Forbidden contradictions:
- Stating that repeat purchase rate is total purchases divided by total customers
- Stating that BRCA refers to the gene in the PANCANCER context

---

## Test result

**Run timestamp:** 2026-04-14 16:12 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/evaluation/failure_taxonomy.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** Which two failure modes account for 85% of all incorrect answers in DAB, what does each mean, and what is the approximate percentage for each?

**Concepts found (5/5):**
  - [x] FM2 incorrect plan accounts for approximately 40 percent of failures
  - [x] FM4 incorrect implementation accounts for approximately 45 percent of failures
  - [x] FM2 means the logical plan is wrong so even perfect execution cannot produce the correct answer
  - [x] FM4 means the plan and data selection are correct but the code implementation is wrong
  - [x] Together they account for approximately 85 percent of all incorrect answers

**Actual answer:**
According to Section B, **FM2 (Incorrect plan)** and **FM4 (Incorrect implementation)** account for ~85% of all incorrect answers.

*   **FM2 (Incorrect plan):** The logical plan is wrong, meaning that even perfect execution cannot produce the correct answer. This failure mode accounts for approximately 40% of failures.
*   **FM4 (Incorrect implementation):** The correct plan is chosen and the correct data is identified, but the code used to execute the plan is wrong. This failure mode accounts for approximately 45% of failures.

**Grader reasoning:** All required concepts are present, and no forbidden contradictions are present, earning a perfect score.

---

### Question 2 — PASS (100/100)

**Question:** What are the known join key format mismatches in DAB for TCGA barcodes and Salesforce IDs, how should each be resolved, and what is the general protocol when a cross-DB join returns zero rows?

**Concepts found (3/3):**
  - [x] TCGA barcodes may be full 28-character in one DB and truncated to 12-character in another resolved by truncating or extending to match
  - [x] Salesforce IDs may be 15-character in one DB and 18-character in another resolved by using the 15-character prefix
  - [x] When a cross-DB join returns zero rows the agent should stop inspect join key formats from both sides sample values detect the mismatch normalize and retry

**Actual answer:**
Based on the provided document, here's the information on join key format mismatches, their resolution, and the zero-row recovery protocol:

**TCGA barcode:**

*   DB A Format: Full 28-char
*   DB B Format: Truncated 12-char
*   Resolution: Truncate or extend to match

**Salesforce ID:**

*   DB A Format: 15-char
*   DB B Format: 18-char
*   Resolution: Use 15-char prefix

**Zero-row recovery protocol:**

When a cross-DB join returns zero rows, the agent should:

1.  Stop.
2.  Inspect join key formats from both sides.
3.  Sample values from each database.
4.  Detect the mismatch.
5.  Normalize the keys to a common format.
6.  Retry the join.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found.

---

### Question 3 — PASS (100/100)

**Question:** Why did all frontier models score 0% on the Patents dataset, what is the FM4 critical sub-pattern causing this, what specific date format examples show why regex fails, what other datasets are affected by this same regex pattern, and what extraction method should be used instead?

**Concepts found (5/5):**
  - [x] All models scored 0% pass@1 on Patents across all trials
  - [x] The FM4 critical sub-pattern is that all tested agents use regex exclusively for text extraction
  - [x] Regex cannot handle the more than 20 date format variants in Patents such as dated 5th March 2019 or March the 18th 2019
  - [x] The correct extraction methods are dateutil.parser.parse or pd.to_datetime not bare regex
  - [x] Additional failures include PANCANCER gender misclassification where regex MALE matches inside FEMALE

**Actual answer:**
Here's the answer based solely on the provided document:

*   **Why 0% on Patents:** All tested agents/models scored 0% pass@1 on the Patents dataset.
*   **FM4 Critical Sub-Pattern:** The primary failure mode is FM4 (Incorrect implementation), specifically the sub-pattern of relying exclusively on regex for text extraction.
*   **Date Format Examples:** Regex cannot handle the >20 date format variants in Patents, such as  "dated 5th March 2019" or "March the 18th, 2019".
*   **Other Datasets Affected:** The same regex-only extraction pattern also causes PANCANCER gender misclassification, where regex `MALE` matches inside `FEMALE`, and Bookreview year extraction errors where regex matches ISBN segments
*   **Extraction Method:** `dateutil.parser.parse` or `pd.to_datetime` should be used instead of bare regex.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are present.

---

### Question 4 — PASS (100/100)

**Question:** How many adversarial probes are required for the probe library, how many of the four hard requirement categories must be covered, and what six fields must each probe document?

**Concepts found (3/3):**
  - [x] Minimum 15 probes are required
  - [x] Minimum 3 of the 4 hard requirement categories must be covered
  - [x] Each probe must document query text and failure category and expected failure and observed failure and fix applied and post-fix score

**Actual answer:**
Based on the document:

*   A minimum of **15** adversarial probes are required for the probe library.
*   The adversarial probe library must cover at least **3** of the 4 hard requirement categories.
*   Each probe must document the following six fields:
    1.  Query text
    2.  Failure category
    3.  Expected failure
    4.  Observed failure
    5.  Fix applied
    6.  Post-fix score

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, resulting in a perfect score.

---

### Question 5 — PASS (100/100)

**Question:** For the domain knowledge gap failure category HR4, what is the correct definition of repeat purchase rate versus the naive interpretation, and what is the dangerous misinterpretation of BRCA in the PANCANCER dataset?

**Concepts found (4/4):**
  - [x] Repeat purchase rate correct definition is customers with 2 or more purchases divided by total unique customers not total purchases divided by total customers
  - [x] The naive interpretation of repeat purchase rate is total purchases divided by customers which is wrong
  - [x] BRCA in PANCANCER stands for Breast Invasive Carcinoma which is a cancer type abbreviation
  - [x] The dangerous misinterpretation is confusing BRCA with the BRCA gene

**Actual answer:**
According to the document, for the domain knowledge gap failure category HR4 regarding "Repeat purchase rate," the naive interpretation is "Total purchases / customers," while the correct interpretation is "Customers with >=2 purchases / unique customers."

In the PANCANCER dataset, the dangerous misinterpretation of BRCA is confusing the "BRCA gene" with "Breast Invasive Carcinoma," as BRCA is a cancer type abbreviation in this dataset, not the gene.

**Grader reasoning:** All required concepts are clearly present and there are no forbidden contradictions, so the score is 100/100.

---
