# KB Evaluation — Failure Taxonomy

_Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.0 — Initial population from DAB paper Section 3.3 (n=1,147 annotated trajectories)_

---

## SECTION A: The Four Hard Requirement Categories

DAB defines four hard requirements that separate enterprise data agents from toy demos. Each category produces a distinct class of failures. The adversarial probe library (probes/probes.md) must cover at least 3 of these 4 categories.

### HR1 — Multi-Database Routing

**What it tests:** Agent must route sub-queries to the correct database system (PostgreSQL, MongoDB, SQLite, DuckDB), translate between query dialects, and merge results.

**How agents fail:**
- Query only one database when two are needed
- Use SQL syntax on MongoDB (FM6 — dialect error)
- Fail to merge results from separate databases
- Assume all tables are in the same database

**Probe type:** Give a query requiring data from two different database systems. Verify the agent queries both and merges results correctly.

**Example probe:** "What is the average rating of books in the Literature & Fiction category?" — requires PostgreSQL (category) + SQLite (ratings) + cross-DB join on book_id.

---

### HR2 — Ill-Formatted Join Keys

**What it tests:** Agent must detect and resolve format mismatches in join keys across databases.

**How agents fail:**
- Attempt join without inspecting key formats — get zero rows
- Strip too much or too little from key prefix
- Fail silently with empty result instead of detecting the mismatch

**Zero-row recovery protocol:** When a cross-DB join returns zero rows, the agent should stop, inspect join key formats from both sides, sample values from each database, detect the mismatch, normalize the keys to a common format, and retry the join.

**Probe type:** Give a query where join keys have different formats across databases. Verify the agent samples keys, detects the mismatch, normalizes, and produces correct results.

**Known DAB patterns:**

| Entity | DB A Format | DB B Format | Resolution |
|--------|-------------|-------------|------------|
| Customer ID | `CUST-00123` | `123` | Strip prefix, zero-pad |
| TCGA barcode | Full 28-char | Truncated 12-char | Truncate or extend to match |
| Salesforce ID | 15-char | 18-char | Use 15-char prefix |
| gmap_id | String in PostgreSQL | String in SQLite | Direct match (same format) |
| Phone number | `+1-555-0100` | `5550100` | Strip country code and separators |

**Example probe:** "How many support tickets were filed by customers who made repeat purchases?" — requires joining customer IDs that are formatted differently across the transaction DB and CRM DB.

---

### HR3 — Unstructured Text Transformation

**What it tests:** Agent must extract structured facts from free-text fields (support notes, clinical notes, reviews, patent descriptions) before using them in calculations.

**How agents fail:**
- Return raw text instead of structured extraction
- Use regex-only extraction — fails on variant formats (FM4 critical sub-pattern)
- Skip extraction entirely and use a proxy column
- Regex `MALE` matches inside `FEMALE` (PANCANCER)
- Year-extraction regex matches ISBN segments (bookreview)

**Probe type:** Give a query requiring a count or classification derived from a free-text field. Verify the agent performs extraction before aggregation.

**DAB domains with unstructured text requirements:**

| Domain | Text Field | Extraction Needed |
|--------|------------|-------------------|
| Telecom | Support notes | Complaint category |
| Healthcare | Clinical notes | Diagnosis codes |
| Retail | Product reviews | Sentiment / attributes |
| Patents | Publication descriptions | Filing dates (>20 format variants) |
| AG News | Article descriptions | Topic classification |
| Book Reviews | Review text | Publication year (not ISBN) |

**Example probe:** "What percentage of support tickets mention billing complaints?" — requires text extraction from free-text notes field, not just keyword matching.

---

### HR4 — Domain Knowledge Gap

**What it tests:** Agent must know business definitions NOT present in the schema — industry terminology, fiscal calendars, status code meanings.

**How agents fail:**
- Use naive definition instead of domain-specific one (e.g., "active" = any non-null row)
- Apply calendar year when fiscal year is different
- Confuse BRCA gene with BRCA cancer type abbreviation
- Assume standard metric definition when dataset uses custom one

**Probe type:** Give a query using an ambiguous business term. Verify the agent consults the domain glossary (KB v2) before computing.

**High-risk terms from DAB:**

| Term | Naive Interpretation | Correct Interpretation |
|------|---------------------|----------------------|
| Churn | Didn't purchase this month | Cancelled or became inactive (dataset-specific) |
| Active account | status != 'closed' | Specific status code values per dataset |
| Repeat purchase rate | Total purchases / customers | Customers with >=2 purchases / unique customers |
| Fiscal year | Jan 1 - Dec 31 | Dataset-specific start/end dates |
| BRCA | BRCA gene | Breast Invasive Carcinoma — this is a cancer type abbreviation in PANCANCER, NOT the BRCA gene |
| Latest version | Highest semver string | Most recent by UpstreamPublishedAt date |

**Example probe:** "What is the repeat purchase rate for Q3?" — verify the agent uses the correct definition (ratio of customers, not transactions) and confirms the time window.

---

## SECTION B: Paper Failure Modes (FM1–FM5)

Source: DAB paper Section 3.3, based on 1,147 annotated incorrect trajectories across 5 models.

**Key statistic: FM2 + FM4 account for ~85% of all incorrect answers. Agents usually find the right data — they fail at planning or implementing.**

| FM Code | Name | % of Failures | Description | Mitigation |
|---------|------|---------------|-------------|------------|
| FM1 | Fails before planning | varies (Gemini-2.5-Flash: 63.4% null tool calls) | Agent makes no attempt — returns null tool-call or refuses ("I cannot join across databases") | System prompt must explicitly state cross-DB joins are supported; ensure tool definitions are visible |
| FM2 | Incorrect plan | ~40% | Logical plan is wrong — even perfect execution cannot produce correct answer | Domain glossary (KB v2 business_terms.md) + exploration before execution (~20% tool calls) |
| FM3 | Incorrect data selection | ~15% | Correct plan but wrong table or column chosen (e.g., checking `description` for language when it is in `details`) | Schema enrichment (KB v2 schemas.md) with column semantics beyond raw data types |
| FM4 | Incorrect implementation | ~45% | Correct plan + correct data, but code is wrong. Dominant sub-pattern: regex-only text extraction | Expose dedicated extraction tools (dateutil, NER, LLM-based extraction) alongside SQL and Python |
| FM5 | Runtime error | rare (Kimi-K2: 6.6%) | API failures, token limits, timeouts, 100-call iteration limit | Budget monitoring, efficient queries, error recovery loop |

### FM4 Critical Sub-Pattern: Regex-Only Text Extraction

The FM4 critical sub-pattern is that all tested agents use regex exclusively for text extraction. This manifests in two key ways:

1. **Patents: 0% pass@1 across all models and all trials** because regex cannot handle the more than 20 date format variants in Patents such as "dated 5th March 2019" or "March the 18th, 2019". The correct extraction methods are `dateutil.parser.parse` or `pd.to_datetime`, not bare regex.
2. **PANCANCER: gender misclassification** where regex `MALE` matches inside `FEMALE`, and **Bookreview: year errors** where regex matches ISBN segments.

**Paper recommendation:** Expose dedicated extraction tools (date parsers, NER taggers, LLM-based extraction) alongside SQL and Python execution.

---

## SECTION C: Probe-to-Failure Mapping

This table maps which probe types test which failure categories and modes. Use this when building the adversarial probe library (probes/probes.md).

| Probe Type | Hard Requirement Tested | Failure Modes Exposed | Minimum Probes |
|------------|------------------------|----------------------|----------------|
| Cross-DB join query | HR1 (Multi-DB Routing) | FM1, FM3, FM6 | 4 |
| Format-mismatch join | HR2 (Ill-Formatted Keys) | FM4 | 4 |
| Text extraction query | HR3 (Unstructured Text) | FM4 | 4 |
| Ambiguous business term | HR4 (Domain Knowledge) | FM2, FM5 | 3 |
| **Total minimum** | **3+ categories** | | **15** |

### Probe Documentation Format (for probes/probes.md)

Each probe must document:

1. **Query text** — the natural language question
2. **Failure category** — which of the 4 hard requirements it tests
3. **Expected failure** — what the agent is likely to get wrong
4. **Observed failure** — what the agent actually got wrong
5. **Fix applied** — what KB entry, prompt change, or code fix resolved it
6. **Post-fix score** — pass/fail on this query after the fix

---

## SECTION D: Completely Unsolved Datasets

| Dataset | pass@1 (best model) | Primary Failure Mode | Why |
|---------|---------------------|---------------------|-----|
| Patents | 0% across ALL models, ALL trials | FM4 (regex-only extraction) | >20 date format variants; CPC hierarchy navigation; 5GB SQLite file |
| stockindex (partial) | Very low | FM5 (domain knowledge) | Exchange-to-region mapping not in schema |

**Patents** is the single hardest dataset. Any agent that solves even 1 Patents query would be a novel research contribution. The same regex-only extraction problem also causes PANCANCER gender misclassification (regex `MALE` matches inside `FEMALE`).

---

_CHANGELOG: v1.0 created April 14 2026. Initial population from DAB paper Section 3.3, Challenge document, and Practitioner Manual._
