# KB Evaluation — DAB Overview

_Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.0 — Initial population from DAB paper (arxiv 2603.20576) and Practitioner Manual_

---

## SECTION A: What DAB Is

DataAgentBench (DAB) is the first benchmark that evaluates AI data agents on realistic enterprise workloads. Published by UC Berkeley EPIC Data Lab + PromptQL (Hasura), March 2026.

- **54 queries** across **12 datasets**, **9 domains**, **4 database systems**
- Database systems: PostgreSQL, MongoDB, SQLite, DuckDB — often multiple in the same query
- All 54 queries require multi-DB integration; 47/54 require text transformation; 26/54 have ill-formatted join keys; 30/54 need domain knowledge
- Best frontier model (no scaffold): ~38% pass@1
- Best scaffolded system: PromptQL + Gemini-3.1-Pro at 54.3% pass@1
- **1,147 annotated failure trajectories** analyzed for failure mode classification

---

## SECTION B: DAB Query Format

### Agent Input (per query)

Each DAB query provides the agent with:

| Field | Type | Description |
|-------|------|-------------|
| `question` | string | Natural language business question |
| `db_ids` | list[string] | Database identifiers available for this query (e.g., `["bookreview_postgres", "bookreview_sqlite"]`) |
| `hint` | string (optional) | Clarification hint — use with `--use_hints` flag |

### Agent Output (per query)

The agent must return:

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | The final answer to the business question |
| `tool_calls` | list[object] | Full trace of every tool call made (tool name, arguments, result) |
| `iterations` | int | Number of agent loop iterations used |

### Available Tools (DAB scaffold)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `query_db` | Execute a query against a specific database | Fetching data from PostgreSQL, MongoDB, SQLite, or DuckDB |
| `list_db` | Introspect schema — list tables, columns, sample values | First 2-3 calls of any query for exploration |
| `execute_python` | Run Python code in a sandboxed Docker container | Data transformation, cross-DB joins in pandas, text extraction, statistical tests |
| `return_answer` | Submit the final answer and terminate the agent loop | Once and only once per query — this ends the session |

---

## SECTION C: Scoring Method — pass@1

### Definition

**pass@1** = fraction of queries where the agent returns the correct answer on the first trial. Each query is scored as binary pass/fail with no partial credit — the answer is either fully correct or it counts as a failure.

Formula: `pass@1 = (number of queries correct on first attempt) / 54`

### Trial Protocol

- **50 trials per query** minimum (required for benchmark submission)
- Each trial is an independent run — fresh context, no memory of prior trials
- pass@1 is computed per query, then averaged across all 54 queries
- pass@50 is also reported: fraction of queries solved in at least 1 of 50 trials (measures capability ceiling)

### Scoring Rules

- Each query is scored as binary pass/fail with no partial credit
- Answer must match the expected answer exactly or within tolerance defined per query
- Validation is done by `eval/score.py` in the DAB repository
- The `validate/validate.py` module checks answer format compliance before scoring

### Current Leaderboard (March 2026)

| System | pass@1 | pass@50 |
|--------|--------|---------|
| PromptQL + Gemini-3.1-Pro | 54.3% | — |
| PromptQL + Claude-Opus-4.6 | 50.8% | — |
| Gemini-3-Pro (no scaffold) | 38% | 69% |
| GPT-5.2 (no scaffold) | 36% | 67% |
| Gemini-2.5-Flash (no scaffold) | 33% | 63% |

---

## SECTION D: Benchmark Submission Requirements

### What to Submit

A GitHub Pull Request to `ucbepic/DataAgentBench` containing:

1. **Results JSON** — `submission/team_[name]_results.json` with all 54 queries, 50 trials each
2. **AGENT.md** — Architecture overview, key design decisions, what worked, what did not
3. **PR title** following the format: `[Team Name] — TRP1 FDE Programme, April 2026`
4. **PR body** must include the pass@1 score, the trial count, and a brief architecture description

**Important:** The PR body is required and must include the pass@1 score, the trial count, and a brief architecture description. PRs without this information in the body will be rejected.

### How to Generate Results

```bash
cd DataAgentBench
python eval/run_benchmark.py \
  --agent your_agent_module \
  --trials 50 \
  --output results/your_team_results.json

# Verify score
python eval/score.py --results results/your_team_results.json
```

### Submission Steps

```bash
# Fork ucbepic/DataAgentBench on GitHub
cp results/your_team_results.json submission/team_[name]_results.json
git add submission/team_[name]_results.json AGENT.md
git commit -m "Add [Team Name] DAB evaluation results"
git push origin main
# Open PR from fork to ucbepic/DataAgentBench
```

---

## SECTION E: Evaluation Harness Schema

### Purpose

The evaluation harness traces every tool call, records query outcomes against expected results, and produces a score that must improve measurably between Week 8 baseline and final submission.

### Trace Schema (per query execution)

The trace schema captures the following fields for each query execution: `query_id`, `dataset`, `question`, `trial` (trial number), `timestamp`, `tool_calls` (where each tool call entry records `step`, `tool`, `arguments`, `result_summary`, `success`, and `duration_ms`), `final_answer`, `expected_answer`, `pass` (pass/fail), `iterations_used`, `total_tool_calls`, and `exploration_ratio`.

### Score Log Format (across runs)

Each score log data point records `run_id`, `timestamp`, `model`, `trials_per_query`, `pass_at_1`, `queries_passed`, `queries_total`, `kb_version`, and `notes`. At least two data points are required (baseline and final).

### Regression Suite

- A held-out set of queries that the agent must continue to pass after every change
- If a previously-passing query starts failing, the change that caused it must be investigated
- Stored in `eval/held_out_test_set.json` with expected answers

### Key Metrics to Track

| Metric | What It Measures | Target |
|--------|------------------|--------|
| pass@1 | First-trial accuracy | Higher is better; improvement required |
| Exploration ratio | % of tool calls that are schema inspection | ~20% optimal (below 15%: agent dives into queries without understanding the schema, leading to wrong data source selection; above 30%: agent wastes token budget on exploration and runs out of iterations) |
| Average iterations | Agent loop steps per query | Lower is more efficient |
| Self-correction rate | % of failures recovered via retry | Higher indicates robust error handling |
| KB hit rate | % of queries where KB domain knowledge was consulted | Should increase as KB grows |

---

_CHANGELOG: v1.0 created April 14 2026. Initial population from DAB paper, Practitioner Manual, and Challenge document._
