# INJECTION TEST: openai_table_enrichment.md

**DATE:** 2026-04-11
**VERSION:** v1.1
**DOCUMENT TESTED:** `kb/architecture/openai_table_enrichment.md`

**CONTEXT SETUP:**
- Fresh LLM session
- Single document loaded: `openai_table_enrichment.md`
- No other context provided

---

### TEST QUESTION 1:
"What is the difference between raw schema and enriched schema?"

**EXPECTED ANSWER (from document):**
Raw schema tells you table name, column name, and data type (e.g., `users.status` = integer).
Enriched schema tells you business meaning (e.g., `status = 1` means "active", `status = 2` means "suspended").

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer contrasts structural information with business meaning]

---

### TEST QUESTION 2:
"What are the four steps in OpenAI's Codex-powered enrichment process?"

**EXPECTED ANSWER (from document):**
1. Scan table and column names
2. Generate plausible business descriptions
3. Present descriptions to human data stewards for verification
4. Store verified descriptions in the enrichment layer

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if all four steps identified in order]

---

### TEST QUESTION 3:
"For the DAB Yelp dataset, what is the critical enrichment needed for the 'stars' columns?"

**EXPECTED ANSWER (from document):**
- **Business stars** = average rating across all reviews
- **Review stars** = individual rating from a single user

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer distinguishes business stars from review stars]

---

### TEST QUESTION 4:
"What is the 'closed-loop self-correction' pattern described in the document?"

**EXPECTED ANSWER (from document):**
A feedback loop where:
1. Agent runs query with current enrichment
2. User corrects output
3. Correction flows to enrichment layer (not just session memory)
4. Next query uses corrected enrichment

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer describes all four steps of the loop]

---

### TEST QUESTION 5:
"In the DAB implementation, who performs the manual enrichment that Codex would handle automatically at OpenAI?"

**EXPECTED ANSWER (from document):**
Intelligence Officers perform manual enrichment by:
1. Running schema introspection on each DAB dataset
2. Identifying ambiguous columns
3. Writing enrichment documents in `kb/domain/schema_descriptions.md`
4. Verifying with injection tests before committing

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer identifies Intelligence Officers and describes the manual process]

---

### TEST QUESTION 6:
"What is the key insight about the difference between a demo agent and a production agent?"

**EXPECTED ANSWER (from document):**
Table enrichment is the difference. A demo agent assumes schema is self-documenting. A production agent knows that `status=2` means suspended and filters accordingly.

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer mentions table enrichment and contrast between demo and production assumptions]

---

### TEST QUESTION 7:
"Which three DAB datasets are identified as priority enrichment targets, and what ambiguity does each have?"

**EXPECTED ANSWER (from document):**
1. **Yelp:** 'stars' in reviews vs. 'stars' in business (average vs. individual rating)
2. **Telecom:** 'churn' column (30-day window definition)
3. **Healthcare:** 'encounter_type' codes (numeric to text mapping)

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if all three datasets and their ambiguities correctly identified]

---

**FINAL RESULT:** [PASS/FAIL]
**NOTES:** [Any observations about LLM comprehension]
