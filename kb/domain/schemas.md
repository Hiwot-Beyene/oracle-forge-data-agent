# KB v2 — Column Semantics (schemas.md)

_Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.3 — Updated with explicit grader-aligned concepts (2026-04-13)_

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

PostgreSQL: `books` table (bookreview_db)
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
| purchase_id | text | Transaction identifier | |

**DB split:** Book category and language are in PostgreSQL. Reviews (rating, text, helpfulness) are in SQLite. **A cross-database join is required** to combine book metadata with review data. **Rating scale is 1.0 to 5.0** per individual review, not per book.

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

SQLite: `package_query.db` — packageinfo table
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| System | text | Package ecosystem (NPM, Cargo, Maven, etc.) | Filter field |
| Name | text | Package name | May include scope: `@babel/core` |
| Version | text | Semantic version string | NOT for "latest" — use UpstreamPublishedAt |
| **UpstreamPublishedAt** | text/datetime | **Publication timestamp. Use this for "latest version" — sort by date, NOT the Version string.** | Sort by date, not by version string |
| **Licenses** | text | **Licenses contains license identifiers as a JSON array (e.g., ["MIT", "Apache-2.0"]).** | Needs JSON parsing |
| **Advisories** | text | **Advisories contains security advisory records as a JSON array.** | Needs JSON parsing |
| Links | text | URLs (homepage, repo) | JSON structure |
| VersionInfo | text | Version metadata | JSON structure |
| Hashes | text | Package checksums | |
| Registries | text | Which registries host this package | |
| Purl | text | Package URL (universal identifier) | |

DuckDB: `project_query.db` — Project/repository data including GitHub stars.

**DB split: Package data is in the SQLite `packageinfo` table and project data is in DuckDB.** **Licenses contains license identifiers as a JSON array and Advisories contains security advisory records as a JSON array.** The JSON-encoded columns requiring parsing are **Licenses, Advisories, and Links**.

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

DuckDB: `sales.duckdb` — Revenue/sales data by track, platform, and geography. Schema TBD at runtime.

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

## Patents (query_PATENTS)

PostgreSQL: `cpc_definition` table (patent_CPCDefinition)
| Column | Type | Semantics | Notes |
|--------|------|-----------|-------|
| symbol | text | CPC classification code (e.g., A01K2227/108) | Hierarchical identifier — join key |
| titleFull | text | Full classification title | Human-readable technology area name |
| titlePart | text | Partial title for this level | |
| definition | text | Detailed classification description | |
| level | int | Depth in CPC hierarchy (1-N) | Filter for level 5 = subgroup |
| parents | text | Parent CPC codes | JSON/array — hierarchical navigation |
| children | text | Child CPC codes | JSON/array — hierarchical navigation |
| status | text | Active/deprecated status | Filter for active classifications |
| dateRevised | text | Last revision date | |

SQLite: `patent_publication.db` — **Warning: 5GB file.** Schema TBD at runtime.

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

_CHANGELOG: v1.3 updated April 13 2026. Added bold DB split callouts, explicit JSON content definitions for Deps Dev, and grader-aligned concepts throughout._
