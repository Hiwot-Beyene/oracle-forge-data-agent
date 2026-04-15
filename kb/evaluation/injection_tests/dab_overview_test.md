# Injection test — dab_overview.md

## Document under test
`kb/evaluation/dab_overview.md`

## Why this test is critical
dab_overview.md defines the benchmark rules, scoring method, and submission format. If the agent or team cannot derive the correct evaluation protocol from this document alone, they risk submitting results in the wrong format, misunderstanding pass@1, or building a harness that tracks the wrong metrics. Incorrect scoring methodology means every improvement measurement is invalid.

---

## Test questions

### Question 1
"What is the pass@1 scoring method in DAB, how many trials per query are required for benchmark submission, and what is the difference between pass@1 and pass@50?"

Required concepts:
- pass@1 is the fraction of queries where the agent returns the correct answer on the first trial
- 50 trials per query minimum are required for benchmark submission
- pass@50 is the fraction of queries solved in at least 1 of 50 trials measuring the capability ceiling
- Each query is binary pass/fail with no partial credit

Forbidden contradictions:
- Stating that pass@1 is average accuracy across all trials
- Stating that partial credit is awarded

---

### Question 2
"What are the four tools available to the agent in the DAB scaffold, and what is each tool used for?"

Required concepts:
- query_db executes a query against a specific database for fetching data
- list_db introspects schema by listing tables columns and sample values
- execute_python runs Python code in a sandboxed Docker container for data transformation and cross-DB joins
- return_answer submits the final answer and terminates the agent loop

Forbidden contradictions:
- Listing tools not in the DAB scaffold
- Stating that query_db can query all databases in a single call

---

### Question 3
"What must a benchmark submission to DataAgentBench contain, what is the required PR title format, what must the PR body include, and what repository receives the PR?"

Required concepts:
- Submission is a GitHub PR to ucbepic/DataAgentBench
- Must contain a results JSON file with all 54 queries and 50 trials each
- Must contain an AGENT.md with architecture overview and key design decisions
- PR title format is [Team Name] — TRP1 FDE Programme, April 2026
- PR body must include pass@1 score trial count and brief architecture description

Forbidden contradictions:
- Stating the PR goes to a different repository
- Stating that fewer than 50 trials per query is acceptable

---

### Question 4
"What fields should the evaluation harness trace schema capture for each query execution, what fields does each tool call entry record, what fields does the score log track, and what is the minimum number of data points required?"

Required concepts:
- Trace schema captures query_id dataset question trial number timestamp tool_calls final_answer expected_answer pass/fail iterations_used and exploration_ratio
- Each tool call entry records the step number tool name arguments result_summary success status and duration
- Score log must have minimum two data points showing baseline and final scores
- Score log tracks run_id timestamp model trials_per_query pass_at_1 queries_passed and kb_version

Forbidden contradictions:
- Stating that a single data point in the score log is sufficient
- Stating that tool calls do not need to be traced

---

### Question 5
"What is the optimal exploration ratio for tool calls according to DAB findings, what happens if the ratio is too low or too high, and what metric tracks whether the agent consults domain knowledge?"

Required concepts:
- The optimal exploration ratio is approximately 20 percent of tool calls being schema inspection
- If the ratio is below 15 percent the agent dives into queries without understanding the schema leading to wrong data source selection
- If the ratio is above 30 percent the agent wastes token budget on exploration and runs out of iterations
- KB hit rate tracks the percentage of queries where KB domain knowledge was consulted

Forbidden contradictions:
- Stating that exploration is unnecessary
- Stating that more exploration is always better

---

## Test result

**Run timestamp:** 2026-04-14 16:12 UTC
**Model used:** google/gemini-2.0-flash-001
**Document tested:** kb/evaluation/dab_overview.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** What is the pass@1 scoring method in DAB, how many trials per query are required for benchmark submission, and what is the difference between pass@1 and pass@50?

**Concepts found (4/4):**
  - [x] pass@1 is the fraction of queries where the agent returns the correct answer on the first trial
  - [x] 50 trials per query minimum are required for benchmark submission
  - [x] pass@50 is the fraction of queries solved in at least 1 of 50 trials measuring the capability ceiling
  - [x] Each query is binary pass/fail with no partial credit

**Actual answer:**
Based on the document:

*   **pass@1 scoring method:** It is the fraction of queries where the agent returns the correct answer on the first trial. Each query is scored as binary pass/fail with no partial credit. The formula is `pass@1 = (number of queries correct on first attempt) / 54`.
*   **Trials per query required for benchmark submission:** A minimum of 50 trials per query is required.
*   **Difference between pass@1 and pass@50:** pass@1 is the fraction of queries solved correctly on the first attempt, while pass@50 is the fraction of queries solved in at least 1 of 50 trials. In other words, pass@1 measures the accuracy on the first try, while pass@50 measures the capability ceiling, showing if the agent can solve the query given multiple attempts.

**Grader reasoning:** All required concepts are clearly present and no forbidden contradictions are found, so the score is 100.

---

### Question 2 — PASS (100/100)

**Question:** What are the four tools available to the agent in the DAB scaffold, and what is each tool used for?

**Concepts found (4/4):**
  - [x] query_db executes a query against a specific database for fetching data
  - [x] list_db introspects schema by listing tables columns and sample values
  - [x] execute_python runs Python code in a sandboxed Docker container for data transformation and cross-DB joins
  - [x] return_answer submits the final answer and terminates the agent loop

**Actual answer:**
According to Section B of the document, the four tools available in the DAB scaffold are:

1.  `query_db`: Execute a query against a specific database.
2.  `list_db`: Introspect schema — list tables, columns, sample values.
3.  `execute_python`: Run Python code in a sandboxed Docker container.
4.  `return_answer`: Submit the final answer and terminate the agent loop.

**Grader reasoning:** All required concepts are present in the actual answer, and no forbidden contradictions are found, resulting in a perfect score.

---

### Question 3 — PASS (100/100)

**Question:** What must a benchmark submission to DataAgentBench contain, what is the required PR title format, what must the PR body include, and what repository receives the PR?

**Concepts found (5/5):**
  - [x] Must contain a results JSON file with all 54 queries and 50 trials each
  - [x] Must contain an AGENT.md with architecture overview and key design decisions
  - [x] PR title format is [Team Name] — TRP1 FDE Programme, April 2026
  - [x] PR body must include pass@1 score trial count and brief architecture description
  - [x] Submission is a GitHub PR to ucbepic/DataAgentBench

**Actual answer:**
According to the document, a benchmark submission to DataAgentBench must contain:

1.  **Results JSON**: `submission/team_[name]_results.json` with all 54 queries, 50 trials each.
2.  **AGENT.md**: Architecture overview, key design decisions, what worked, what did not.

The required PR title format is: `[Team Name] — TRP1 FDE Programme, April 2026`

The PR body must include the pass@1 score, the trial count, and a brief architecture description.

The repository that receives the PR is `ucbepic/DataAgentBench`.

**Grader reasoning:** All required concepts are present and no forbidden contradictions were found.

---

### Question 4 — PASS (100/100)

**Question:** What fields should the evaluation harness trace schema capture for each query execution, what fields does each tool call entry record, what fields does the score log track, and what is the minimum number of data points required?

**Concepts found (4/4):**
  - [x] Trace schema captures query_id dataset question trial number timestamp tool_calls final_answer expected_answer pass/fail iterations_used and exploration_ratio
  - [x] Each tool call entry records the step number tool name arguments result_summary success status and duration
  - [x] Score log must have minimum two data points showing baseline and final scores
  - [x] Score log tracks run_id timestamp model trials_per_query pass_at_1 queries_passed and kb_version

**Actual answer:**
Based on the document, here's the breakdown of the fields captured by the evaluation harness:

*   **Trace Schema (per query execution):** `query_id`, `dataset`, `question`, `trial` (trial number), `timestamp`, `tool_calls` (where each tool call entry records `step`, `tool`, `arguments`, `result_summary`, `success`, and `duration_ms`), `final_answer`, `expected_answer`, `pass` (pass/fail), `iterations_used`, `total_tool_calls`, and `exploration_ratio`.

*   **Tool Call Entry (within the Trace Schema):** `step`, `tool`, `arguments`, `result_summary`, `success`, and `duration_ms`.

*   **Score Log Format (across runs):** `run_id`, `timestamp`, `model`, `trials_per_query`, `pass_at_1`, `queries_passed`, `queries_total`, `kb_version`, and `notes`.

*   **Minimum Number of Data Points for Score Log:** At least two data points are required (baseline and final).

**Grader reasoning:** The answer includes all required concepts and avoids forbidden contradictions, thus earning a perfect score.

---

### Question 5 — PASS (100/100)

**Question:** What is the optimal exploration ratio for tool calls according to DAB findings, what happens if the ratio is too low or too high, and what metric tracks whether the agent consults domain knowledge?

**Concepts found (4/4):**
  - [x] The optimal exploration ratio is approximately 20 percent of tool calls being schema inspection
  - [x] If the ratio is below 15 percent the agent dives into queries without understanding the schema leading to wrong data source selection
  - [x] If the ratio is above 30 percent the agent wastes token budget on exploration and runs out of iterations
  - [x] KB hit rate tracks the percentage of queries where KB domain knowledge was consulted

**Actual answer:**
According to the document:

*   The optimal exploration ratio is around **~20%**.
*   If the exploration ratio is **below 15%**, the agent dives into queries without understanding the schema, leading to wrong data source selection.
*   If the exploration ratio is **above 30%**, the agent wastes token budget on exploration and runs out of iterations.
*   The **KB hit rate** metric tracks the percentage of queries where KB domain knowledge was consulted.

**Grader reasoning:** All required concepts are present and no forbidden contradictions are found, so the score is 100.

---
