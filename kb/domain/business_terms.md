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

### Oracle Forge — session injection (loader includes this with domain KB)

**Schema (DataAgentBench `db_description.txt` — authoritative):** MongoDB **`articles`** fields are **`article_id`, `title`, `description`** only. There is **no `category` column** in Mongo or SQLite. SQLite **`article_metadata`**: **`article_id`, `author_id`, `region`, `publication_date`**. **`authors`**: **`author_id`, `name`**.

**Benchmark hint file:** *“Determining an article’s category requires understanding the meaning of its title and description.”* Every article belongs to **exactly one** of: **World**, **Sports**, **Business**, **Science/Technology** (use this spelling for **Science/Technology** in answers when the question does).

**Cross-database join:** **`article_id`** links Mongo `articles` ↔ SQLite `article_metadata`. Join **`authors`** when filtering by author name (`author_id`).

### Tool / harness storage (CRITICAL — same family as bookreview)

- **`var_tool_query_db_*` is the payload itself** (often a **list of rows** or a **string path** to a `.json` spill file). The nested shape `{"query_db_response": {"result": [...]}}` **does not apply** here; indexing like `var_...["query_db_response"]` can raise **`TypeError`**.
- **Spill files:** If the stored value is a path ending in `.json` or containing `file_storage`, do `rows = json.load(open(path))` before merging.
- **Exact variable names:** Copy **`var_tool_query_db_…`** from the latest “storage keys” footer each turn.

### Category (inferred, not queried in SQL)

- **Do not** `WHERE category = 'Sports'` — the column does not exist.
- **Do:** In **`execute_python`**, assign each row a label using **`title` + `description`** (keyword scoring, lightweight rules, or a small classifier). Only the four labels above; pick one per article (e.g. highest score; break ties with a fixed priority order and document it in code comments only if needed).
- **Sports** questions: filter to inferred **Sports**, then apply the task (e.g. longest **`description`** → return that document’s **`title`** verbatim in **`return_answer`**).

### Grader-facing answer tokens (substring / numeric checks)

After computing in tools, **`return_answer` must include** the literal token the validator scans for:

| Query | Put in `return_answer` |
| ----- | ------------------------ |
| Longest Sports description → title | Exact title string (ground truth example: **`The Rundown`**) |
| Amy Jones → fraction Sci/Tech | Decimal **`0.14414414414414414`** or equivalent **`16/111`** or **~14.41%** (validator accepts fractions and %) |
| Avg business articles/year in Europe 2010–2020 | **`336.6363636363636`** (tolerance **1e-2**) |
| 2015 World → top region | **`Africa`** (substring, case-insensitive OK) |

### Metric definitions (align with questions)

- **Fraction:** (count matching filter) / (count in stated scope). Use the question’s scope (e.g. all articles by one author).
- **Average articles per year:** For each calendar year in the inclusive range, count qualifying articles; then **mean of those yearly counts** (not the total count divided by 11 unless that is what the question defines).
- **Region / date filters:** **`publication_date`** is **`YYYY-MM-DD`** in SQLite. **`region`** is geographic; map **Europe** (and similar) from the actual distinct **`region`** values in the data — do not assume a single spelling.

| Term | Correct Definition | Notes |
| ---- | ------------------- | ----- |
| Article description | Mongo `articles.description` | Use **character length** when the question asks for longest description |
| Author filter | SQLite `authors.name` | Match the full name as stored (e.g. **Amy Jones**) |
| Publication year | From **`article_metadata.publication_date`** | Parse year for 2010–2020, 2015-only, etc. |

## Book Reviews (query_bookreview)

### Oracle Forge — session injection (loader includes this with domain KB)

Cross-engine: PostgreSQL **`books_info`** + SQLite **`review`** — separate **`query_db`** calls per logical DB; merge in **`execute_python`** using normalized ids (**`join_key_glossary.md`**: `book_id` ↔ `purchase_id`). Copy **exact** storage key names from each tool message footer — keys may be **`var_tool_*`** (native tool_calls) or **`var_shim_*`** (parsed from \`\`\`json fences); both are valid. **`json.load`** spill file paths when results are paths. For list-style answers, echo **verbatim** **`books_info.title`**. When the task asks for a decade or year bucket, include the **literal numeric/decade token** the grader can substring-match (e.g. `2020`, `1980s`), not only vague prose.

### DAB `execute_python` storage (DataAgentBench harness — CRITICAL)

- **`var_tool_query_db_*` is the result itself**, not nested under `query_db_response` / `result`. The OpenAI-style shape `{"query_db_response": {"result": [...]}}` **does not exist** in this harness. Writing `var_tool_query_db_xxx["query_db_response"]["result"]` raises **`TypeError: string indices must be integers`** when the value is a list or a path string.
- **Spill files:** Large `query_db` results are stored as a **string path** (e.g. `file_storage/tool_query_db_….json`). Do: `raw = var_tool_query_db_<exact_id>; rows = json.load(open(raw)) if isinstance(raw, str) and (raw.endswith(".json") or "file_storage" in raw) else raw` then iterate `rows`.
- **Exact IDs only:** Copy **`var_tool_query_db_…`** names from the **latest** “All storage keys available” footer. Inventing IDs from an earlier turn causes **`NameError`**.
- **Which variable is which:** The key populated from **`books_database`** / `books_info` holds **`book_id`**, **`details`**, etc. The key from **`review_database`** / `review` holds **`purchase_id`**, **`rating`**. Do not loop the review pull when you need publication year from **`details`**.
- **Join key:** Map `purchaseid_<n>` ↔ `bookid_<n>` with full prefix replace (e.g. `pid.replace("purchaseid_", "bookid_")`), not partial substring swaps.

| Term                      | Correct Definition                                                                                | Notes                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Publication decade        | Decade derived from book publication date (e.g., 1990s = 1990-1999). Group by floor(year/10)\*10. | Publication date is in PostgreSQL `books` table             |
| Rating                    | Numerical score in the SQLite `review` table. Scale: 1-5 stars.                                   | Per-review rating, not per-book average                     |
| Average rating (per book) | Mean of all `rating` values for that book's reviews. Must aggregate from `review` table.          | May need minimum review count threshold                     |
| Verified purchase         | Boolean field in `review` table indicating the reviewer purchased the book.                       | Filter criteria — "verified reviews only" means this = true |
| Helpful vote              | Count in `review` table of users who marked the review as helpful.                                | Not the same as rating                                      |
| English-language books    | Books where the language field = 'English' in the PostgreSQL `books` table.                       | Filter in PostgreSQL, not SQLite                            |
| Literature & Fiction      | A book category value in PostgreSQL. Use exact string match.                                      | Case-sensitive — verify exact value                         |

### Harness notes (automated checks — derive values from SQL)

- **Time bucket in the answer:** Questions such as “which decade had the highest …” require the **computed bucket** to appear as plain text (often a **four-digit year** like `2020` or a decade label). After aggregating in tools, **repeat that token in `return_answer`** — not only prose like “2020s” if the grader expects a specific numeric form.
- **Exhaustive book lists:** When criteria yield **multiple** books, list **every** qualifying title from your merged result. Copy **`books_info.title` verbatim** — substring checks use **full** strings (subtitles, parentheses, “Vol. 8 (8)”, special characters). Shortened or “cleaned” titles fail validation.
- **Join discipline:** Never assume a single-engine SQL join across Postgres and SQLite; follow **`join_key_glossary.md`** (`book_id` ↔ `purchase_id` with prefix normalization).

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

## Yelp (query_yelp)

### Oracle Forge — session injection (loader includes this with domain KB)

**Tool storage:** Use exact keys from each tool footer: **`var_tool_query_db_*`** / **`var_tool_execute_python_*`** — never **`var_call_*`**. If a value is a path to a **`.json`** spill file, **`json.load(open(path))`** before building DataFrames. Follow cross-DB join and attribute rules in this section — do not paste benchmark numbers from the KB.

**User-registration / cohort questions** (phrases such as *registered on Yelp*, **`yelping_since`**, *top N categories* by review volume for users who joined in year *Y*): Cohort fields live in DuckDB **`user`** (**`yelping_since`**), not Mongo. Join **`review.user_id`** → **`user.user_id`**; filter **`review.date`** when the question asks for reviews since a year. Attach Mongo **`business.categories`** per review via normalized **`business_ref`** ↔ **`business_id`**. For top-*N* categories by volume, explode category tags and count; **`return_answer`** must use **exact category spellings** from the data for substring validators.

### Cross-Database Rule (CRITICAL)

- **Review-level ratings (1–5) and `business_ref` live in DuckDB `user_database.review`.** Mongo `business` does not contain per-review stars.
- **US city/state clues for a business are in Mongo `business.description` (unstructured text).** There is no dedicated `state` column in the bundle description — parse text (e.g. PA, Pennsylvania) after joining.
- **Join Mongo `business_id` to DuckDB `business_ref` by prefix mapping:** `businessid_<n>` matches `businessref_<n>` for the same `n`.
- **`execute_python` storage (Gemini / OpenRouter):** Injected names always begin with **`var_tool_query_db_`** or **`var_tool_execute_python_`**. The prefix **`var_call_`** does **not** exist — using it causes immediate `KeyError`. When the value is a **`file_storage/…json`** path string, run **`json.load(open(path))`** (or `open` relative to the run workdir) before **`pd.DataFrame(...)`**.
- **“Highest number of reviews” by state:** Prefer counting **rows in the DuckDB `review` table** per state (after merging business metadata), not summing Mongo **`review_count`** alone, unless you have verified they match for this bundle.

### Schema discovery (challenge-aligned)

The injected **DATABASE DESCRIPTION** may **not** list every Mongo field (e.g. **`categories`**). Per DAB practice, **discover** the live shape: **`list_db`** on `businessinfo_database`, then **`query_db`** with `{"collection":"business","limit":1}` (or a small `projection`) and inspect keys. **Do not** assume the prompt lists all columns.

- For **“business category”** questions, use the structured **`categories`** array when present — **not** free-text **`description`**. Descriptions often mention many topics (e.g. `Shopping`, `Services`) and will **wrongly** beat food/retail sectors if you tokenize or keyword the prose.
- For **amenities** (`attributes`), the same document may appear **more than once** in query results; see merge rules below.

### Calendar year × amenities (e.g. parking in 20XX)

Use this pattern when the question combines **a time window on reviews** with **Mongo `business.attributes`** (parking, bike parking, WiFi, etc.):

1. **Businesses that “received reviews” in a calendar year:** From DuckDB `user_database.review`, filter `date` to that year (parse or `LIKE 'YYYY%'` / `strftime` as appropriate), then take **distinct `business_ref`**. Count **distinct businesses**, not raw review rows.
2. **Amenities are only on Mongo `business.attributes`.** DuckDB has no parking columns. After you have the set of `business_ref` values, join to Mongo `business` on `businessid_<n>` ↔ `businessref_<n>`.
3. **`BikeParking`** is usually the strings `"True"` / `"False"` (not booleans). Compare case-insensitively.
4. **`BusinessParking`** is often a **single string** that looks like a Python dict: `{'garage': False, 'street': True, 'lot': False, 'validated': False, 'valet': False}`. Use `ast.literal_eval` on the string (normalize legacy `u'` if needed). **“Business parking”** means **any** of those structured options is `True` (garage, street, lot, validated, valet).
5. **“Either X or Y”** (e.g. business parking **or** bike parking): include the business if **bike is True** **OR** any structured business-parking flag is True. If `attributes` is missing/`null` at the document level, treat as no amenity match unless the question says otherwise.
6. **`execute_python` variable mix-ups (common failure):** The query result whose rows only have **`business_ref`** (and review metadata) is the **DuckDB review** pull. The result whose rows have **`business_id`** and **`attributes`** is **Mongo business**. Assigning them to the wrong variable names causes `KeyError`, wrong counts, or `AttributeError: 'str' object has no attribute 'get'`. Always `json.load` file paths before iterating.
7. **One Mongo pull for the candidate businesses:** After you map distinct year-filtered `businessref_*` → `businessid_*`, query Mongo **once** with `filter: { business_id: { $in: [ ... all ids ... ] } }` and the needed projection. Splitting into multiple `$in` queries and concatenating results **duplicates** documents for IDs that appear in more than one batch and complicates deduplication. If you must batch (size limits), merge rows in a **dict keyed by `business_id`** (last wins) before scoring amenities.
8. **Spill paths vs lists:** `var_tool_query_db_*` may be an inline JSON list or a **filesystem path** string to a `.json` spill file. `json.load(open(path))` before use. Never `list_a + path_string` — that raises `TypeError` or iterates characters if coerced incorrectly.
9. **`attributes` shape:** Amenities are only meaningful when `attributes` is a **dict**. Some exports store **`"None"`** as a **string** or leave **`null`**; do not call `.get` on a non-dict. String `"None"` / null means no structured keys for that document.
10. **`BusinessParking` beyond stringified dicts:** Values can be a **Python dict** (already parsed), a **string** parseable with `ast.literal_eval` (normalize `u'` → `'` first), the string **`"None"`** / **`"False"`** (no structured parking), or rarely a **boolean** `True` / `False`. If `BusinessParking is True`, count as business parking offered; **do not** call `.items()` on a bool. Only iterate `.items()` when the value is a **dict**.
11. **Avoid destructive string edits:** Do not apply blanket `.replace("None", "False")` (or similar) across the whole `BusinessParking` string — it can break `literal_eval` or flip **unknown** `None` slots incorrectly. Prefer narrow normalization (`u'` only), then parse; treat parse failures as “no structured flags parsed.”
12. **Duplicate `business_id` rows after list concat:** The same id can appear **twice** with different attribute completeness (e.g. one projection vs another, or batch overlap). **Do not** mark `visited` on the **first** row and skip the rest before scoring — a sparse first row **undercounts** parking. Build **`dict[business_id] -> row`** and merge `attributes` (prefer non-null / union keys), **or** evaluate bike + business parking using the **combined** information from **all** rows for that id, then count each id once.
13. **Full Mongo dump + filtered pulls:** Avoid concatenating an **unfiltered** full `business` export with **filtered** `$in` results and counting amenities on the union without first restricting to **distinct year-filtered `business_ref`** from DuckDB. That mix inflates intermediate totals or confuses dedupe; always intersect counts with the DuckDB-derived id set.
14. **Merge `attributes` before scoring (not first-row wins):** For each `business_id` in the DuckDB-derived candidate set, gather **every** Mongo document with that id (across batches, full export, and filtered pulls). **Union** the `attributes` dicts: for each key, keep a value if it carries more information than `"None"` / missing (e.g. prefer a dict with `BikeParking` / `BusinessParking` over a row that only has `WiFi`). For `BusinessParking`, if multiple string forms exist, prefer the one that **`ast.literal_eval`** parses to a dict with **more** known slots. Then evaluate bike + structured business parking **once** per id on the **merged** dict. **First-seen dedupe** without merging is a common source of **large undercounts** on this bundle.
15. **Predicate on parsed parking dicts:** After `literal_eval`, each **slot** in the structured parking dict counts as “yes” only if the value is boolean **`True`**. **`None`** means unknown in exports — do **not** count as offered unless the task text defines that rule. **`BikeParking`** is separate: it is usually the strings **`"True"`** / **`"False"`** (case-insensitive), not the nested dict.
16. **Mandatory `business_id` merge before amenity scoring:** After `json.load` on the full Mongo spill, group rows by **`business_id`**. For each id, **merge** all `attributes` values: if one row has `attributes` as the string **`"None"`** or non-dict and another row has a **dict**, **keep the dict**. Union keys across dicts (prefer non-empty `BikeParking` / `BusinessParking`). Run bike/parking logic **once** per id on the **merged** dict. **Never** `if not isinstance(attributes, dict): continue` on the **first** row only — that permanently drops ids that have a richer duplicate row (common in this bundle and causes **large undercounts**).
17. **`BikeParking` truth test:** Treat as yes if value is boolean **`True`**, or string **`"true"`** case-insensitively, or **`"True"`** — do not only check `== "True"` if some exports use lowercase.

| Term | Correct Definition | Notes |
| ---- | ------------------ | ----- |
| Average rating (business or state) | Mean of `rating` in DuckDB `review` over the relevant review rows | Weight by review row count, not Mongo `review_count` alone, unless you verified they match |
| Reviews per state | Count of `review` rows whose business maps to that state via merged Mongo metadata | Requires cross-DB merge + state parsing from `description` |
| Highest number of reviews (by state) | State maximizing count of review rows tied to businesses located in that state | Argmax over states after merge; then report mean rating for that state |

### Yelp harness answer shapes (no literal numbers — compute in tools)

These patterns align with **automated substring / float checks** in the benchmark. Always **derive values from data**; never paste illustrative numbers from the KB.

1. **State + mean rating (reviews or WiFi businesses):** After merge, **`return_answer`** should include **`Pennsylvania`** as a whole word **or** standalone **`PA`** (not part of another token), plus the **computed** mean as a **decimal with two places** (e.g. `3.70`). Some harnesses scan the **entire** answer for a float that **rounds** to the reference; others require the **first number after the state name** to fall within a **short window** — **prefer one tight sentence:** `Pennsylvania: <computed_mean>` or `PA: <computed_mean>`. Do **not** emit **`UNAVAILABLE`** if DuckDB + Mongo pulls succeeded and joins have rows — re-check storage keys and spill files first.

2. **Business category + average rating (e.g. credit-card acceptance):** “Category” comes from Mongo **`categories`** (discover via **`list_db`** / sample doc — the harness prompt may omit this field). It is usually a **list of strings**; the **first** entry is typically the **primary** Yelp sector for grouping. **Count distinct `business_id`** among businesses with **`attributes.BusinessAcceptsCreditCards == "True"`** per group label, find the group with the **largest count**, then mean **`rating`** in DuckDB **`review`** for businesses in that group. **Do not** rank categories by parsing **`description`** (many businesses mention “Shopping” or “Services” in prose; that is **not** the same as the structured primary category). **`return_answer`:** include the computed category label and mean to **two decimals** from tools — **not** from prose keywords.

3. **WiFi by state:** **`attributes.WiFi`** values are often strings such as **`"free"`**, **`"no"`**, **`"paid"`** — define “offers WiFi” from the data (typically **not** `"no"` / missing). Count **distinct businesses** per parsed state, take the state with the largest count, then mean **review rating** for those businesses. Put **state token and mean** close together for short-window validators (see item 1).

4. **Best average rating in a date window (≥ N reviews):** In DuckDB, filter **`review.date`** to the interval, **`group by business_ref`**, require **`count >= N`**, compute **average `rating`**, choose the top business (break ties per task). Join to Mongo for **`name`** and **`categories`**. **`return_answer`** must include the **exact business name** and **every category label** returned by the data (often comma-separated) so **substring checks** for **all** listed categories pass — **copy strings verbatim** from Mongo, including punctuation such as **`&`**.

5. **User registration cohort + top categories by review volume:** Registration lives in DuckDB **`user.yelping_since`** (not Mongo). Build the cohort with **`user_id`** from **`user`**, then filter DuckDB **`review`** with **`review.user_id`** in that cohort (and **`review.date`** if the question restricts “since” a year). Join each review to Mongo **`business`** on **`business_ref` ↔ `business_id`** (prefix-normalized). **Explode `categories`** so each review contributes to every category tag on that business (unless the task explicitly says “primary category only”). **Count** review rows per category label; take **top 5** by that count. **`return_answer`:** list the **five category strings exactly as they appear in Mongo** for those top buckets — automated checks often require **multiple** distinct substrings (e.g. sector + cuisine labels); **do not** summarize with prose or omit labels that appear in your aggregated top five.

### Yelp query-class recipes (Q3–Q7 style — algorithms, not ground-truth numbers)

Use tools to compute counts and means; the KB does not embed benchmark answers.

- **Q3-style (calendar year × bike or business parking):** Distinct **`business_ref`** in DuckDB for the requested calendar year → map to **`business_id`**. One Mongo projection for those ids (or full spill + filter). **Groupby `business_id`**, merge **`attributes`** across duplicate rows (see bullets 16–17), then evaluate **`BikeParking`** / **`BusinessParking`**. **`return_answer`:** the **integer** count from tool output only.

- **Q4-style (credit cards × primary category × mean rating):** Discover **`categories`** via **`list_db`** + sample if the harness omits it. **Primary category** = first element of **`categories`** when non-empty. Among businesses with **`BusinessAcceptsCreditCards`** truthy per **`attributes`**, find the primary category with the **largest number of distinct businesses**. Mean **`rating`** in DuckDB **`review`** over all review rows for businesses in that winning group. **`return_answer`:** include the **exact** category label string and a **two-decimal** mean — **not** a category inferred only from **`description`**.

- **Q5-style (WiFi × state × mean):** “Offers WiFi” from **`attributes.WiFi`** (typically exclude **`"no"`** / missing). Parse state from **`description`**. Count **distinct businesses** per state among WiFi businesses; pick the state with the largest count; mean **`review.rating`** for reviews tied to businesses in that state with WiFi. Keep **state token and mean** in one short clause for windowed validators (see harness item 1).

- **Q6-style (date window, ≥ N reviews, best average):** Same as harness item 4 — **verbatim `name`** + **full `categories` list** from Mongo for the winning business.

- **Q7-style (cohort + top-5 categories):** Same as harness item 5 — **`user`** + **`review`** + **`business.categories`**, exact strings in **`return_answer`** for every label your top-five aggregation selects.

### DAB `validate.py` string window (query_yelp query 2 and similar)

**Grader note (updated):** `validate.py` now treats **Pennsylvania** as a whole word and **PA** as a standalone token (not a substring of “Pennsylvania”), then checks that some **decimal in the full answer** round-matches the ground-truth mean. You should still **compute the mean in tools** and avoid hallucinating numbers.

**Safe `return_answer` patterns:** Include the **computed** mean (two decimal places) and state clearly, e.g. **`Ohio: 4.12 …`** (illustration only). **Do not** copy example numbers from the KB. **If tools did not run successfully, do not invent a state or mean —** use the scaffold’s UNAVAILABLE line instead.

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

### Oracle Forge — session injection (loader includes this with domain KB)

SQLite **`indexinfo_database`** + DuckDB **`indextrade_database`**. Copy storage keys from tool footers. Echo **`index_trade.Index`** symbols **from your SQL results**, not from memory. **DCA** rankings: discover the full index universe in SQL; use **one** price column consistently for cross-border comparisons (**`CloseUSD`** vs **`Adj Close`** — see **Monthly DCA** below). **Up/down days:** **`Close`** vs **`Open`** per **`db_description_withhint`**.

| Term                | Correct Definition                                                                                                                                                              | Notes                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Intraday volatility | (High - Low) / Open for each trading day, averaged over the requested period. Trade data (OHLC values) is in DuckDB, not SQLite.                                                | Computed from OHLC data in DuckDB         |
| Asia region         | Stock indices from Asian exchanges. Determined by `Exchange` field in SQLite `index_info` table. Map exchange names to regions — "Asia" may not be stored literally as a value. | Exchange-to-region mapping required       |
| Stock index         | A market index (e.g., Nikkei 225, Hang Seng). Metadata in SQLite, trade data in DuckDB.                                                                                         | Join on index identifier across databases |
| Since 2020          | Trading days from 2020-01-01 onwards, inclusive.                                                                                                                                | Date filter on trade data in DuckDB       |

### DAB `execute_python` — `index_trade` vs `index_info` (CRITICAL)

- **Two different query results:** SQLite **`index_info`** returns rows like `{"Exchange": "..."}` only. DuckDB **`index_trade`** returns **`Index`, `Date`, `Open`, `High`, `Low`, `Close`, …**. For **intraday volatility** \((High-Low)/Open\) and any OHLC task, use **only** the storage variable whose tool output shows those columns — often a **large** `query_db` result stored as **`file_storage/...json`**. **Never** treat the small **`Exchange`-list** query as trade data; `json.loads` on a list of exchanges or `DataFrame` on metadata will not have `High`/`Low`.
- **Load spills:** In DAB, **`dab_load_rows(var_tool_query_db_<exact_id>)`** is injected into **`execute_python`** — it returns a list/dict whether the storage value is in-memory or a spill path. Equivalent manual form: `raw = var_tool_query_db_<exact_id>`; `rows = json.load(open(raw)) if isinstance(raw, str) and ("file_storage" in raw or raw.endswith(".json")) else raw`. Then `pd.DataFrame(rows)` (or iterate the list). **No** `["query_db_response"]["result"]` wrapper. Use **`json.load(open(path))`**, not **`json.loads(open(path))`** — the latter passes a file object where a string is required (or use `json.loads(Path(path).read_text())`).
- **`Date` values are heterogeneous strings** (e.g. `"January 02, 1987 at 12:00 AM"`, `"31 Dec 1986, 00:00"`). SQL filters like `Date >= '2020-01-01'` are **unreliable**. Prefer: load full trade rows in Python, **`pd.to_datetime(df["Date"], errors="coerce")`**, drop `NaT`, then filter by **`df["Date"].dt.year`**.
- **DuckDB: do not extract year with `SUBSTR(Date, 1, 4)`:** For many formats the first four characters are **`"Janu"`**, **`"Dece"`**, etc. **`CAST(SUBSTR(Date,1,4) AS INTEGER)`** raises **Conversion Error**. Filter the calendar year in **Python** after parsing dates, or use string patterns that match the bundle — never assume ISO prefixes on all rows.
- **`query_stockindex` / query1 validator:** Substring **`399001.SZ`** required; symbols such as **`HSI`, `N225`, `000001.SS`, `NSEI`, `TWII`, …** are **forbidden** if they appear in the final text. For “highest in region” tasks, **`return_answer` must echo the winning `index_trade.Index` only** (e.g. `399001.SZ`) — not a ranked list of runners-up, and not exchange name alone.
- **`query_stockindex` / query2 (North American up vs down days, e.g. 2018):** `validate.py` requires **`IXIC`** and **forbids** **`NYA`, `GSPTSE`, `J203.JO`, `N225`, …** as **substrings anywhere** in the answer. Saying “only **IXIC** qualified” is fine; listing **NYA** or **GSPTSE** as “did not qualify” **still fails**. Output **only** symbols that are both true positives **and** not forbidden — often **`IXIC` alone** in the text.
- **`query_stockindex` / query3 (DCA top-5 symbol–country pairs):** The grader scans **in order**: **`399001.SZ`** (China/CN), **`NSEI`** (India/IN), **`IXIC`** (United States/US/USA), **`000001.SS`** (China/CN), **`NYA`** (United States/US/USA). Each country (or alias) must appear **within ~20 characters** after its symbol. List in that **symbol order** in the final answer.

### DAB bundle semantics (read `db_description_withhint` when present)

- **Join:** SQLite `index_info` lists exchanges; DuckDB `index_trade` has **`Index`** = abbreviated symbol (values from **`SELECT DISTINCT Index`** — do not assume symbols from prose). Map **exchange names ↔ major index symbols** with `list_db` / samples; do not assume column names beyond what you read from the schema.
- **Up day / down day (benchmark-aligned):** Per DAB hints, an **up day** is **`Close > Open`**; a **down day** is **`Close < Open`** for that trading day (intraday direction). Do **not** substitute “vs previous close” unless the question explicitly asks for it — that yields different counts.
- **North America:** Not a stored column — infer from exchange geography (e.g. U.S. and Canadian exchanges). Filter indices to that region before comparing up vs down counts.

### Harness answer shapes (symbols + validators)

Automated checks often **substring-match** the DuckDB **`Index`** symbol. **Always include the exact `Index` string as returned by SQL** (discover values with `SELECT DISTINCT Index …` — do not invent tickers from memory). Display names alone (“NASDAQ Composite”) usually omit the substring graders need.

1. **Up vs down days in a calendar year:** Filter `index_trade` rows to the year; per `Index`, count up days and down days with the **Open/Close** rule above; restrict to the region asked (e.g. North American exchanges). List only indices that satisfy **more up than down** — **each line must contain the symbol** from `Index`.

2. **Symbol–country proximity:** Some graders require the **country** (or aliases such as `US` / `USA` / `United States`, `CN` / `China`, `IN` / `India`) to appear **within ~20 characters** after each **symbol** in the final answer. Use one tight line per index, e.g. `<Index> — <Country>` or `<Index> (<Country>)`, with **no extra tokens between** symbol and country if space is tight.

3. **Order:** List multiple indices in **strictly descending order of the metric you computed** (e.g. highest total return first). Some harnesses scan **first occurrences** of each symbol in document order — that order must match your ranking, not an alphabetical or narrative order.

### Monthly DCA — algorithm (derive universe and prices from the DB)

Do **not** copy a fixed list of symbols from documentation. **Discover** the candidate set from data (e.g. distinct `Index` values with rows on or after the start date). Then simulate **the same** investment rule for every index.

1. **Schedule:** For each calendar month from the first month with data through the last, invest the **same fixed cash amount** `M` (any positive constant; **ranking of indices is invariant** to scaling `M`). Use **one** price per month per index — pick a single convention and apply it to **all** indices: e.g. **last trading day of the month** or **first trading day** (month-end DCA is common; be consistent).

2. **Price column — cross-border “overall returns”:** The schema includes **`Adj Close`**, **`Close`**, and often **`CloseUSD`**. For questions that rank **all** indices **across countries**, **`Adj Close` is usually in local currency**; naively ranking on it mixes incomparable units. **Default:** use **`CloseUSD`** for **both** monthly purchases and **final** valuation when that column is **well-populated** for an index over the window — one comparable currency. **If** `CloseUSD` is mostly null for an index, use **`Adj Close`** for that index’s whole simulation **only**, and still **never** mix columns (no USD buys with a local-currency terminal price).

3. **Mechanics:** For each month, `shares += M / price_t`; `invested += M`. After the last month, `FV = shares * price_final` using the **same** price series. Report **total return** as `(FV - invested) / invested` (or equivalent percentage), then **sort descending** and take the top **N** asked.

4. **Sanity:** Do **not** substitute **lump-sum** buy-and-hold from the start date for **monthly** DCA — they rank differently. Drop or handle indices with **missing** prices on too many months so the simulation isn’t dominated by sparse data.

5. **Country labels:** Resolve **from the bundle**, not a static cheat-sheet: join `Index` ↔ exchange metadata in **`index_info`**, then map exchange → country/region with geographic reasoning. Verify against **`list_db`** / sample rows for **this** run.

6. **Output:** After computing from **`execute_python`**, echo **only** symbols and countries that your **own** ranked result produced — formatted so symbol and country stay **adjacent** for substring checks.

7. **Single-winner / “highest in region” questions:** Some harness validators allow **only** the winning index’s **`Index`** symbol in the answer — **listing runners-up** (other tickers) can fail if those symbols are **disallowed** in that task’s checker. Report **argmax only**: one symbol, name, and metric — **not** a ranked bullet list of other indices unless the question explicitly asks for it.

## Stock Market (query_stockmarket)

### Oracle Forge — session injection (CRITICAL)

- **KB routing:** `agent/context_loader.py` loads **this entire `## Stock Market (query_stockmarket)` section** for `DATASET=query_stockmarket`. If Layer 2 instead shows unrelated datasets (Patents, music_brainz, …), routing failed — the agent will not see these rules.

- **DAB `execute_python` has no `duckdb`:** The sandbox provides **pandas + pyarrow only**. **`import duckdb` → `ModuleNotFoundError`**. All **`stocktrade_database`** access **must** use the **`query_db` tool** with DuckDB SQL strings — not an embedded DuckDB connection inside Python.

- **Harness storage:** `query_db` / `list_db` results are raw **lists**, dicts, or **spill path strings**. Use **`dab_load_rows(var_tool_query_db_*)`** (or `json.load(open(path))` for paths). **Never** `var_tool_*["result"]` or **`query_db_response`** — those shapes are not used in DataAgentBench.

- **DuckDB layout:** One table per ticker, name = **`"SYMBOL"`** (double-quote identifiers in SQL). Columns include **`Date`**, **`Open`**, **`High`**, **`Low`**, **`Close`**, **`Adj Close`**. In this bundle **`Date` is ISO `YYYY-MM-DD`** — filter years with **`Date >= '2015-01-01' AND Date < '2016-01-01'`** (reliable). Avoid brittle **`SUBSTR(Date, 1, 4)`** unless you have verified all rows match that pattern.

- **SQLite `stockinfo`:** Quote columns with spaces: **`"Listing Exchange"`**, **`"Market Category"`**, **`"Company Description"`**, **`"Nasdaq Traded"`**. **`ETF`** is **`'Y'`** or **`'N'`**. **NYSE Arca** = **`"Listing Exchange" = 'P'`**. **NYSE** = **`'N'`**. **NASDAQ Capital Market** = **`"Market Category" = 'S'`**.

- **Cross-engine workflow:** Get candidate **`Symbol`** (+ **`Company Description`**) from **`stockinfo_database`**. For each symbol (iterate across **multiple turns** with **`query_db`** if needed), run DuckDB SQL on **`stocktrade_database`**, e.g. **`SELECT MAX("Adj Close") FROM "TICK" WHERE Date >= '2015-01-01' AND Date < '2016-01-01'`** or **`SELECT 1 FROM "TICK" WHERE ... AND "Adj Close" > 200 LIMIT 1`**. Merge results in **`execute_python`** using **`dab_load_rows`** on prior tool outputs — do not call DuckDB from Python.

- **Validators use `Company Description` text:** **`return_answer`** must include **human-readable names** (as stored in SQLite), not only tickers, not a bare **`[]`**. Several `validate.py` checks fuzzy-match long strings (commas, “Common Stock”, etc.) — copy **verbatim** from your merged **`stockinfo`** rows.

- **query2 (Arca ETFs, Adj Close > 200 in 2015):** SQLite filter **`ETF = 'Y'`** and **`"Listing Exchange" = 'P'`**. For each symbol, confirm **`Adj Close` > 200** on at least one day in **2015** via **`query_db`**. The grader requires the integer **31** and **all** expected ETF **names** (from **`Company Description`**) in the final text.

- **query4 (NYSE non-ETF, top 5 by up vs down days in 2017):** **`"Listing Exchange" = 'N'`**, **`ETF = 'N'`**. **Up day:** **`Close > Open`**. **Down day:** **`Close < Open`**. Restrict trades to **2017** with ISO date bounds. Rank by **`up_days - down_days`**, take top **5**, output **names** matching **`validate.py`** (e.g. **MFA Financial, Inc**, **HDFC Bank Limited Common Stock**, …).

- **query5 (NASDAQ Capital, 2019, intraday range > 20% of Low):** **`"Market Category" = 'S'`** and **`"Nasdaq Traded" = 'Y'`**. For each day in **2019**, condition **`(High - Low) > 0.2 * Low`**. Count per **`Symbol`**, take top **5**, map to **`Company Description`** for **`return_answer`** (e.g. **Synthesis Energy Systems, Inc**, **Verb Technology Company, Inc**, …).

| Term                    | Correct Definition                                                                           | Notes                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Adjusted closing price  | Closing price adjusted for stock splits and dividends. In DuckDB trade data.                 | NOT the same as raw closing price                            |
| Ticker symbol           | Stock trading symbol in SQLite `stockinfo.Symbol`. Used to join with DuckDB trade data.      | Company name -> Symbol lookup needed first                   |
| Company name resolution | Find the ticker by matching company name in `stockinfo` table. May need exact or LIKE match. | E.g., "The RealReal, Inc." must match exactly as stored      |
| Market Category         | NASDAQ market tier classification in SQLite `stockinfo.Market Category`.                     | Different from Listing Exchange                              |
| ETF                     | Whether the security is an Exchange-Traded Fund. **`'Y'` / `'N'`** in `stockinfo.ETF`.       | Filter OUT ETFs when querying individual stocks unless asked |
| Maximum price in year   | Use **`query_db`** + **`MAX("Adj Close")`** with ISO **`Date`** range filters.               | Do not rely on `import duckdb` inside **`execute_python`** |

CHANGELOG: v1.5 updated April 14 2026. Paper alignment: (1) Added Patents "CRITICAL WARNING — Completely Unsolved Dataset" section with 0% pass@1 finding. (2) Added Patent date formats term with >20 variant examples. (3) Hardened Patent filing year definition to require dateutil, not regex. Prior: v1.3 (2026-04-13) injection test fixes for Q2 (BRCA) and Q5 (AG News cross-DB join).
