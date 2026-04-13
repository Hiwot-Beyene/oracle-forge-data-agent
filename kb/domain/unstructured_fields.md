# KB v2 — Unstructured Text Fields Inventory (unstructured_fields.md)

Oracle Forge | Intelligence Officers | April 2026
Status: v1.1 — Updated with injection test fixes (2026-04-13)

## How to Use This File

When a query requires information from a free-text or semi-structured field:

1. Look up the field in this inventory
2. Follow the extraction approach listed
3. Sample 10 values first to verify the format matches what is documented here
4. Use `execute_python` tool for extraction — SQL alone cannot reliably parse unstructured text
5. Log any new extraction patterns discovered to KB v3

## Unstructured Text Fields (Free Text)

These fields contain natural language text that may need NLP/LLM extraction.

### AG News — `articles.description` (MongoDB)

| Property            | Value                                                                                              |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| Database            | MongoDB `articles` collection                                                                      |
| Field               | description                                                                                        |
| Content type        | Article body text (news article content)                                                           |
| Typical length      | 100-500 characters                                                                                 |
| Use cases           | Character count analysis, keyword search, topic extraction                                         |
| Extraction approach | For character count: `len(description)`. For keyword/topic: regex or LLM extraction                |
| Example query       | "What is the title of the sports article whose description has the greatest number of characters?" |

### Book Reviews — `review.text` (SQLite)

| Property            | Value                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------- |
| Database            | SQLite `review_query.db`                                                                     |
| Field               | text                                                                                         |
| Content type        | User-written book reviews                                                                    |
| Typical length      | 50-2000 characters                                                                           |
| Use cases           | Sentiment analysis, keyword extraction, topic detection                                      |
| Extraction approach | For sentiment: LLM classification or keyword heuristics. For keywords: regex or LIKE queries |
| Example query       | Queries requiring sentiment or specific content from reviews                                 |

### Google Local — `business_description.description` (PostgreSQL)

| Property            | Value                                                                              |
| ------------------- | ---------------------------------------------------------------------------------- |
| Database            | PostgreSQL `googlelocal_db`                                                        |
| Field               | description                                                                        |
| Content type        | Business description text (what the business does, services offered)               |
| Typical length      | 0-1000 characters (may be NULL for some businesses)                                |
| Use cases           | Business type classification, service detection, keyword search                    |
| Extraction approach | LIKE/ILIKE for keyword search in SQL, or LLM extraction for complex classification |

### Google Local — `review.text` (SQLite)

| Property            | Value                                                               |
| ------------------- | ------------------------------------------------------------------- |
| Database            | SQLite `review_query.db`                                            |
| Field               | text                                                                |
| Content type        | User-written business reviews                                       |
| Typical length      | 10-500 characters                                                   |
| Use cases           | Sentiment analysis, service quality extraction, complaint detection |
| Extraction approach | LLM extraction or keyword-based classification                      |

### PANCANCER Atlas — `clinical_info.Patient_description` (PostgreSQL)

| Property            | Value                                                                                 |
| ------------------- | ------------------------------------------------------------------------------------- |
| Database            | PostgreSQL `pancancer_clinical`                                                       |
| Field               | Patient_description                                                                   |
| Content type        | Clinical notes about the patient                                                      |
| Typical length      | Variable                                                                              |
| Use cases           | Diagnosis extraction, treatment history, clinical observations                        |
| Extraction approach | Medical NLP — use LLM with specific extraction schema. Regex for ICD codes if present |

### Stock Market — `stockinfo.Company Description` (SQLite)

| Property            | Value                                                                  |
| ------------------- | ---------------------------------------------------------------------- |
| Database            | SQLite `stockinfo_query.db`                                            |
| Field               | Company Description                                                    |
| Content type        | Company business description (what the company does, sector, products) |
| Typical length      | 100-500 characters                                                     |
| Use cases           | Sector classification, business activity detection, keyword search     |
| Extraction approach | LIKE for simple keyword search, LLM for complex classification         |

### GitHub Repos — README content (DuckDB)

| Property            | Value                                                                                                                |
| ------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Database            | DuckDB `repo_artifacts.db`                                                                                           |
| Field               | README file content                                                                                                  |
| Content type        | Repository documentation in Markdown                                                                                 |
| Typical length      | 100-10000 characters                                                                                                 |
| Use cases           | Copyright detection, technology detection, project description extraction                                            |
| Extraction approach | Regex for "copyright" keyword. LLM for semantic analysis                                                             |
| Difficulty          | LOW — simple keyword search, not complex NLP                                                                         |
| Example query       | "Among repositories that do not use Python, what proportion of their README.md files include copyright information?" |

Note: Repository metadata and language information is in SQLite `repo_metadata.db`, but README content is in DuckDB `repo_artifacts.db`.

### CRM Arena Pro — Support articles and call transcripts (PostgreSQL)

| Property            | Value                                                                                                                                  |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Database            | PostgreSQL `crm_support`                                                                                                               |
| Field               | Article body / transcript text                                                                                                         |
| Content type        | Support knowledge articles and call transcripts                                                                                        |
| Typical length      | Variable                                                                                                                               |
| Use cases           | BANT factor analysis, lead qualification, issue categorization                                                                         |
| BANT Definition     | BANT stands for Budget, Authority, Need, and Timeline. The extraction must analyze each factor individually.                           |
| Extraction approach | LLM extraction for BANT factors. Requires `execute_python` tool — SQL alone cannot reliably parse unstructured text for BANT analysis. |
| Difficulty          | HIGH — rated HIGH in the Hard Requirement 3 (HR3) coverage map                                                                         |
| Example query       | "Can this lead be qualified based on latest discussions? Which BANT factors fail?"                                                     |

## Semi-Structured Fields (JSON/Array in TEXT columns)

These fields contain structured data encoded as text (JSON, arrays, delimited values).
They require parsing before use but are not free-text. All semi-structured JSON fields are rated LOW difficulty because they need parsing, not NLP extraction.

### Google Local — `business_description.hours` (PostgreSQL)

| Property         | Value                                                                                                                |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- |
| Database         | PostgreSQL `googlelocal_db`                                                                                          |
| Field            | hours                                                                                                                |
| Content type     | JSON array of operating hours per day of week                                                                        |
| Format           | `[["Monday, 9AM-5PM"], ["Tuesday, 9AM-5PM"], ...]` or similar                                                        |
| Parsing approach | For hours: use PostgreSQL `hours::json` or `json_array_elements` to parse the array. In Python: `json.loads(hours)`. |
| Use cases        | "Is this business open on Sundays?", "What are the operating hours?"                                                 |

### Google Local — `business_description.MISC` (PostgreSQL)

| Property         | Value                                                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Database         | PostgreSQL `googlelocal_db`                                                                                                          |
| Field            | MISC                                                                                                                                 |
| Content type     | JSON object with business attributes (services, amenities, accessibility)                                                            |
| Format           | `{"Service options": ["Dine-in", "Takeout"], "Accessibility": ["Wheelchair accessible"], ...}`                                       |
| Parsing approach | For MISC: use PostgreSQL `MISC::json->>'key'` (json arrow notation) to access nested key-value pairs. In Python: `json.loads(misc)`. |
| Use cases        | Service availability queries, accessibility checks, amenity filtering                                                                |

### Deps Dev — `packageinfo.Licenses` (SQLite)

| Property         | Value                                                                   |
| ---------------- | ----------------------------------------------------------------------- |
| Database         | SQLite `package_query.db`                                               |
| Field            | Licenses                                                                |
| Content type     | JSON array of license identifiers                                       |
| Format           | `["MIT"]` or `["Apache-2.0", "MIT"]`                                    |
| Parsing approach | Python: `json.loads(licenses)`. SQLite: use `json_extract` if available |
| Use cases        | License compliance queries, license distribution analysis               |

### Deps Dev — `packageinfo.Advisories` (SQLite)

| Property         | Value                                                  |
| ---------------- | ------------------------------------------------------ |
| Database         | SQLite `package_query.db`                              |
| Field            | Advisories                                             |
| Content type     | JSON array of security advisory records                |
| Format           | `[{"id": "CVE-...", "severity": "HIGH", ...}]` or `[]` |
| Parsing approach | Python: `json.loads(advisories)`, then filter/count    |
| Use cases        | Security audit queries, vulnerability counts           |

### Deps Dev — `packageinfo.Links` (SQLite)

| Property         | Value                                               |
| ---------------- | --------------------------------------------------- |
| Database         | SQLite `package_query.db`                           |
| Field            | Links                                               |
| Content type     | JSON object with URL links (homepage, repo, issues) |
| Parsing approach | Python: `json.loads(links)`                         |

### Patents — `cpc_definition.parents` / `children` (PostgreSQL)

| Property         | Value                                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| Database         | PostgreSQL `patent_CPCDefinition`                                            |
| Fields           | parents, children                                                            |
| Content type     | JSON arrays of CPC code references                                           |
| Parsing approach | PostgreSQL: `parents::json` or `json_array_elements`. Python: `json.loads()` |
| Use cases        | Navigating the CPC hierarchy, finding parent/child technology areas          |

## Extraction Protocol

When a query requires data from an unstructured field, follow this protocol:
Step 1: IDENTIFY the field from this inventory → Confirms the field exists and which DB holds it
Step 2: SAMPLE 10 values from the field → Run: SELECT field FROM table LIMIT 10 → Verify the content matches what is documented here
Step 3: CHOOSE extraction method → Simple keyword search: Use SQL LIKE/ILIKE or regex | Counting/length: Use SQL LENGTH() or string functions | Structured extraction: Use `execute_python` with LLM extraction | JSON parsing: Use SQL json functions or Python `json.loads`
Step 4: EXTRACT and join back → Store extraction results in a pandas DataFrame → Join with other query results on the appropriate key
Step 5: LOG the extraction pattern to KB v3 → Record: field name, extraction method used, success/failure

## Hard Requirement 3 Coverage Map

DAB's Hard Requirement 3 (Unstructured Text Transformation) appears in these datasets:
| Dataset | Field | Extraction Type | Difficulty |
|---------|-------|-----------------|------------|
| AG News | articles.description | Text length, keyword search | LOW |
| Book Reviews | review.text | Sentiment, content analysis | MEDIUM |
| CRM Arena Pro | Support articles / transcripts | BANT factor extraction | HIGH |
| Google Local | business_description.description | Business classification | MEDIUM |
| Google Local | review.text | Sentiment, complaint detection | MEDIUM |
| Google Local | business_description.hours | JSON array parsing | LOW |
| Google Local | business_description.MISC | JSON object parsing | LOW |
| GitHub Repos | README content | Copyright detection | LOW |
| PANCANCER Atlas | Patient_description | Clinical note extraction | HIGH |
| Stock Market | Company Description | Sector classification | LOW |
| Deps Dev | Licenses, Advisories | JSON array parsing | LOW |
| Patents | parents, children | JSON array parsing | LOW |

CHANGELOG: v1.1 updated April 13 2026. Fixes applied for injection test Q1 (explicit BANT definition, execute_python requirement, and HIGH difficulty rating clearly stated).
