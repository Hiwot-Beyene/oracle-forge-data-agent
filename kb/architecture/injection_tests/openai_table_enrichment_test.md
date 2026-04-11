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

**Run timestamp:** 2026-04-11 14:45 UTC
**Document:** openai_enrichment
### Q1: 75/100
**Actual:** Based on the document, Codex Enrichment (Layer 3) refers to OpenAI's specialized table enrichment system that uses a dedicated Codex model to make database schemas semantically meaningful rather than just syntactically correct.

## What Codex Enrichment (Layer 3) is:

A specialized Codex model (separate from the main agent LLM) that runs as a daily async process to enrich raw database schemas with business context and semantic meaning.

## How it finds facts invisible in SQL metadata:

The system uses a 4-step process to discover hidden semantic information:

1. **Scan** table and column names in the database
2. **Generate** plausible business descriptions by analyzing pipeline code (this is key - it looks beyond just the schema to actual code usage)
3. **Present** these generated descriptions to human data stewards for verification
4. **Store** the verified descriptions in an enrichment layer

## The problem it solves:

Raw SQL metadata only tells you technical details like "column `status`, type `integer`" but doesn't reveal that:
- `status = 1` means "active" 
- `status = 2` means "suspended"
- `status = 3` means "deleted" (but records remain for audit)

The document emphasizes that **"Table enrichment is the difference between a demo agent and a production agent"** - without this enrichment, agents produce queries that are syntactically correct but semantically wrong because they lack the business context that humans understand but that isn't captured in database schemas.
---