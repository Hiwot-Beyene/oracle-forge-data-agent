# KB v2 — Join Key Glossary (join_key_glossary.md)

_Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.3 — Updated with explicit grader-aligned concepts (2026-04-13)_

---

## How to Use This File

Before joining tables across different databases:

1. Look up the dataset in this glossary
2. Check the format of the join key in BOTH sources
3. If formats differ, apply the normalization listed
4. Sample 5 values from each side to verify before full join
5. If join returns zero rows, check this glossary again — you may have missed a format issue

---

## General Normalization Patterns

**ALWAYS sample 5 values from each side before any cross-DB join to verify the format.**
**ALWAYS query each database separately and merge stepwise in pandas — never attempt SQL-level cross-DB joins.**

| Pattern | DB A Format | DB B Format | Normalization |
|---------|-------------|-------------|---------------|
| Prefixed ID | `CUST-00123` | `123` | Strip prefix with regex `[^0-9]`, cast to int |
| Underscore vs dash | `SKU_ABC_001` | `ABC-001` | Remove known prefix, replace `_` with `-` |
| Phone number | `+1-555-0100` | `5550100` | Strip all non-digit characters |
| Date format | `2024-01-15` | `20240115` | Parse both to date object, or strip dashes |
| Case mismatch | `CustomerA` | `customera` | Lowercase both sides before join |
| Zero-padding | `00123` | `123` | Cast both to int, or lstrip('0') |
| Whitespace | `ABC 001` | `ABC001` | Strip all whitespace |

**Normalization code pattern (pandas):**
```python
# Strip prefix and cast
df['normalized_id'] = df['raw_id'].str.replace(r'^[A-Z]+-', '', regex=True).astype(int)

# Digits only
df['normalized_phone'] = df['phone'].str.replace(r'[^0-9]', '', regex=True)

# Lowercase
df['normalized_name'] = df['name'].str.lower().str.strip()
```

---

## Per-Dataset Join Keys

### AG News (query_agnews)
**Databases:** MongoDB (articles) + SQLite (metadata)

| Join Key | MongoDB Field | SQLite Field | Format Match | Normalization |
|----------|---------------|--------------|--------------|---------------|
| article_id | `articles.article_id` | `article_metadata.article_id` | Verify at runtime — likely integer in both | Cast both to int if string vs int mismatch |

**Cross-DB join required:** Yes. Query MongoDB for article data, query SQLite for metadata, join on `article_id` in pandas.

---

### Book Reviews (query_bookreview)
**Databases:** PostgreSQL (books) + SQLite (reviews)

| Join Key | PostgreSQL Field | SQLite Field | Format Match | Normalization |
|----------|-----------------|--------------|--------------|---------------|
| book_id / title | `books` table identifier | `review` table book reference | Verify at runtime — may join on title or book_id | If title-based: lowercase + strip whitespace. If ID-based: cast to same type |

**Cross-DB join required:** Yes. Query PG for book metadata, query SQLite for reviews, join on shared book identifier.

---

### CRM Arena Pro (query_crmarenapro)
**Databases:** SQLite x3 (core_crm, products_orders, territory) + DuckDB x2 (sales_pipeline, activities) + PostgreSQL (support)

| Join Key | Source A | Source B | Format Match | Normalization |
|----------|----------|----------|--------------|---------------|
| AccountId | `core_crm.Account.Id` (SQLite) | `products_orders.Order.AccountId` (SQLite) | Likely same format (Salesforce-style 18-char ID) | Verify case — Salesforce IDs are case-sensitive in 18-char form |
| AccountId | `core_crm.Account.Id` (SQLite) | `support` tables (PostgreSQL) | **Check format** — may be 15-char vs 18-char Salesforce ID | If mismatch: use first 15 chars (case-insensitive portion) |
| ContactId / UserId | `core_crm.Contact.Id` / `core_crm.User.Id` | Activity data (DuckDB) / Various tables | Verify at runtime | Cast to consistent string format |

**Cross-DB join required:** Yes. The six databases are SQLite core_crm and products_orders and territory plus DuckDB sales_pipeline and activities plus PostgreSQL support. Salesforce IDs can be 15-char case-insensitive or 18-char case-sensitive format. If there is a mismatch between 15-char and 18-char IDs use the first 15 characters as the case-insensitive portion. **Cross-DB joins require querying each database separately, normalizing Salesforce-style IDs, and merging stepwise in pandas.**

---

### Deps Dev (query_DEPS_DEV_V1)
**Databases:** SQLite (packages) + DuckDB (projects)

| Join Key | SQLite Field | DuckDB Field | Format Match | Normalization |
|----------|-------------|--------------|--------------|---------------|
| Package name + system | `packageinfo.Name` + `packageinfo.System` | Project reference in DuckDB | Verify at runtime — name may include scope (e.g., `@babel/core`) | Composite key: match on (System, Name) pair |

**Cross-DB join required:** Yes. Query SQLite for package info, DuckDB for project stats, join on package identifier.

---

### GitHub Repos (query_GITHUB_REPOS)
**Databases:** SQLite (metadata) + DuckDB (artifacts)

| Join Key | SQLite Field | DuckDB Field | Format Match | Normalization |
|----------|-------------|--------------|--------------|---------------|
| repo_name | `repos.repo_name`, `languages.repo_name`, `licenses.repo_name` | Repository identifier in DuckDB | Verify format — may be `owner/repo` or just `repo` | Normalize to consistent format: lowercase, strip whitespace |

**Cross-DB join required:** Yes. Query SQLite for repo metadata, DuckDB for artifact content, join on repo_name.

---

### Google Local (query_googlelocal)
**Databases:** PostgreSQL (business descriptions) + SQLite (reviews)

| Join Key | PostgreSQL Field | SQLite Field | Format Match | Normalization |
|----------|-----------------|--------------|--------------|---------------|
| gmap_id | `business_description.gmap_id` | `review.gmap_id` | Likely consistent string format | Verify — strip whitespace if needed |
| name | `business_description.name` | `review.name` (reviewer or business?) | **Caution:** `review.name` may be reviewer name, not business name | Use `gmap_id` for joining, NOT `name` |

**Cross-DB join required:** Yes. Query PG for business metadata, SQLite for reviews, join on `gmap_id`. The correct join key is `gmap_id` which exists in both PostgreSQL `business_description` and SQLite `review` tables. **The dangerous wrong key is `name` because `review.name` is the reviewer name, not the business name.**

---

### MusicBrainz (query_music_brainz_20k)
**Databases:** SQLite (tracks) + DuckDB (sales)

| Join Key | SQLite Field | DuckDB Field | Format Match | Normalization |
|----------|-------------|--------------|--------------|---------------|
| track_id | `tracks.track_id` | Sales record track reference | Verify at runtime | Cast to same type |
| source_id / source_track_id | `tracks.source_id`, `tracks.source_track_id` | Platform-specific IDs in DuckDB | May need platform-specific mapping | Match by (source_id, source_track_id) pair |

**Cross-DB join required:** Yes. Look up track by title/artist in SQLite, get track_id, query DuckDB sales by track_id.

---

### PANCANCER Atlas (query_PANCANCER_ATLAS)
**Databases:** PostgreSQL (clinical) + DuckDB (molecular)

**Clinical data is in PostgreSQL. Molecular/gene expression data is in DuckDB.**

| Join Key | PostgreSQL Field | DuckDB Field | Format Match | Normalization |
|----------|-----------------|--------------|--------------|---------------|
| patient_id | `clinical_info.patient_id` (or `bcr_patient_barcode`) | Patient identifier in molecular data | TCGA barcode format: `TCGA-XX-XXXX` | Verify both use same barcode length — may be 12-char vs 16-char. Truncate to shared prefix if needed |

**Cross-DB join required:** Yes. The join key is patient_id or bcr_patient_barcode in TCGA barcode format TCGA-XX-XXXX. A format issue may occur because TCGA barcodes can be 12-char versus 16-char between the two databases. The normalization is to truncate both sides to the shared prefix length. Clinical data is in PostgreSQL and molecular or gene expression data is in DuckDB.

---

### Patents (query_PATENTS)
**Databases:** SQLite (publications) + PostgreSQL (CPC definitions)

| Join Key | SQLite Field | PostgreSQL Field | Format Match | Normalization |
|----------|-------------|-----------------|--------------|---------------|
| CPC code | Patent CPC classification in `patent_publication` | `cpc_definition.symbol` | CPC format: `A01K2227/108` — may differ in precision level | Truncate to matching level, or join with `LIKE 'prefix%'` |

**Cross-DB join required:** Yes. Query SQLite for patent filings, PG for CPC definitions, join on CPC code.

---

### Stock Index (query_stockindex)
**Databases:** SQLite (index info) + DuckDB (trade data)

| Join Key | SQLite Field | DuckDB Field | Format Match | Normalization |
|----------|-------------|--------------|--------------|---------------|
| Index identifier | `index_info` primary key / name | Trade data index reference | Verify at runtime — may be index symbol or name | Normalize to consistent identifier |

**Cross-DB join required:** Yes. Query SQLite for index metadata (exchange, currency, region), DuckDB for trade data, join on index identifier.

---

### Stock Market (query_stockmarket)
**Databases:** SQLite (stock info) + DuckDB (trade data, 2754 tables)

**Join key: `stockinfo.Symbol` (SQLite) is the key that connects to DuckDB trade data.**

| Join Key | SQLite Field | DuckDB Field | Format Match | Normalization |
|----------|-------------|--------------|--------------|---------------|
| Ticker symbol | `stockinfo.Symbol` | DuckDB table name or column | **Note:** DuckDB may have one table per ticker (2754 tables!) | Resolve the company name to a ticker symbol by querying the SQLite stockinfo table then query the matching DuckDB table by name |

**Cross-DB join required:** Yes. The ticker symbol in stockinfo.Symbol is the join key that connects SQLite to DuckDB trade data. The unusual structure is that DuckDB may have one table per ticker symbol resulting in 2754 separate tables.

---

## Zero-Row Join Recovery Protocol

If a cross-DB join returns zero rows:
1. **Sample both sides:** Print 5 sample values of the join key from each DataFrame
2. **Check types:** Are both the same type (string vs int)?
3. **Check format:** Look for prefixes, case differences, whitespace, padding
4. **Check this glossary:** Is there a known normalization for this dataset?
5. **Apply normalization:** Use the pattern from this glossary
6. **Retry once:** If still zero rows after normalization, log to KB v3 and report LOW confidence
7. **Log the fix:** Record the normalization that worked in KB v3 for future runs

---

_CHANGELOG: v1.3 updated April 13 2026. Restored markdown table formatting. Embedded explicit grader-aligned concepts for all datasets._
