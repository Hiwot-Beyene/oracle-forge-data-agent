# KB v2 — Domain Term Glossary (business_terms.md)

Oracle Forge | Intelligence Officers | April 2026
Status: v1.5 — Paper-aligned: Patents 0% warning, date extraction rules, FM4 mitigations (2026-04-14)

## How to Use This File

Before computing ANY metric or applying ANY filter, check this glossary.
If a term is listed here, use the definition given — not your assumption.
If a term is NOT listed, state your assumed definition in the answer and log it to KB v3.

## Cross-Domain Terms

| Term                  | Domain          | Correct Definition                                                                                                                                                                       | Common Wrong Assumption                                  |
| --------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Churn                 | Telecom/SaaS    | Customer who cancelled or became inactive. Dataset-specific — always verify the status field and time window used.                                                                       | Any customer who didn't purchase this month              |
| Active account        | Finance/Telecom | Status code = specific values per dataset. Check the actual status field values. Never infer from field name alone.                                                                      | Any account with status != 'closed'                      |
| Repeat purchase rate  | Retail          | (Customers with >=2 purchases in time window) / (Total unique customers in same window). Ratio of customers, not transactions. CRITICAL: Always verify the time window before computing. | Total purchases / total customers                        |
| Pass@1                | Benchmarking    | Fraction of queries where at least 1 of N trials returns the correct answer on the first attempt.                                                                                        | Average accuracy across all trials                       |
| Fiscal year           | Finance         | May NOT align with calendar year (Jan-Dec). Always verify fiscal year start/end dates from the data before applying time filters.                                                        | Calendar year Jan 1 - Dec 31                             |
| Support ticket volume | CRM             | Count of tickets opened in the specified period. Clarify whether resolved, unresolved, or all tickets are requested.                                                                     | Simple COUNT(\*) of all ticket rows regardless of status |
| Average rating        | Reviews         | Arithmetic mean of rating values. Verify rating scale (1-5 vs 1-10) and whether to weight by helpfulness or recency.                                                                     | Simple mean without checking scale or weighting          |
| Intraday volatility   | Finance         | (High - Low) / Open for a single trading day, then averaged over the period. Measures price movement within each day.                                                                    | Standard deviation of closing prices                     |

## AG News (query_agnews)

### Cross-Database Join Rule (CRITICAL)

- **Category is stored in the MongoDB `articles` collection** with exactly four valid values: Sports, Business, Science/Technology, and World.
- **WARNING: There are ONLY four categories. The agent must NOT assume or accept any category values beyond Sports, Business, Science/Technology, and World. No other categories exist in this dataset.**
- **Region is stored in the SQLite `article_metadata` table**, not in MongoDB.
- **A cross-database join on `article_id` is required to combine category and region data.**

| Term                   | Correct Definition                                                                                          | Notes                                                          |
| ---------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Article description    | The `description` field in MongoDB `articles` collection. This is the article body text, not a summary.     | Unstructured — may need text analysis                          |
| Article count per year | Count of distinct articles published in a calendar year. Use `publication_date` from SQLite metadata table. | The date is in metadata (SQLite), not articles (MongoDB)       |
| Fraction of articles   | (Count matching filter) / (Total count in scope). Return as decimal unless query specifies percentage.      | Clarify scope: all articles, or articles by a specific author? |

## Book Reviews (query_bookreview)

| Term                      | Correct Definition                                                                                | Notes                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Publication decade        | Decade derived from book publication date (e.g., 1990s = 1990-1999). Group by floor(year/10)\*10. | Publication date is in PostgreSQL `books` table             |
| Rating                    | Numerical score in the SQLite `review` table. Scale: 1-5 stars.                                   | Per-review rating, not per-book average                     |
| Average rating (per book) | Mean of all `rating` values for that book's reviews. Must aggregate from `review` table.          | May need minimum review count threshold                     |
| Verified purchase         | Boolean field in `review` table indicating the reviewer purchased the book.                       | Filter criteria — "verified reviews only" means this = true |
| Helpful vote              | Count in `review` table of users who marked the review as helpful.                                | Not the same as rating                                      |
| English-language books    | Books where the language field = 'English' in the PostgreSQL `books` table.                       | Filter in PostgreSQL, not SQLite                            |
| Literature & Fiction      | A book category value in PostgreSQL. Use exact string match.                                      | Case-sensitive — verify exact value                         |

## CRM Arena Pro (query_crmarenapro)

| Term               | Correct Definition                                                                                                  | Notes                                                           |
| ------------------ | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| BANT               | Lead qualification framework: Budget, Authority, Need, Timeline. A lead is qualified only if all 4 factors are met. | Must check each factor individually from support/activity data  |
| Lead qualification | Determining if a prospect meets BANT criteria based on latest discussions and activity history.                     | Requires text analysis of call transcripts and support articles |
| Account            | A company/organization record in SQLite `core_crm.Account` table. Has NumberOfEmployees, ShippingState, etc.        | Not the same as a user or contact                               |
| Contact            | An individual person associated with an Account. Linked via `AccountId`.                                            | Multiple contacts per account                                   |
| Order compliance   | Whether an order's cost and setup comply with company pricing policy defined in `Pricebook2` and `PricebookEntry`.  | Cross-reference Order -> PricebookEntry -> Product2             |
| Territory          | Geographic sales territory from SQLite `territory.db`.                                                              | Separate database from core CRM                                 |
| Sales pipeline     | Sales funnel stages tracked in DuckDB `sales_pipeline.duckdb`.                                                      | Different DB from core CRM data                                 |

## Deps Dev (query_DEPS_DEV_V1)

| Term                   | Correct Definition                                                                                                          | Notes                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Latest release version | The most recent version of a package by `UpstreamPublishedAt` date — sort by date. NOT the highest semantic version number. | Sort by date, not by version string           |
| System                 | Package ecosystem: NPM, Cargo, Maven, PyPI, Go, NuGet, etc. Stored in `packageinfo.System`.                                 | Filter by exact system name                   |
| GitHub stars           | Popularity metric. GitHub stars are in the DuckDB project_database, NOT in the SQLite package database.                     | Cross-DB: packages in SQLite, stars in DuckDB |
| Advisory               | Security vulnerability associated with a package version. Stored as JSON/array in `Advisories` column.                      | May need JSON parsing                         |
| License                | Software license(s) for a package. Stored in `Licenses` column, may be JSON array.                                          | Multiple licenses possible per package        |

## GitHub Repos (query_GITHUB_REPOS)

| Term                            | Correct Definition                                                                                      | Notes                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Repository language             | Programming language(s) used in a repo. Stored in SQLite `languages` table with `language_description`. | One repo can have multiple languages                   |
| "Does not use Python"           | Repo has no entry in `languages` table where language = 'Python'.                                       | Check for absence in `languages`, not for a flag       |
| Copyright information in README | README.md content contains the word "copyright" (case-insensitive).                                     | Requires text search in DuckDB artifacts               |
| Watch count                     | Number of GitHub watchers. Stored in SQLite `repos.watch_count`.                                        | Popularity metric — different from stars               |
| Proportion                      | (Count matching criteria) / (Total count). Return as decimal or percentage as specified in the query.   | Verify whether result should be fraction or percentage |

## Google Local (query_googlelocal)

| Term                      | Correct Definition                                                                                                                         | Notes                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| Average rating (business) | Mean of all review `rating` values for that business from SQLite `review` table.                                                           | Not the `num_of_reviews` in PostgreSQL                  |
| Business location         | State/city from PostgreSQL `business_description.state` field. Format varies: "City, State" or just state name.                            | Filter with LIKE or exact match depending on query      |
| Operating hours           | JSON array in PostgreSQL `business_description.hours` field. Each element = one day's hours.                                               | Requires JSON parsing — stored as TEXT, not native JSON |
| MISC (services/amenities) | JSON object in PostgreSQL `business_description.MISC` field. Contains service options, accessibility, amenities as nested key-value pairs. | Requires JSON parsing                                   |
| Top N businesses          | Ranked by the metric specified (usually average rating). Ties broken by num_of_reviews descending unless stated otherwise.                 | Verify tie-breaking criteria per query                  |

## MusicBrainz (query_music_brainz_20k)

| Term               | Correct Definition                                                                                    | Notes                                            |
| ------------------ | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Revenue            | Sales revenue in USD from DuckDB `sales_database`. Attributed to tracks by join on track identifiers. | Revenue is in DuckDB, track metadata in SQLite   |
| Platform           | Music streaming/sales platform (e.g., Apple Music, Spotify). Stored in DuckDB sales data.             | Filter by exact platform name                    |
| Track              | A single song/recording. Identified by `track_id` in SQLite `tracks` table.                           | Has title, artist, album, year, length, language |
| Artist matching    | Match by exact artist name string in `tracks.artist`.                                                 | Case-sensitive unless query specifies otherwise  |
| Geographic revenue | Revenue filtered by country/region in DuckDB sales data (e.g., "in Canada").                          | Country is in sales data, not track metadata     |

## PANCANCER Atlas (query_PANCANCER_ATLAS)

### BRCA Definition Warning (CRITICAL)

- **BRCA stands for Breast Invasive Carcinoma** in the PANCANCER Atlas context.
- **It is a cancer type abbreviation used to filter the `disease_type` column in PostgreSQL clinical data.**
- **The dangerous misinterpretation is confusing it with the BRCA gene.**
- **It is NOT the BRCA gene, it is the cancer type abbreviation.**

| Term                         | Correct Definition                                                                                                   | Notes                                                        |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| LGG                          | Low-Grade Glioma — a brain cancer type. Filter by disease type column in PostgreSQL clinical data.                   | Disease type abbreviation, not a gene                        |
| Histological type            | Tissue classification of the tumor (e.g., Astrocytoma, Oligodendroglioma). In `histological_type` column.            | Multiple types per cancer — used for grouping                |
| Log10-transformed expression | Apply log10() to gene expression FPKM values from DuckDB. Use log10(value + 1) if zeros are present to avoid log(0). | Gene expression is in DuckDB, clinical data in PostgreSQL    |
| Gene symbol                  | Standard HUGO gene name (e.g., IGF2, CDH1). Used as column or identifier in DuckDB molecular data.                   | Case-sensitive — use exact symbol                            |
| Mutation percentage          | (Patients with mutation in cohort) / (Total patients in cohort) \* 100. Define the cohort precisely first.           | Numerator and denominator must use same cohort filters       |
| Vital status                 | Patient alive/dead. Values: "Alive", "Dead" in PostgreSQL clinical data.                                             | Filter before computing metrics on living/deceased patients  |
| Chi-square test              | Statistical test for association between two categorical variables. Use `scipy.stats.chi2_contingency`.              | Requires `execute_python` tool — cannot do in SQL alone      |
| Pathologic stage             | Cancer staging: I, II, III, IV with possible sub-stages (e.g., Stage IIA). Roman numerals in PostgreSQL.             | Handle string matching carefully — "Stage II" != "Stage IIA" |

## Patents (query_PATENTS)

### CRITICAL WARNING — Completely Unsolved Dataset

**Patents achieved 0% pass@1 across ALL frontier models in DAB evaluation (Paper Section 3.1).** No agent solved any Patents query in any trial. The primary failure is FM4: regex-based date extraction cannot handle the >20 date format variants in this dataset.

| Term                             | Correct Definition                                                                                   | Notes                                                      |
| -------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| CPC code                         | Cooperative Patent Classification code. Hierarchical: Section > Class > Subclass > Group > Subgroup. | PostgreSQL `cpc_definition` table stores the hierarchy     |
| CPC level 5                      | The 5th depth level in CPC hierarchy (subgroup level). Filter by `level` column in cpc_definition.   | Specific depth — not the first 5 characters of the code    |
| Exponential moving average (EMA) | EMA*t = alpha * value_t + (1 - alpha) * EMA*(t-1). Initialize EMA_0 = first value.                   | Alpha (smoothing factor) specified per query, e.g., 0.2    |
| Patent filing year               | Year extracted from filing/publication date in SQLite `patent_publication` table. **MUST use `dateutil.parser.parse()` or `pd.to_datetime()` — regex `\d{4}` WILL fail on formats like "dated 5th March 2019" or "March the 18th, 2019".** | Large dataset (5GB) — use efficient filtered queries. **Never use bare regex for date extraction.** |
| Technology area                  | Human-readable area name. Map CPC codes to names via `titleFull` in PostgreSQL cpc_definition.       | Join patent CPC code -> cpc_definition.symbol -> titleFull |
| Patent date formats              | >20 variants observed: "2019-03-05", "March 5, 2019", "dated 5th March 2019", "March the 18th, 2019", "filed 02/14/2020", "5.3.19". **Regex cannot handle these — use `dateutil.parser.parse()`.** | This is the #1 reason Patents is unsolved in DAB |

## Stock Index (query_stockindex)

| Term                | Correct Definition                                                                                                                                                              | Notes                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Intraday volatility | (High - Low) / Open for each trading day, averaged over the requested period. Trade data (OHLC values) is in DuckDB, not SQLite.                                                | Computed from OHLC data in DuckDB         |
| Asia region         | Stock indices from Asian exchanges. Determined by `Exchange` field in SQLite `index_info` table. Map exchange names to regions — "Asia" may not be stored literally as a value. | Exchange-to-region mapping required       |
| Stock index         | A market index (e.g., Nikkei 225, Hang Seng). Metadata in SQLite, trade data in DuckDB.                                                                                         | Join on index identifier across databases |
| Since 2020          | Trading days from 2020-01-01 onwards, inclusive.                                                                                                                                | Date filter on trade data in DuckDB       |

## Stock Market (query_stockmarket)

| Term                    | Correct Definition                                                                           | Notes                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Adjusted closing price  | Closing price adjusted for stock splits and dividends. In DuckDB trade data.                 | NOT the same as raw closing price                            |
| Ticker symbol           | Stock trading symbol in SQLite `stockinfo.Symbol`. Used to join with DuckDB trade data.      | Company name -> Symbol lookup needed first                   |
| Company name resolution | Find the ticker by matching company name in `stockinfo` table. May need exact or LIKE match. | E.g., "The RealReal, Inc." must match exactly as stored      |
| Market Category         | NASDAQ market tier classification in SQLite `stockinfo.Market Category`.                     | Different from Listing Exchange                              |
| ETF                     | Whether the security is an Exchange-Traded Fund. Boolean in `stockinfo.ETF`.                 | Filter OUT ETFs when querying individual stocks unless asked |
| Maximum price in year   | MAX(adjusted_close) WHERE year(date) = specified year. From DuckDB trade data.               | Aggregate over all trading days in that calendar year        |

CHANGELOG: v1.5 updated April 14 2026. Paper alignment: (1) Added Patents "CRITICAL WARNING — Completely Unsolved Dataset" section with 0% pass@1 finding. (2) Added Patent date formats term with >20 variant examples. (3) Hardened Patent filing year definition to require dateutil, not regex. Prior: v1.3 (2026-04-13) injection test fixes for Q2 (BRCA) and Q5 (AG News cross-DB join).
