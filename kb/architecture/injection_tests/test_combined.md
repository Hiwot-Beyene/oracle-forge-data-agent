# COMBINED INJECTION TEST: Full KB v1

**DATE:** 2026-04-11
**VERSION:** v1.1
**DOCUMENTS TESTED:** All architecture documents loaded simultaneously

**CONTEXT SETUP:**
- Fresh LLM session
- All architecture documents loaded: 
    - `claude_memory_layers.md`
    - `claude_tool_scoping.md`
    - `claude_autodream.md`
    - `openai_six_layers.md`
    - `openai_table_enrichment.md`
- No other context provided

---

### TEST QUESTION 1 (Integration):
"A DAB query fails because the agent tried to join PostgreSQL `users.id` (integer) with MongoDB `tickets.customer_id` (string formatted as 'CUST-00123'). Which specific components from the KB should prevent or fix this failure?"

**EXPECTED ANSWER (Composite from multiple documents):**
- **Tool Scoping:** The agent should have used `resolve_join_key` tool rather than direct join
- **Six Layers - Layer 3 (Column Semantics):** Should have documented the format mismatch in `schema_descriptions.md`
- **autoDream:** After failure, correction should be logged to `kb/corrections/` with format `[Query] → [Format mismatch] → [Use resolve_join_key tool with format normalization]`
- **Memory Layers:** The `kb/domain/` glossary should have pre-loaded the format difference

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer references at least three distinct KB components]

---

### TEST QUESTION 2 (Synthesis):
"Explain how the three-layer memory architecture (Claude Code) and the six-layer context architecture (OpenAI) complement each other in the DAB agent design."

**EXPECTED ANSWER (Composite):**
- **Claude Code layers** handle **when** knowledge is loaded (index first, topics on demand, transcripts via search)
- **OpenAI layers** handle **what** knowledge exists (schema → relationships → semantics → patterns → institutional → preferences)
- **Together:** The DAB agent uses Claude's loading pattern to navigate OpenAI's content layers
- **Example:** Session starts with `AGENT.md` (index) → queries Yelp → loads `kb/domain/yelp/` (topic) containing enriched schema (OpenAI layers 1-5)

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer describes temporal loading vs. content layering distinction]

---

**FINAL RESULT:** [PASS/FAIL]
**NOTES:** [Any observations about LLM synthesis capability across documents]
