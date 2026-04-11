# INJECTION TEST: claude_tool_scoping.md

**DATE:** 2026-04-11
**VERSION:** v1.1
**DOCUMENT TESTED:** `kb/architecture/claude_tool_scoping.md`

**CONTEXT SETUP:**
- Fresh LLM session
- Single document loaded: `claude_tool_scoping.md`
- No other context provided

---

### TEST QUESTION 1:
"What are the four tool categories in Claude Code's architecture?"

**EXPECTED ANSWER (from document):**
1. **File System Tools** (`read_file`, `write_file`, `list_directory`, `search_content`)
2. **Code Execution Tools** (`run_terminal`, `run_python`, `run_tests`)
3. **Git Tools** (`git_status`, `git_diff`, `git_commit`, `git_branch`)
4. **External Tools** (`web_search`, `web_fetch`, `api_call`)

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if all four categories identified with at least one example each]

---

### TEST QUESTION 2:
"According to the 'Tool First' design rule, should a DAB agent generate raw SQL queries?"

**EXPECTED ANSWER (from document):**
No. The agent should select tools from a manifest, not generate raw shell commands or raw SQL. For DAB, this means using named MCP Toolbox tools like `query_postgres_[dataset]` rather than having the LLM write SQL strings directly.

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if answer states agent should use named tools, not raw SQL]

---

### TEST QUESTION 3:
"What are the three properties every Claude Code tool must have?"

**EXPECTED ANSWER (from document):**
1. **Tight domain boundaries** (one tool does one thing well)
2. **Explicit preconditions** (what must be true before calling)
3. **Clear error semantics** (what failure means and how to recover)

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if all three properties correctly identified]

---

### TEST QUESTION 4:
"What are the four required MCP tools for the DAB agent?"

**EXPECTED ANSWER (from document):**
1. `query_postgres_[dataset]` - One tool per PostgreSQL database
2. `query_mongo_[collection]` - One tool per MongoDB collection
3. `extract_structured_text` - Unstructured field parser (Week 3 module)
4. `resolve_join_key` - Format normalizer for cross-DB joins

**ACTUAL LLM RESPONSE:**
[Copy full response here]

**PASS/FAIL:** [PASS if all four tools identified with their purposes]

---

**FINAL RESULT:** [PASS/FAIL]
**NOTES:** [Any observations about LLM comprehension]
