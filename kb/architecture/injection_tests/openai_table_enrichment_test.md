# Injection test — openai_table_enrichment.md

## Document under test
`kb/architecture/openai_table_enrichment.md`

## Test questions

### Question 1
"What is Codex Enrichment (Layer 3) and how does it find facts invisible in SQL metadata?"

Required concepts:
- Daily asynchronous background process (codex crawl)
- Derives definitions from the pipeline code that generates tables
- Infers upstream/downstream dependencies, ownership, and granularity
- Reveals filtering assumptions (e.g., US users only) invisible in schema
- Pipeline logic is more useful context than raw table schemas

Forbidden contradictions:
- Stating Codex Enrichment is a real-time SQL query

---

## Test result

**Run timestamp:** 2026-04-11 16:42 UTC
**Document:** openai_enrichment
### Q1: 100/100
**Concepts found:**
  - [x] Daily asynchronous background process (codex crawl)
  - [x] Derives definitions from the pipeline code that generates tables
  - [x] Infers upstream/downstream dependencies, ownership, and granularity
  - [x] Reveals filtering assumptions (e.g., US users only) invisible in schema
  - [x] Pipeline logic is more useful context than raw table schemas
**Concepts missing:**
**Actual answer:**
Based on the document, Codex Enrichment (Layer 3) is a specialized system that uses a Codex model to automatically enrich database schemas with semantic information that isn't available in raw SQL metadata.

## What is Codex Enrichment (Layer 3)?

Codex Enrichment is implemented as a **daily async process called a "Codex Crawl"** that runs separately from the main agent LLM. It's designed to solve the problem where raw schema only provides basic structural information (like `table users`, `column status`, `type integer`) but doesn't explain what the data actually means semantically.

## How it finds facts invisible in SQL metadata:

The Codex Crawl operates through a 5-step process:

1. **Scan** table and column names
2. **Generate** deeper definitions by analyzing **pipeline code** rather than just SQL schemas
3. **Discover Assumptions** by identifying hidden business logic 
4. **Present** descriptions to human data stewards for verification
5. **Store** verified descriptions in the enrichment layer

## Key capabilities for finding invisible facts:

- **Infers upstream/downstream dependencies, ownership, and granularity** facts from pipeline code
- **Identifies hidden filtering logic** like "filter only US users before aggregating" which is completely invisible in table schemas
- **Captures the intent of the data generation process** rather than just structural information

The document emphasizes that **pipeline logic provides more useful context than raw table schemas** because it reveals the semantic meaning and business rules that govern how the data should be interpreted and used. This allows the system to understand that `status = 1` means "active", `status = 2` means "suspended", etc. - information that would never appear in SQL metadata alone.
**Grader reasoning:** All five required concepts are clearly present in the answer with specific examples and explanations, and no forbidden contradictions were found.
---