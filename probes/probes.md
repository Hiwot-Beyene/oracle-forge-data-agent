# Adversarial Probe Library

## Purpose
Structured queries designed to expose specific failure modes in the DAB data agent. Each probe targets one of DAB's four hard requirement categories and documents the expected failure, observed behavior, fix applied, and resulting score improvement.

## Summary Statistics

| Category | Probes Count | Baseline Pass Rate | Fixed Pass Rate | Improvement |
|----------|--------------|-------------------|-----------------|-------------|
| Multi-Database Routing | 5 | TBD | TBD | TBD |
| Ill-Formatted Key Mismatch | 5 | TBD | TBD | TBD |
| Unstructured Text Extraction | 5 | TBD | TBD | TBD |
| Domain Knowledge Gap | 5 | TBD | TBD | TBD |
| **TOTAL** | **20** | **TBD** | **TBD** | **TBD** |

## Probe Index

### Category 1: Multi-Database Routing (5 probes)
- Probe 1.1: Yelp Business-Review Join
- Probe 1.2: CRMArenaPro Customer-Ticket Correlation
- Probe 1.3: AG News Article-Category Classification
- Probe 1.4: BookReview Book-Reviewer Aggregation
- Probe 1.5: Google Local Business-Review Sentiment

### Category 2: Ill-Formatted Key Mismatch (5 probes)
- Probe 2.1: CRMArenaPro Customer ID Format (CUST-XXXXX vs Integer)
- Probe 2.2: CRMArenaPro Product Code vs SKU
- Probe 2.3: BookReview Book ID Field Name Mismatch
- Probe 2.4: AG News Title-Based Join (No ID Match)
- Probe 2.5: CRMArenaPro Order ID Format (ORD-YYYY-XXXXX)

### Category 3: Unstructured Text Extraction (5 probes)
- Probe 3.1: Yelp Review Keyword Counting
- Probe 3.2: CRMArenaPro Support Ticket Sentiment
- Probe 3.3: Google Local Review Attribute Extraction
- Probe 3.4: AG News Article Category Prediction
- Probe 3.5: BookReview Review-Text Rating Consistency

### Category 4: Domain Knowledge Gap (5 probes)
- Probe 4.1: "Active Customer" Definition (Yelp)
- Probe 4.2: "Churn" Definition (CRMArenaPro)
- Probe 4.3: "Recent" Temporal Scope (AG News)
- Probe 4.4: "High-Value Customer" Threshold (CRMArenaPro)
- Probe 4.5: "Rating" vs "Stars" Distinction (Yelp)

---

## Detailed Probes

### Category 1: Multi-Database Routing

#### Probe 1.1: Yelp Business-Review Join
**Category:** Multi-database routing failure
**Dataset:** Yelp
**Difficulty:** Medium

**Query:**
```
"List the names and average star ratings of businesses that have at least 10 reviews mentioning 'service'"
```

**Databases Involved:**
- DuckDB: `businesses` table (business metadata, names, average stars)
- MongoDB: `reviews` collection (individual reviews, text content)

**Expected Failure:**
Agent queries only one database (either only DuckDB or only MongoDB) and fails to join the results. May attempt cross-database JOIN in SQL syntax (not supported). May ignore the text extraction requirement entirely.

**Ground Truth Pattern:**
1. Query MongoDB: Find business_ids with >=10 reviews containing "service" in text field
2. Query DuckDB: Get name and stars for those business_ids
3. Merge results in Python

**Observed Failure:**
```
[To be filled after running baseline agent]
- Did agent query both databases? 
- Did it attempt cross-database join?
- What error message appeared?
```

**Fix Applied:**
```
[To be filled after implementing fix]
- Added multi-database routing logic
- Implemented Python-side merge
- Updated KB with join pattern
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 1.2: CRMArenaPro Customer-Ticket Correlation
**Category:** Multi-database routing failure
**Dataset:** CRMArenaPro
**Difficulty:** Hard

**Query:**
```
"Calculate the correlation between customer lifetime value and number of support tickets opened. Show top 10 customers with highest ticket-to-value ratio."
```

**Databases Involved:**
- PostgreSQL: `customers` table (customer_id, lifetime_value placeholder)
- SQLite: `tickets` table (cust_id, ticket counts)
- DuckDB: `customer_360` table (actual lifetime_value)

**Expected Failure:**
Agent fails to navigate three different database systems. May only query one or two, missing critical data. May not recognize that `lifetime_value` exists in DuckDB analytics table, not PostgreSQL core tables.

**Ground Truth Pattern:**
1. Query DuckDB: Get customer_id, lifetime_value from customer_360
2. Query SQLite: Count tickets per cust_id from tickets
3. Resolve customer_id format (see Probe 2.1)
4. Calculate ratio in Python: tickets / lifetime_value
5. Sort and return top 10

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 1.3: AG News Article-Category Classification
**Category:** Multi-database routing failure
**Dataset:** AG News
**Difficulty:** Medium

**Query:**
```
"Count how many sports articles were published in the last 7 days from sources with credibility score above 0.8"
```

**Databases Involved:**
- MongoDB: `articles` collection (title, text, date, source)
- SQLite: `article_categories` table (article_title, category_id)
- SQLite: `category_mapping` table (category_id, category_name)
- SQLite: `source_metadata` table (source_name, credibility_score)

**Expected Failure:**
Agent fails to join MongoDB articles with SQLite categories due to lack of shared ID. May not recognize need for title-based fuzzy matching. May query only MongoDB and miss category/credibility filters.

**Ground Truth Pattern:**
1. Query MongoDB: Get articles from last 7 days
2. Query SQLite: Get category info and source credibility
3. Join on title (exact or fuzzy match)
4. Filter by category="Sports" and credibility>0.8
5. Return count

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 1.4: BookReview Book-Reviewer Aggregation
**Category:** Multi-database routing failure
**Dataset:** BookReview
**Difficulty:** Easy

**Query:**
```
"Find the top 5 reviewers who have given the highest average ratings, but only include reviewers who have reviewed at least 3 books published after 2010"
```

**Databases Involved:**
- PostgreSQL: `reviews` table (reviewer_id, book_id, rating)
- SQLite: `books` table (id, publication_year)
- SQLite: `reviewers` table (user_id, username)

**Expected Failure:**
Agent may query PostgreSQL only, missing book publication years. May not recognize that book_id in PostgreSQL maps to id in SQLite. May fail to join three tables across two databases.

**Ground Truth Pattern:**
1. Query SQLite books: Get book ids published > 2010
2. Query PostgreSQL: Get reviews for those book_ids
3. Group by reviewer_id, count reviews, average rating
4. Filter count >= 3
5. Query SQLite reviewers: Get usernames
6. Sort and return top 5

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 1.5: Google Local Business-Review Sentiment
**Category:** Multi-database routing failure
**Dataset:** Google Local
**Difficulty:** Medium

**Query:**
```
"Find all restaurants in San Francisco with average rating above 4.0 that have at least one review mentioning 'slow service' in the last 30 days"
```

**Databases Involved:**
- PostgreSQL: `businesses` table (business_id, name, category, city, rating)
- SQLite: `reviews` table (business_id, text, rating, review_date)

**Expected Failure:**
Agent may query only one database. May not correctly filter by category ("restaurants") and city ("San Francisco") in PostgreSQL while simultaneously filtering reviews by date and keyword in SQLite.

**Ground Truth Pattern:**
1. Query PostgreSQL: Get business_ids for restaurants in SF with rating>4.0
2. Query SQLite: Get reviews in last 30 days for those business_ids
3. Filter reviews containing "slow service"
4. Return businesses with at least one matching review

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

### Category 2: Ill-Formatted Key Mismatch

#### Probe 2.1: CRMArenaPro Customer ID Format (CUST-XXXXX vs Integer)
**Category:** Ill-formatted key mismatch
**Dataset:** CRMArenaPro
**Difficulty:** Hard

**Query:**
```
"Show the total order value for each customer who opened a high-priority support ticket in Q3 2024"
```

**Format Mismatch:**
- PostgreSQL `customers.customer_id`: Integer (e.g., 123)
- SQLite `tickets.cust_id`: String with prefix (e.g., "CUST-00123")
- SQLite `orders.customer_id`: Integer (matches PostgreSQL)

**Expected Failure:**
Agent attempts direct equality join between `customers.customer_id` (123) and `tickets.cust_id` ("CUST-00123"), returning empty result. May not detect format mismatch and report "no customers found" incorrectly.

**Ground Truth Pattern:**
1. Query SQLite tickets: Get cust_id for high-priority tickets in Q3
2. Normalize cust_id: Strip "CUST-" prefix and leading zeros → integer
3. Query PostgreSQL customers: Get customer info for those IDs
4. Query SQLite orders: Sum order values for those customer_ids
5. Return results

**Required Conversion:**
```python
# SQLite "CUST-00123" → PostgreSQL 123
customer_id_int = int(cust_id_str.replace("CUST-", "").lstrip("0"))
```

**Observed Failure:**
```
[To be filled]
- Did agent attempt direct join?
- Did it return empty result or error?
- Did it recognize format mismatch?
```

**Fix Applied:**
```
[To be filled]
- Implemented join_key_resolver.normalize_key()
- Added format detection before join attempt
- Updated KB join_key_glossary.md with pattern
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 2.2: CRMArenaPro Product Code vs SKU
**Category:** Ill-formatted key mismatch
**Dataset:** CRMArenaPro
**Difficulty:** Medium

**Query:**
```
"List all products that have never been ordered, along with their category and list price"
```

**Format Mismatch:**
- SQLite `order_items.product_code`: VARCHAR (e.g., "PROD-ABC-123")
- SQLite `products.sku`: VARCHAR (e.g., "PROD-ABC-123" - same format but different field name)

**Expected Failure:**
Agent may attempt to join on non-existent `product_code` field in products table, or may not recognize that `product_code` and `sku` refer to the same entity with different field names.

**Ground Truth Pattern:**
1. Query products: Get all sku, category, list_price
2. Query order_items: Get distinct product_codes that have been ordered
3. Filter products where sku NOT IN ordered product_codes
4. Return results

**Required Mapping:**
- `order_items.product_code` ↔ `products.sku` (field name differs, format matches)

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 2.3: BookReview Book ID Field Name Mismatch
**Category:** Ill-formatted key mismatch
**Dataset:** BookReview
**Difficulty:** Easy

**Query:**
```
"Find the average rating for each book published in 2020 or later"
```

**Format Mismatch:**
- PostgreSQL `reviews.book_id`: INTEGER
- SQLite `books.id`: INTEGER (same format, different field name)

**Expected Failure:**
Agent may attempt to join on `reviews.book_id = books.book_id` which doesn't exist. May fail with "column not found" error.

**Ground Truth Pattern:**
1. Query SQLite books: Get id, title for books published >= 2020
2. Query PostgreSQL reviews: Get reviews for those book_ids
3. Group by book_id, calculate average rating
4. Return results

**Required Mapping:**
- `reviews.book_id` ↔ `books.id`

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 2.4: AG News Title-Based Join (No ID Match)
**Category:** Ill-formatted key mismatch
**Dataset:** AG News
**Difficulty:** Hard

**Query:**
```
"What is the most common news category for articles from high-credibility sources (score > 0.9)?"
```

**Format Mismatch:**
- MongoDB `articles`: Has `title` field, no shared ID with SQLite
- SQLite `article_categories`: Has `article_title` field
- SQLite `source_metadata`: Has `source_name` field

**Expected Failure:**
Agent cannot find a shared ID between MongoDB articles and SQLite categories. May give up or attempt impossible cross-database ID join. May not recognize title-based matching is required.

**Ground Truth Pattern:**
1. Query SQLite: Get high-credibility source names (credibility > 0.9)
2. Query MongoDB: Get articles from those sources
3. Query SQLite: Get categories by article_title
4. Use fuzzy string matching or exact title match
5. Count category frequencies, return most common

**Required Approach:**
- No ID exists; must join on text fields (title/article_title)
- May require fuzzy matching for slight title variations

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 2.5: CRMArenaPro Order ID Format (ORD-YYYY-XXXXX)
**Category:** Ill-formatted key mismatch
**Dataset:** CRMArenaPro
**Difficulty:** Medium

**Query:**
```
"Find all support tickets related to orders placed in December 2024"
```

**Format Mismatch:**
- PostgreSQL `opportunities`: May reference order_id as string "ORD-2024-12345"
- SQLite `orders.order_id`: INTEGER (12345)
- SQLite `tickets`: May reference order_id in description text only

**Expected Failure:**
Agent cannot find direct order_id in tickets table. Fails to extract order reference from unstructured ticket description. Misses the relationship entirely.

**Ground Truth Pattern:**
1. Query SQLite orders: Get order_ids from December 2024
2. Normalize to ORD-YYYY-XXXXX format
3. Query SQLite tickets: Search description field for order reference strings
4. Return matching tickets

**Required Conversion:**
```python
# Integer 12345 → String "ORD-2024-12345"
order_ref = f"ORD-2024-{order_id:05d}"
```

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

### Category 3: Unstructured Text Extraction

#### Probe 3.1: Yelp Review Keyword Counting
**Category:** Unstructured text extraction failure
**Dataset:** Yelp
**Difficulty:** Medium

**Query:**
```
"How many reviews mention 'wait time' or 'waiting' and have a rating of 2 stars or less?"
```

**Unstructured Field:**
- MongoDB `reviews.text`: Free-text review content

**Expected Failure:**
Agent may return raw review text instead of count. May attempt SQL LIKE query on MongoDB (wrong syntax). May fail to extract keyword presence from text field. May count reviews without keyword filtering.

**Ground Truth Pattern:**
1. Query MongoDB: Get reviews with stars <= 2
2. Python-side extraction: Filter reviews where text.lower() contains "wait time" or "waiting"
3. Count filtered results
4. Return count (not the reviews themselves)

**Extraction Required:**
```python
keywords = ["wait time", "waiting"]
count = sum(1 for r in reviews if any(kw in r['text'].lower() for kw in keywords))
```

**Observed Failure:**
```
[To be filled]
- Did agent return count or raw text?
- Did it correctly filter by keyword?
- Did it handle MongoDB text search correctly?
```

**Fix Applied:**
```
[To be filled]
- Implemented text extraction utility
- Added Python-side filtering step
- Updated unstructured_fields.md KB
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 3.2: CRMArenaPro Support Ticket Sentiment
**Category:** Unstructured text extraction failure
**Dataset:** CRMArenaPro
**Difficulty:** Hard

**Query:**
```
"Calculate the percentage of support tickets that express negative sentiment, grouped by customer segment"
```

**Unstructured Fields:**
- SQLite `tickets.description`: Issue description
- SQLite `ticket_comments.comment_text`: Conversation history

**Expected Failure:**
Agent may not extract sentiment from text fields. May rely only on structured fields like priority or status. May return raw ticket counts without sentiment analysis.

**Ground Truth Pattern:**
1. Query DuckDB customer_360: Get customer_id, segment
2. Query SQLite tickets: Get ticket_id, description for each customer
3. Extract sentiment: Count negative words or use stars/priority as proxy
4. Group by segment, calculate percentage
5. Return results

**Extraction Required:**
```python
negative_words = ["frustrated", "disappointed", "not working", "issue", "problem", "fail"]
def is_negative(text):
    return any(word in text.lower() for word in negative_words)
```

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 3.3: Google Local Review Attribute Extraction
**Category:** Unstructured text extraction failure
**Dataset:** Google Local
**Difficulty:** Medium

**Query:**
```
"Which restaurants have the most reviews mentioning 'friendly staff' or 'great service'? Show top 10."
```

**Unstructured Field:**
- SQLite `reviews.text`: Free-text review content

**Expected Failure:**
Agent may not perform keyword extraction. May return businesses with most total reviews, ignoring text content requirement. May fail to aggregate by business correctly.

**Ground Truth Pattern:**
1. Query PostgreSQL businesses: Get restaurant business_ids
2. Query SQLite reviews: Get all reviews for those businesses
3. Filter reviews mentioning "friendly staff" OR "great service"
4. Count mentions per business
5. Sort and return top 10

**Extraction Required:**
```python
keywords = ["friendly staff", "great service"]
```

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 3.4: AG News Article Category Prediction
**Category:** Unstructured text extraction failure
**Dataset:** AG News
**Difficulty:** Medium

**Query:**
```
"Find all articles from the last 30 days that discuss 'artificial intelligence' but are NOT categorized as Sci/Tech"
```

**Unstructured Field:**
- MongoDB `articles.text`: Full article body

**Expected Failure:**
Agent may only use category metadata, missing the text content requirement. May not perform keyword search across article bodies. May not handle negation (NOT categorized as Sci/Tech) correctly.

**Ground Truth Pattern:**
1. Query SQLite: Get category info for all articles
2. Filter for articles NOT in Sci/Tech category
3. Query MongoDB: Get article text for those articles
4. Filter where text contains "artificial intelligence" or "AI"
5. Return matching articles

**Extraction Required:**
```python
keywords = ["artificial intelligence", "AI", "machine learning"]
```

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 3.5: BookReview Review-Text Rating Consistency
**Category:** Unstructured text extraction failure
**Dataset:** BookReview
**Difficulty:** Hard

**Query:**
```
"Find reviews where the text expresses strong negative sentiment but the rating is 4 or 5 stars. Count how many such inconsistent reviews exist."
```

**Unstructured Field:**
- PostgreSQL `reviews.review_text`: Full review content

**Expected Failure:**
Agent may not perform sentiment analysis. May only use rating field, missing the inconsistency requirement. May not compare text sentiment with numeric rating.

**Ground Truth Pattern:**
1. Query PostgreSQL: Get all reviews with rating >= 4
2. Extract sentiment from review_text
3. Identify negative sentiment indicators
4. Count reviews with negative text but positive rating
5. Return count

**Extraction Required:**
```python
negative_indicators = ["disappointing", "overrated", "boring", "waste", "terrible", "poorly written"]
```

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

### Category 4: Domain Knowledge Gap

#### Probe 4.1: "Active Customer" Definition (Yelp)
**Category:** Domain knowledge gap
**Dataset:** Yelp
**Difficulty:** Medium

**Query:**
```
"Show the geographic distribution of active users across different states"
```

**Ambiguous Term:** "Active user"

**Possible Interpretations:**
1. User account exists (row in users table)
2. User has written at least one review
3. User has written a review in the last 30 days
4. User has logged in recently (not available in schema)

**Expected Failure:**
Agent assumes "active" means account exists (Interpretation 1). Returns all users regardless of activity. Answer is syntactically correct but semantically wrong.

**Correct Domain Definition:**
For Yelp dataset, "active user" typically means user has written at least one review (`review_count > 0`).

**Ground Truth Pattern:**
1. Query DuckDB users: Filter where review_count > 0
2. Group by state (extract from user location or business state for reviews)
3. Count active users per state
4. Return distribution

**Observed Failure:**
```
[To be filled]
- What definition did agent use?
- Did it filter by review_count?
- Did it explain its interpretation?
```

**Fix Applied:**
```
[To be filled]
- Added domain_terms.md entry for "active"
- Updated KB with Yelp-specific definition
- Agent now injects domain terms for ambiguous queries
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 4.2: "Churn" Definition (CRMArenaPro)
**Category:** Domain knowledge gap
**Dataset:** CRMArenaPro
**Difficulty:** Hard

**Query:**
```
"Calculate the churn rate for enterprise customers in Q4 2024"
```

**Ambiguous Term:** "Churn rate"

**Possible Interpretations:**
1. Customers who canceled service (status = 'Closed')
2. Customers with no purchase in last 30 days
3. Customers with no purchase in last 90 days
4. Customers with no purchase in last 180 days

**Expected Failure:**
Agent may use wrong time window or wrong status code. May return cancellation rate instead of inactivity-based churn. May not recognize enterprise segment filter.

**Correct Domain Definition:**
For CRMArenaPro, "churned customer" = no purchase in 180+ days. `days_since_last_order > 180` in customer_360 table.

**Ground Truth Pattern:**
1. Query DuckDB customer_360: Filter segment = 'Enterprise'
2. Identify churned: days_since_last_order > 180 OR churn_risk = 'High'
3. Calculate rate: churned_enterprise / total_enterprise
4. Return percentage

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 4.3: "Recent" Temporal Scope (AG News)
**Category:** Domain knowledge gap
**Dataset:** AG News
**Difficulty:** Easy

**Query:**
```
"Show the most common topics in recent business news"
```

**Ambiguous Term:** "Recent"

**Possible Interpretations:**
1. Last 24 hours
2. Last 7 days
3. Last 30 days
4. Current month

**Expected Failure:**
Agent may use arbitrary or undefined time window. May return all-time data without date filter. May not document assumption.

**Correct Domain Definition:**
For news datasets, "recent" typically means last 7 days. If undefined, agent should default to 7 days and note assumption in trace.

**Ground Truth Pattern:**
1. Define "recent" = articles from last 7 days
2. Query MongoDB: Get articles from last 7 days
3. Query SQLite: Get category = 'Business'
4. Extract topics/keywords from text
5. Count frequencies, return most common

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 4.4: "High-Value Customer" Threshold (CRMArenaPro)
**Category:** Domain knowledge gap
**Dataset:** CRMArenaPro
**Difficulty:** Medium

**Query:**
```
"Compare the average support ticket resolution time for high-value customers versus regular customers"
```

**Ambiguous Term:** "High-value customer"

**Possible Interpretations:**
1. Top 10% by lifetime value
2. Top 20% by lifetime value
3. Lifetime value > $10,000
4. Segment = 'Enterprise'

**Expected Failure:**
Agent may not know how to define "high-value." May use arbitrary threshold. May not find pre-calculated segment in customer_360 table.

**Correct Domain Definition:**
For CRMArenaPro, "high-value" can be:
- Pre-calculated: `segment = 'Enterprise'` in customer_360 table
- Calculated: Top 20% by `lifetime_value`

**Ground Truth Pattern:**
1. Query DuckDB customer_360: Get customer_id, segment, lifetime_value
2. Define high-value: segment='Enterprise' OR lifetime_value > 80th percentile
3. Query SQLite tickets: Get resolution time (closed_date - opened_date) for each customer
4. Group by high-value flag, calculate average
5. Return comparison

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

#### Probe 4.5: "Rating" vs "Stars" Distinction (Yelp)
**Category:** Domain knowledge gap
**Dataset:** Yelp
**Difficulty:** Medium

**Query:**
```
"Find businesses where the average rating is above 4.0 but the most recent 10 reviews average below 3.0"
```

**Ambiguous Terms:** "Rating" vs "Stars"

**Distinction Required:**
- Business `stars`: Pre-calculated average of ALL reviews (static)
- Review `stars`: Individual rating (1-5)
- Calculated average of recent reviews: Must be computed from review data

**Expected Failure:**
Agent may only use business.stars field, missing the "recent reviews" calculation entirely. May not understand that business.stars is historical average, not current sentiment.

**Ground Truth Pattern:**
1. Query DuckDB businesses: Filter where stars > 4.0
2. Query MongoDB reviews: For each business, get most recent 10 reviews by date
3. Calculate average of those 10 review stars
4. Filter where calculated average < 3.0
5. Return business names

**Key Insight:**
`businesses.stars` ≠ average of recent reviews. Must compute from review data.

**Observed Failure:**
```
[To be filled]
- Did agent compute from reviews or use pre-calculated stars?
- Did it correctly filter by recency?
- Did it understand the distinction?
```

**Fix Applied:**
```
[To be filled]
- Added domain_terms.md entry for "rating vs stars"
- Agent now computes from review data when "recent" specified
- Updated query_patterns.md with pattern
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

## Additional Probes (Bonus)

### Probe 5.1: Complex Multi-Category Probe (CRMArenaPro)
**Category:** Multi-DB + Key Mismatch + Domain Knowledge
**Dataset:** CRMArenaPro
**Difficulty:** Extreme

**Query:**
```
"Identify high-value customers who have shown signs of churn risk (multiple recent support tickets with negative sentiment) but have not been contacted by sales in the last 30 days. Show their lifetime value and recommended next action."
```

**Challenges Combined:**
- Multi-DB: PostgreSQL (customers, activities), SQLite (tickets), DuckDB (customer_360)
- Key Mismatch: customer_id (int) vs cust_id ("CUST-XXXXX")
- Unstructured Text: ticket description sentiment extraction
- Domain Knowledge: "high-value", "churn risk", "recent"

**Expected Failure:** Agent fails on multiple dimensions simultaneously.

**Ground Truth Pattern:**
1. Define terms from KB
2. Query customer_360: Get high-value customers
3. Query tickets: Get recent tickets with negative sentiment
4. Normalize customer IDs
5. Query activities: Filter out customers with recent sales contact
6. Return actionable list

**Observed Failure:**
```
[To be filled]
```

**Fix Applied:**
```
[To be filled]
```

**Score Before Fix:** ___ / 1
**Score After Fix:** ___ / 1

---

## Probe Library Usage

### Running a Probe
```python
from utils.benchmark_harness_wrapper import run_dab_query

# Run probe against agent
traces = run_dab_query(
    agent=my_agent,
    dataset="yelp",
    query_id="probe_1_1",  # Custom probe ID
    trials=5
)

# Validate against expected pattern
validation = harness.validate_result(traces[0], "yelp", "probe_1_1")
```

### Documenting Results
```markdown
## Probe Result Entry Format
- **Date:** YYYY-MM-DD
- **Probe ID:** 1.1
- **Agent Version:** v1.2.0
- **Pass/Fail:** [PASS/FAIL]
- **Failure Mode Observed:** [Description]
- **Fix Implemented:** [Description]
- **Score Delta:** [+X%]
```

### Updating KB from Probes
When a probe consistently fails:
1. Document failure in `kb/corrections/CHANGELOG.md`
2. Identify root cause category
3. Update relevant KB document (domain_terms.md, join_key_glossary.md, etc.)
4. Re-run probe to verify fix
5. Promote successful pattern to `query_patterns.md`

---

## Maintenance Log

| Date | Probe ID | Action | Score Before | Score After | Owner |
|------|----------|--------|--------------|-------------|-------|
| [Date] | [ID] | [Initial run/Fix applied] | [%] | [%] | [Name] |

---

## Contribution Guidelines

When adding new probes:
1. Select category (1-4) based on primary failure mode
2. Write query that isolates that specific failure
3. Document expected failure and ground truth pattern
4. Include both pre-fix and post-fix score tracking
5. Update summary statistics table

Probes that test multiple categories simultaneously should be placed in "Complex Multi-Category" section.