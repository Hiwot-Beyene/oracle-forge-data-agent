# INJECTION TEST: openai_six_layers.md

**DATE:** 2026-04-11
**VERSION:** v1.1
**DOCUMENT TESTED:** `kb/architecture/openai_six_layers.md`

**CONTEXT SETUP:**
- Fresh LLM session
- Single document loaded: `openai_six_layers.md`
- No other context provided

---

### TEST QUESTION 1:
"List all six layers of OpenAI's data agent context architecture in order."

**EXPECTED ANSWER (from document):**
1. **Raw Schema**
2. **Table Relationships**
3. **Column Semantics**
4. **Query Patterns**
5. **Institutional Knowledge**
6. **User Preferences**

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if all six layers in correct order]

---

### TEST QUESTION 2:
"Which layer is described as the 'hardest sub-problem' by OpenAI's writeup?"

**EXPECTED ANSWER (from document):**
Layer 3: **Column Semantics** (table enrichment)

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer identifies Column Semantics or Layer 3]

---

### TEST QUESTION 3:
"What is the '70,000 table problem'?"

**EXPECTED ANSWER (from document):**
OpenAI's data agent operates across 70,000+ tables in their internal data warehouse. Without the six-layer architecture, the agent cannot efficiently navigate this scale—it would brute-force search all tables for every query. The layers enable navigation from schema → semantics → patterns efficiently.

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer references both the 70,000+ table scale and the need for layered navigation]

---

### TEST QUESTION 4:
"Which layers are REQUIRED for the DAB agent in V1, and which is deferred to V2?"

**EXPECTED ANSWER (from document):**
- **Required V1:** Layers 1-5 (Raw Schema through Institutional Knowledge)
- **Deferred V2:** Layer 6 (User Preferences)

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if correctly distinguishes V1 requirements from V2 deferral]

---

### TEST QUESTION 5:
"A DAB query asks for 'churned customers in Q3.' Which layer provides the definition that churn means 'no purchase in 90 days' rather than 'no purchase in 30 days'?"

**EXPECTED ANSWER (from document):**
Layer 5: **Institutional Knowledge**

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer identifies Layer 5 or Institutional Knowledge]

---

### TEST QUESTION 6:
"How does DAB's scale (12 datasets) compare to OpenAI's scale (70,000 tables), and why does the architecture still apply?"

**EXPECTED ANSWER (from document):**
DAB is easier (12 datasets vs. 70,000 tables) but the architecture still applies because the agent will still fail on ill-formatted join keys and domain terms without layers 3-5. The problem is smaller but the failure modes are identical.

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer acknowledges scale difference but confirms architecture relevance]

---

**FINAL RESULT:** [PASS/FAIL]
**NOTES:** [Any observations about LLM comprehension]
