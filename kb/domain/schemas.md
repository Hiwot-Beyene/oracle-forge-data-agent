# KB v2 — Column Semantics (schemas.md)

_Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.5 — Paper-aligned: Patents unsolved warning, date extraction guidance, FM4 mitigations (2026-04-14)_

## How to Use This File

This documents what columns MEAN in business context — not just their data types.
Raw schema introspection tells you a column is VARCHAR. This file tells you it contains
Salesforce-style 18-character case-sensitive IDs, or that "status" has exactly 3 valid values.
Before selecting a column for a query, check here for:

- What the column actually represents
- Known gotchas (nulls, encoding, valid values)
- Which table is authoritative when multiple tables have similar columns

## AG News (query_agnews)

MongoDB: `articles` collection
| Field | Type | Semantics | Notes |
|-------|------|-----------|-------|
| article_id | int/string | Unique article identifier | Join key to SQLite metadata |
| title | string | Article headline | Short text, not body |
| description | string | Full article body text | Unstructured — primary text field for analysis |
| category | string | News category label | Exactly 4 values: Sports, Business, Science/Technology, World |

SQLite: `article_metadata` table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| article_id | int | FK to MongoDB articles | Join key |
| author_id | int | FK to `authors` table | |
| region | text | Geographic region (Asia, Europe, etc.) | Used for geographic filtering |
| publication_date | text/date | Date article was published | Use for temporal queries — year extraction |

SQLite: `authors` table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| author_id | int | Primary key | Join to article_metadata |
| name | text | Author full name | Used for "articles by X" queries |

## Book Reviews (query_bookreview)

PostgreSQL: `books_info` table (bookreview_db)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| book_id / asin | varchar | Unique book identifier | Join key to SQLite reviews |
| title | varchar | Book title | |
| category | varchar | Book genre/category | e.g., "Literature & Fiction" — exact match required |
| language | varchar | Book language | e.g., "English" — filter for language-specific queries |
| publication_date | date/varchar | When the book was published | Used for decade grouping |

SQLite: `review` table (review_query.db)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| book_ref | text | FK to PostgreSQL books table | Join key — verify format match |
| rating | real | Review score, 1.0-5.0 | Per-review rating |
| title | text | Review title/headline | Short summary by reviewer |
| text | text | Full review body | Unstructured — sentiment/content analysis |
| review_time | text/int | When review was written | May be Unix timestamp — verify format |
| helpful_vote | int | Count of "helpful" votes | Popularity/quality signal |
| verified_purchase | int/bool | Whether reviewer bought the book | 1=verified, 0=not |
| purchase_id | text | **Join key** — references `books_info.book_id` in PostgreSQL | FK to PostgreSQL books — name is misleading, this IS the cross-DB join key |

**DB split:** Book category and language are in PostgreSQL `books_info`. Reviews (rating, text, helpfulness) are in SQLite `review`. **A cross-database join on `books_info.book_id` = `review.purchase_id` is required** to combine book metadata with review data. **Rating scale is 1.0 to 5.0** per individual review, not per book. **The SQLite join column is `purchase_id` (not `book_id`) — the name is misleading but it IS the FK to PostgreSQL.**

## CRM Arena Pro (query_crmarenapro)

SQLite: `core_crm.db` — User table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| Id | text | Salesforce User ID (18-char) | Primary key — case-sensitive |
| Name | text | User full name | Sales rep name |
| Email | text | User email | |

SQLite: `core_crm.db` — Account table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| Id | text | Salesforce Account ID | PK — join key across CRM tables |
| Name | text | Company name | |
| NumberOfEmployees | int | Company size | Numeric — used for segmentation |
| ShippingState | text | US state for shipping | Geographic filter |
| OwnerId | text | FK to User.Id | Account owner (sales rep) |

SQLite: `core_crm.db` — Contact table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| Id | text | Salesforce Contact ID | PK |
| AccountId | text | FK to Account.Id | Links person to company |
| FirstName | text | Contact first name | |
| LastName | text | Contact last name | |
| Email | text | Contact email | |

SQLite: `products_orders.db` — Order table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| Id | text | Order ID | PK |
| AccountId | text | FK to Account.Id | Which company placed the order |
| TotalAmount | real | Order total | Currency amount |
| Status | text | Order status | Check valid values at runtime |

SQLite: `products_orders.db` — Product2, Pricebook2, PricebookEntry
| Table | Key Columns | Semantics |
|-------|-------------|-----------|
| Product2 | Id, Name, ProductCode | Product catalog |
| Pricebook2 | Id, Name, IsActive | Pricing policy definitions |
| PricebookEntry | Id, Pricebook2Id, Product2Id, UnitPrice | Price per product per pricebook |
| OrderItem | Id, OrderId, Product2Id, Quantity, UnitPrice | Line items on orders |

DuckDB: `sales_pipeline.duckdb` — Sales funnel data. Schema TBD at runtime.
DuckDB: `activities.duckdb` — Activity logs. Schema TBD at runtime.
PostgreSQL: `crm_support` — Support tickets and knowledge articles. Schema TBD at runtime.

## Deps Dev (query_DEPS_DEV_V1)

SQLite: `package_query.db` — `packageinfo` table (logical name: `package_database`)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| System | text | Package ecosystem (NPM, Cargo, Maven, etc.) | Filter field |
| Name | text | Package name | May be a normal name (`@babel/core`) **or** a transitive-dependency notation (`@dmrvos/infrajs>0.0.6>typescript` — meaning: at version 0.0.6 of `@dmrvos/infrajs`, the dependency `typescript`). **Do NOT exclude names containing `>`** — they are valid distinct package identifiers and appear in ground-truth answers. |
| Version | text | Semantic version string | NOT for "latest" — use `UpstreamPublishedAt` |
| **UpstreamPublishedAt** | text/datetime | **Publication timestamp. Use this for "latest version" — sort by date, NOT the Version string and NOT `VersionInfo.Ordinal`.** | Sort by date |
| **VersionInfo** | text | JSON: `{"IsRelease": true/false, "Ordinal": N}`. **`IsRelease=1` filters out pre-release/dev versions.** `Ordinal` is a per-package monotonic counter — not a publish-time proxy across packages. | Use `json_extract(VersionInfo, '$.IsRelease') = 1` |
| **Licenses** | text | License identifiers as a JSON array (e.g., `["MIT", "Apache-2.0"]`). **This is the *package*-level license. The query2 phrase "project license" refers to the *project*-level license in `project_info.Licenses` (DuckDB), NOT this column.** | JSON parsing |
| **Advisories** | text | Security advisory records as a JSON array. | JSON parsing |
| Links | text | URLs (homepage, repo) | JSON structure |
| Hashes | text | Package checksums | |
| Registries | text | Which registries host this package | |
| Purl | text | Package URL (universal identifier) | |

DuckDB: `project_query.db` (logical name: `project_database`) — TWO tables, no shared key column between them.

`project_packageversion` — links each package version to a GitHub project
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| System | text | Same as packageinfo.System | |
| Name | text | Same as packageinfo.Name (join key to SQLite) | |
| Version | text | Package version | |
| ProjectType | text | Usually `GITHUB` | |
| **ProjectName** | text | **GitHub repo path, e.g. `mui-org/material-ui`, `sveltejs/svelte`, `microsoft/TypeScript`. This is the answer column when a query asks "which projects".** | Multiple Names can map to the same ProjectName |
| RelationProvenance | text | e.g. `UNVERIFIED_METADATA` | |
| RelationType | text | e.g. `SOURCE_REPO_TYPE` | |

`project_info` — free-text per-project metadata. **Has no `ProjectName` column.**
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| **Project_Information** | text | Free-text sentence. **Multiple narrative templates exist** — any single regex covers only ~75%. Numbers may include comma thousands separators (`73,499 stars`). **Stars and forks are extracted by regex from this text** — they are NOT separate columns. See "Stars/forks extraction" below for the full pattern. | See below |
| Licenses | text | **Project-level** license JSON array (e.g. `["MIT"]`, `["non-standard"]`). Filter "project license MIT" with `Licenses LIKE '%"MIT"%'`. | Distinct from `packageinfo.Licenses` |
| Description | text | Project description | |
| Homepage | text | Project homepage URL | |
| OSSFuzz | text | Often `"nan"` | |

**DB split summary:** Package data → SQLite `packageinfo`. Project ↔ package mapping → DuckDB `project_packageversion`. Project metadata (stars/forks/license) → DuckDB `project_info`. JSON-encoded columns requiring parsing: **`packageinfo.Licenses`, `packageinfo.Advisories`, `packageinfo.Links`, `packageinfo.VersionInfo`, `project_info.Licenses`**. Stars/forks live inside the **free-text** `project_info.Project_Information` and need regex extraction.

**Stars/forks extraction (CRITICAL — both the regex AND the COALESCE composition are landmines):**
The `Project_Information` text uses 3 narrative templates and numbers can be comma-formatted. Two pitfalls stack:
1. `'([0-9]+) stars'` returns `499` from `73,499 stars` (greedy digit run stops at the comma) and matches **none** of the `stars count of N` rows (~22% of corpus).
2. **DuckDB's `regexp_extract` returns empty string `''` on no-match, NOT NULL.** This breaks naive `COALESCE(regexp_extract(...), regexp_extract(...))` — COALESCE picks the `''` from the first regex and never evaluates the second. Wrap each `regexp_extract` in `NULLIF(..., '')` so COALESCE actually falls through.

```sql
-- Stars (covers 96% of rows; NULLIF is mandatory — COALESCE doesn't skip empty strings)
TRY_CAST(REPLACE(
  COALESCE(
    NULLIF(regexp_extract(Project_Information, '([0-9][0-9,]*)\s+stars', 1), ''),
    NULLIF(regexp_extract(Project_Information, 'stars\s+count\s+of\s+([0-9][0-9,]*)', 1), '')
  ), ',', '') AS INTEGER) AS stars

-- Forks (same shape; the 3rd template "forked N times" adds another ~9%)
TRY_CAST(REPLACE(
  COALESCE(
    NULLIF(regexp_extract(Project_Information, '([0-9][0-9,]*)\s+forks', 1), ''),
    NULLIF(regexp_extract(Project_Information, 'forks\s+count\s+of\s+([0-9][0-9,]*)', 1), ''),
    NULLIF(regexp_extract(Project_Information, 'forked\s+([0-9][0-9,]*)\s+times', 1), '')
  ), ',', '') AS INTEGER) AS forks
```

Observed templates (run_1 sweep, 2026-04-18):
- `"... currently has X open issues, Y stars, and Z forks ..."` (~67% of rows)
- `"... has an open issues count of A, a stars count of B, and a forks count of C ..."` (~22%)
- `"... boasting an impressive Y stars and Z forks ..."` and `"... has been forked C times"` (~9%)

**Verification before reporting:** print the top-N candidates with their raw `Project_Information` snippet — (a) any extracted star count ≤ 3 digits next to a comma in the source means the digit-run regex caught the wrong group, (b) any expected high-star project (e.g. `microsoft/typescript` ≈ 95k) showing as NULL means the `NULLIF` wrapper was forgotten and COALESCE stuck on the empty string.

## GitHub Repos (query_GITHUB_REPOS)

SQLite: `repo_metadata.db` — repos table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| repo_name | text | Repository identifier (owner/repo format) | Primary key — join to other tables |
| watch_count | int | GitHub watchers count | Popularity metric |

SQLite: `repo_metadata.db` — languages table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| repo_name | text | FK to repos | Join key |
| language_description | text | Programming language name | One row per language per repo |

SQLite: `repo_metadata.db` — licenses table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| repo_name | text | FK to repos | Join key |
| license | text | License type (MIT, Apache-2.0, etc.) | |

DuckDB: `repo_artifacts.db` — Repository content artifacts including README text. Schema TBD at runtime.

## Google Local (query_googlelocal)

PostgreSQL: `business_description` table (googlelocal_db)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| name | text | Business name | Display name — may not be unique |
| gmap_id | text | Google Maps unique ID | **Primary join key** to SQLite reviews |
| description | text | Business description | Unstructured — detailed text about the business |
| num_of_reviews | int | Total review count | Aggregate — do NOT use for average calculation |
| hours | text | Operating hours as JSON array | Semi-structured — needs JSON parsing. Array of 7 day entries |
| MISC | text | Services/amenities as JSON object | Semi-structured — nested key-value pairs |
| state | text | Location state/city | Format: "City, State" or state name |

SQLite: `review` table (review_query.db)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| name | text | **Reviewer name** (NOT business name) | Do not confuse with business name |
| time | int/text | Review timestamp | May be Unix epoch — verify format |
| rating | int | Review score (1-5) | Individual review rating |
| text | text | Full review body | Unstructured — for sentiment analysis |
| gmap_id | text | FK to business_description | Join key to PostgreSQL |

## MusicBrainz (query_music_brainz_20k)

SQLite: `tracks.db` — tracks table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| track_id | int | Unique track identifier | PK — join key to DuckDB sales |
| source_id | text | Music source/platform identifier | |
| source_track_id | text | Platform-specific track ID | |
| title | text | Song title | Used for song name lookups |
| artist | text | Artist name | Exact match — case-sensitive |
| album | text | Album name | |
| year | int | Release year | |
| length | real | Track duration | Likely in seconds |
| language | text | Song language | |

DuckDB: `sales.duckdb` — `sales` table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| sale_id | INTEGER | Primary key | |
| track_id | INTEGER | FK → SQLite `tracks.track_id` | A single canonical song is spread across multiple `track_id`s (see `business_terms.md` § Song vs track) |
| country | VARCHAR | Buyer country | Values: `Canada`, `USA`, `France`, `Germany`, `UK` (and more) |
| store | VARCHAR | Sales store | Values: `Apple Music`, `iTunes`, `Spotify`, `Amazon Music`, `Google Play` |
| units_sold | INTEGER | Units sold | |
| revenue_usd | DOUBLE | Revenue in USD for this sale row | Aggregate with `SUM(revenue_usd)` |

## PANCANCER Atlas (query_PANCANCER_ATLAS)

PostgreSQL: `clinical_info` table (pancancer_clinical)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| patient_id / bcr_patient_barcode | text | TCGA patient barcode (TCGA-XX-XXXX) | **Primary join key** to DuckDB molecular data |
| Patient_description | text | Unstructured clinical notes | May contain diagnosis details |
| days_to_birth | int | Negative integer — days from birth to diagnosis | Age = abs(days_to_birth) / 365.25 |
| days_to_death | int | Days from diagnosis to death | NULL if alive |
| age_at_initial_pathologic_diagnosis | int | Patient age at diagnosis | Direct age field — prefer this over days_to_birth |
| race | text | Patient race | Demographic data |
| ethnicity | text | Patient ethnicity | Demographic data |
| pathologic_stage | text | Cancer stage: Stage I, II, III, IV (with sub-stages) | Roman numerals — string matching |
| clinical_stage | text | Clinical staging (may differ from pathologic) | |
| histological_type | text | Tumor tissue type | Key grouping variable |
| histology | text | Broader histology classification | |
| vital_status | text | "Alive" or "Dead" | Filter for survival analysis |
| disease_type | text | Cancer type abbreviation (LGG, BRCA, etc.) | Primary cohort filter |

Note: This table has 100+ columns. DuckDB: `pancancer_molecular.db` — Gene expression data (FPKM values), mutation status.

**DB split: Clinical data (including age fields, vital status, disease type) is in PostgreSQL, NOT DuckDB.** Gene expression and molecular data is in DuckDB.

## Patents (query_PATENTS) — **COMPLETELY UNSOLVED: 0% pass@1 across all models**

**This is the hardest dataset in DAB.** No frontier model solved any Patents query in any trial (Paper Section 3.1). Primary failure: FM4 regex-based date extraction on >20 date format variants. Solving even 1 Patents query would be a novel contribution.

PostgreSQL: `cpc_definition` table (patent_CPCDefinition)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| symbol | text | CPC classification code (e.g., A01K2227/108) | Hierarchical identifier — join key |
| titleFull | text | Full classification title | Human-readable technology area name |
| titlePart | text | Partial title for this level | |
| definition | text | Detailed classification description | |
| level | int | Depth in CPC hierarchy (1-N) | Filter for level 5 = subgroup |
| parents | text | Parent CPC codes | JSON/array — hierarchical navigation. Parse with `json.loads()` |
| children | text | Child CPC codes | JSON/array — hierarchical navigation. Parse with `json.loads()` |
| status | text | Active/deprecated status | Filter for active classifications |
| dateRevised | text | Last revision date | **Use `dateutil.parser.parse()` — NOT regex** |

SQLite: `patent_publication.db` — **Warning: 5GB file.** Schema TBD at runtime.
**Date fields in this table use >20 variant formats.** Examples: "2019-03-05", "March 5, 2019", "dated 5th March 2019", "March the 18th, 2019", "filed 02/14/2020". **MUST use `dateutil.parser.parse()` or `pd.to_datetime()` — bare regex WILL fail.**

## Stock Index (query_stockindex)

SQLite: `indexInfo_query.db` — index_info table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| index_id/name | text | Index identifier | Join key to DuckDB trade data |
| Exchange | text | Stock exchange name | Map to region (Asia, Europe, etc.) |
| Currency | text | Trading currency | |

DuckDB: `indextrade_query.db` — OHLC trade data for indices. Schema TBD at runtime.

## Stock Market (query_stockmarket)

SQLite: `stockinfo_query.db` — stockinfo table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| Nasdaq Traded | text | Y/N — traded on NASDAQ | Flag field |
| Symbol | text | Ticker symbol (e.g., AAPL) | **Primary key** — join to DuckDB |
| Listing Exchange | text | Primary exchange (NYSE, NASDAQ, etc.) | |
| Market Category | text | NASDAQ market tier | |
| ETF | text | Y/N — is this an ETF | Filter OUT for individual stock queries |
| Round Lot Size | int | Standard trading lot | |
| Test Issue | text | Y/N — test security | Filter OUT test issues |
| Financial Status | text | Current financial status | |
| NextShares | text | NextShares fund indicator | |
| Company Description | text | **Unstructured** — full company description | Text field for company analysis |

DuckDB: `stocktrade_query.db` — Note: 2,754 tables (likely one per ticker).
**DuckDB contains per-ticker trade tables with OHLCV data** (date, open, high, low, close, adjusted_close, volume).
Query pattern: Look up Symbol in SQLite, then query the matching DuckDB table.

**Key facts:** `Company Description` in SQLite stockinfo is an **unstructured text field** for company business descriptions. The authoritative source for company name to ticker resolution is the SQLite stockinfo table.

## Yelp (query_yelp)

MongoDB: `business` collection (`businessinfo_database`)
| Field | Type | Semantics | Notes |
|-------|------|-----------|-------|
| business_id | string | Unique business identifier | Format: `businessid_N`. Join key to DuckDB reviews — see join_key_glossary.md § Yelp |
| name | string | Business name | Display name |
| review_count | string/int | Total review count | Stored as string — cast to int if needed |
| is_open | string | Open status | `"1"` = open, `"0"` = closed |
| attributes | dict or `"None"` | Business features | Values are **strings** (`"True"`, `"False"`, `"{'garage': False, ...}"`). Use `ast.literal_eval` to parse nested dicts. `"None"` (string) = no attribute data. |
| description | string | Natural language description | Format: `"Located at [address] in [City], [STATE], this [type] offers [categories]."` — state and categories must be extracted via string parsing |
| hours | dict | Operating hours by day | |

**Attributes interpretation:** A feature is "offered" if its key exists in `attributes` and is not `"None"`. Do NOT require a sub-value of `True` — presence of the key means the feature is listed. Example: `BusinessParking: {'garage': False, 'lot': True}` = business parking is offered.

**Category extraction from `description`:** No dedicated `categories` field exists. Extract using string split on known anchors:
```python
anchors = ["services in ", "services, including ", "services including ", "destination for "]
anchor = next((a for a in anchors if a in desc), None)
if anchor:
    cats = desc.split(anchor)[1].split(".")[0]
    cats = cats.replace(", and ", ", ").replace(" and ", ", ").split(", ")
```

**State extraction from `description`:** The format is consistently `in [City], [STATE], this...`. Use `r',\s*([A-Z]{2})\s*,'`.

DuckDB: `review` table (`user_database`)
| Field | Type | Semantics | Notes |
|-------|------|-----------|-------|
| business_ref | string | FK to MongoDB business | Format: `businessref_N` — strip prefix for join |
| rating | string/int | Review score 1–5 | Returned as string — always `pd.to_numeric()` before aggregation |
| date | string | Review date | Format: `YYYY-MM-DD HH:MM:SS` — use `LIKE '2018-%'` for year filtering |
| user_id | string | Reviewer identifier | |

---

## Book Reviews (query_bookreview) — Date/Decade extraction

**`books_info.details` (PostgreSQL):** Unstructured text field containing publication year and other metadata. To extract decade:
1. Extract year with `regexp_match(details, '\d{4}')` or `SUBSTRING(details FROM '\d{4}')` in PostgreSQL.
2. Compute decade in SQL: `CAST(FLOOR(year::int / 10) * 10 AS INTEGER)`.
3. Do NOT use Python `//` operator inside a SQL string — it is not valid SQL syntax.

---

## Authoritative Table Selection Guide

| Data Need | Authoritative Source | Wrong Source |
|-----------|---------------------|-------------|
| Article category (agnews) | MongoDB `articles.category` | Do not infer from metadata |
| Article region (agnews) | SQLite `article_metadata.region` | Not in MongoDB |
| Book language | PostgreSQL `books.language` | Not in SQLite reviews |
| Review rating | SQLite `review.rating` | Not `num_of_reviews` in PG |
| Business location | PostgreSQL `business_description.state` | Not in SQLite reviews |
| Patient disease type | PostgreSQL `clinical_info.disease_type` | Not in DuckDB molecular |
| Company name to ticker | SQLite `stockinfo.Symbol` | Not in DuckDB trade tables |
| CPC code meaning | PostgreSQL `cpc_definition.titleFull` | Not in SQLite patent data |

---

_CHANGELOG: v1.5 updated April 14 2026. Paper alignment: (1) Added Patents "COMPLETELY UNSOLVED" warning header. (2) Added date format variant examples and dateutil requirement. (3) Updated dateRevised and patent_publication notes. Prior: v1.3 (2026-04-13) bold DB split callouts and Deps Dev JSON definitions._
