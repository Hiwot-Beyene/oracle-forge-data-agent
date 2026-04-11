# INJECTION TEST: claude_autodream.md

**DATE:** 2026-04-11
**VERSION:** v1.1
**DOCUMENT TESTED:** `kb/architecture/claude_autodream.md`

**CONTEXT SETUP:**
- Fresh LLM session
- Single document loaded: `claude_autodream.md`
- No other context provided

---

### TEST QUESTION 1:
"What are the three functions of the autoDream background process?"

**EXPECTED ANSWER (from document):**
1. **Orient** — Read MEMORY.md to understand current state
2. **Gather** — Find new signals from daily logs and session transcripts
3. **Consolidate** — Merge disparate observations, remove contradictions, convert vague insights to concrete facts
4. (Bonus) **Prune** — Keep context efficient by removing stale or redundant entries

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if monitor, identify, and consolidate all mentioned]

---

### TEST QUESTION 2:
"What triggers autoDream to write a pattern to MEMORY.md?"

**EXPECTED ANSWER (from document):**
User corrects the same pattern 3 or more times

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer includes "3+ times" or "three or more corrections"]

---

### TEST QUESTION 3:
"In the DAB implementation, who performs the consolidation that autoDream would handle automatically?"

**EXPECTED ANSWER (from document):**
Intelligence Officers perform consolidation manually during mob sessions by reviewing `kb/corrections/` and updating `kb/domain/` when patterns are identified.

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer identifies Intelligence Officers as responsible for manual consolidation]

---

### TEST QUESTION 4:
"What is the required format for every correction entry in the DAB corrections log?"

**EXPECTED ANSWER (from document):**
`[Query that failed] → [What was wrong] → [Correct approach]`

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if all three components identified with arrow notation]

---

### TEST QUESTION 5:
"Why does autoDream run offline rather than during active sessions?"

**EXPECTED ANSWER (from document):**
To prevent consolidation work from consuming the agent's context window or slowing response time. The agent should not be interrupted by memory maintenance tasks.

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer mentions context window preservation or response time]

---

**FINAL RESULT:** [PASS/FAIL]
**NOTES:** [Any observations about LLM comprehension]
