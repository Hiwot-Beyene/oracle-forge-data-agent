# 4. Evaluation Harness — Baseline Score and Methodology

This section describes the evaluation harness in `eval/`, how it scores the
agent against the DataAgentBench ground truth, the held-out set it runs
against, and the interim baseline vs submission numbers it produced for
Sprint 1. Sources of truth referenced: `eval/harness.py`, `eval/scorer.py`,
`eval/config.yaml`, `eval/held_out/manifest.yaml`, `eval/scores/score_log.jsonl`.

---

## 4.1 What the harness is (and is not)

**The harness is a re-scorer over stored DAB agent traces, not an agent
runner.** The DataAgentBench scaffold executes the agent and writes a
`final_agent.json` trace to disk; the harness reads those traces back,
applies DAB's own validator, and writes a structured score row.

This separation is deliberate. It means that:

- Every historical agent run can be re-scored whenever the validator, the
  held-out manifest, or the scoring rules change — without re-running the
  agent or re-paying for LLM calls.
- The score log and the agent traces have independent lifecycles. A trace
  on disk is the permanent artefact; the score row is a derived view.
- Scoring is reproducible from any machine that can read the DAB clone and
  the oracle-forge repo — no agent, no API keys, no databases needed.

**Lineage.** This is the Sentinel pattern from Week 5 (Event Sourcing)
applied to data agents. The trace-summary shape in `trace_logger.py` is
explicitly annotated `"Sentinel-style"`; the regression suite in
`regression_suite.py` follows the same role-comparison approach. No new
scoring philosophy has been invented — the Week 5 work carried across.

---

## 4.2 Harness architecture (`eval/`)

| Module | Lines | Role |
|---|---|---|
| `__main__.py` | 13 | Entry point — `python -m eval` |
| `harness.py` | 171 | Reads manifest + profile, resolves trace paths, scores each dataset, appends to score log |
| `scorer.py` | 26 | Loads DAB's `common_scaffold/validate/validate.py` and invokes it per query |
| `config_loader.py` | 86 | Resolves `eval/config.yaml`, profiles, DAB root (env `$DAB_ROOT` or sibling-repo fallback) |
| `trace_logger.py` | 27 | Summarises `final_agent.json` into the trace sidecar (Sentinel-style) |
| `regression_suite.py` | 52 | Compares `submission` role against `first_run` role; exits non-zero on regression |
| `validate_outputs.py` | 142 | Strict artefact-shape validator (schema, required fields) for score-log rows |

**Inputs per run:**

- `eval/config.yaml` — profile definitions (`first_run`, `submission`) with
  per-dataset run-suffix overrides and a default suffix.
- `eval/held_out/manifest.yaml` — the list of datasets (currently all 12
  DAB query1 entries) to score against.
- `$DAB_ROOT/<dataset>/query1/logs/data_agent/<suffix>/final_agent.json` —
  the stored agent trace to be scored.

**Outputs per run:**

- `eval/scores/score_log.jsonl` — append-only JSONL, one row per profile run.
- `eval/scores/trace_summary.jsonl` — per-run tool-call / message-count
  summary sidecar.
- `results/harness_score_log.jsonl` — mirror of the score log under the
  submission directory.

---

## 4.3 Methodology

### Scoring a single dataset

1. Resolve the run suffix:
   `profile.trace_overrides[<dataset>]` → `manifest.items[<dataset>].run_suffix` → `profile.default_run_suffix`.
2. Open
   `<dab_root>/<dataset>/query1/logs/data_agent/<suffix>/final_agent.json`.
   If the file does not exist, mark the entry `skipped: true,
   reason: missing_trace` and exclude it from the denominator.
3. Read the `final_result` field (the agent's final natural-language
   answer, stripped).
4. Call DAB's own validator:
   `validate(<dab_root>/<dataset>/query1, answer_string)`. This is the
   same function DAB uses to produce the leaderboard score — we do not
   substitute our own comparator.
5. Record `is_valid` (pass/fail) and `validate_reason` (the validator's
   human-readable explanation) on the per-query row.

### Aggregating a profile

`n_total = count(entries where not skipped)`,
`n_pass = count(entries where is_valid)`,
`pass_at_1 = n_pass / n_total` (rounded to 4 decimals; `0.0` when
`n_total == 0`).

Every profile run writes exactly one row to `score_log.jsonl`. Rows are
never rewritten — the score log is an append-only progression log, which
is what the rubric's "measurable improvement between runs" evidence
requires.

### Held-out set (`eval/held_out/manifest.yaml`)

Twelve DAB datasets, `query1` per dataset:

```
query_bookreview, query_yelp, query_agnews, query_stockmarket,
query_stockindex, query_crmarenapro, query_googlelocal, query_PATENTS,
query_PANCANCER_ATLAS, query_GITHUB_REPOS, query_DEPS_DEV_V1,
query_music_brainz_20k
```

Datasets without an on-disk agent trace are honestly skipped and
excluded from the denominator, rather than silently counted as failures.

### Profiles (`eval/config.yaml`)

Two roles are defined for Sprint 1. The trace overrides below point at
the agent runs currently checked into the DAB clone:

| Profile | default_run_suffix | trace_overrides |
|---|---|---|
| `first_run` | `run_0` | `query_bookreview: run_0`, `query_yelp: run_0` |
| `submission` | `run_4` | `query_bookreview: run_4`, `query_yelp: run_1` |

`first_run` scores the earliest agent runs available on disk —
genuinely the team's baseline, not a cherry-picked low-water mark.
`submission` scores the latest runs per dataset, which is what the team
would submit if the PR were cut at the interim.

---

## 4.4 Baseline and submission scores (2026-04-15)

Produced by running `DAB_ROOT=... python -m eval --reset-log` against the
current DAB trace state. Both rows landed in `eval/scores/score_log.jsonl`.

| Run id | Role | Traces scored | n_pass / n_total | pass@1 |
|---|---|---|---|---|
| `20260415T131132Z_first_run` | `first_run` | bookreview `run_0`, yelp `run_0` | 1 / 2 | **0.5000** |
| `20260415T131132Z_submission` | `submission` | bookreview `run_4`, yelp `run_1` | 2 / 2 | **1.0000** |

### What moved the score

The single behavioural change between `first_run` and `submission` was on
the yelp query — cross-collection reasoning about average business rating
in Indianapolis:

| Dataset | Baseline (`first_run`) answer | Submission (`run_1`) answer | Ground truth | Outcome |
|---|---|---|---|---|
| `query_bookreview` | `"2020s"` | `"2020s"` | decade-of-publication check | Passes at both roles |
| `query_yelp` | `"The average rating… is 4.0."` | `"…approximately 3.55."` | `≈ 3.55` | Baseline FAIL, submission PASS |

Bookreview passed even at baseline because the PostgreSQL ↔ SQLite join
(via `book_id` ↔ `purchase_id`) was already covered by the MCP Toolbox
tool descriptions plus `kb/domain/join_key_glossary.md`. The yelp delta
comes from the Layer-2 domain knowledge now reaching the agent — that
`yelp_db.business` (MongoDB) holds metadata only and ratings live in
DuckDB `review.rating`. Crossing that boundary correctly is what turned
`4.0` into `3.55`, which is a Layer-2 context win rather than a raw
LLM-capability win.

### What is excluded (honest scoping)

The remaining 10 manifest datasets (`agnews`, `stockmarket`, `stockindex`,
`crmarenapro`, `googlelocal`, `PATENTS`, `PANCANCER_ATLAS`, `GITHUB_REPOS`,
`DEPS_DEV_V1`, `music_brainz_20k`) have no agent traces in the DAB clone
yet. The harness records them in each row with
`skipped: true, reason: missing_trace` and excludes them from `n_total`,
which is why the interim denominators are 2 rather than 12. Sprint 2
adds coverage using the same ingestion, routing, and scoring pattern
used for bookreview and yelp.

### Trials

Sprint 1 scores `n = 1` trial per dataset. The DAB benchmark submission
spec requires `n ≥ 50` trials per query at submission time; that is a
Sprint 2 deliverable and is why the harness writes to a separate score
role (`submission`) rather than claiming the DAB leaderboard format.

---

## 4.5 Score-row schema

Each row in `eval/scores/score_log.jsonl` looks like:

```json
{
  "schema_version": 1,
  "run_id": "20260415T131132Z_submission",
  "timestamp_utc": "2026-04-15T13:11:32.919940+00:00",
  "run_role": "submission",
  "profile": "submission",
  "default_run_suffix": "run_4",
  "trace_overrides": {"query_bookreview": "run_4", "query_yelp": "run_1"},
  "dab_root": "/path/to/DataAgentBench",
  "manifest": "/path/to/oracle-forge-data-agent/eval/held_out/manifest.yaml",
  "n_total": 2,
  "n_pass": 2,
  "pass_at_1": 1.0,
  "per_query": [
    {
      "dataset": "query_bookreview",
      "run_suffix_used": "run_4",
      "is_valid": true,
      "validate_reason": "Ground truth found in LLM output.",
      "final_agent": "<path>/final_agent.json"
    },
    {
      "dataset": "query_yelp",
      "run_suffix_used": "run_1",
      "is_valid": true,
      "validate_reason": "Found matching number: 3.55 \u2248 3.55",
      "final_agent": "<path>/final_agent.json"
    }
    // ...skipped entries follow
  ]
}
```

The `validate_reason` field is produced by DAB's own validator, not by
the harness — it is the explanation the DAB scorer would give for the
leaderboard.

---

## 4.6 Regression suite

`eval/regression_suite.py` loads the score log, indexes by `run_role`,
and compares `submission` to `first_run`. It exits non-zero if
`submission.pass_at_1 < first_run.pass_at_1`. This is the Sprint-1
guard against silent regressions when the team re-runs the harness as
new agent traces land. At the interim, `submission - first_run = +0.5`
(regression check passes).

---

## 4.7 How to reproduce

```bash
# From the oracle-forge repo root, with the DAB fork cloned at a sibling
# path (or $DAB_ROOT set):
DAB_ROOT=/abs/path/to/DataAgentBench python -m eval --reset-log

# --reset-log truncates score_log.jsonl + trace_summary.jsonl + the
# results/ mirror before writing, so the file holds only the two rows
# produced by this invocation. Omit it to append for progression tracking.

# Score only one profile:
python -m eval --profile submission
```

Outputs land in `eval/scores/` (primary) and `results/harness_score_log.jsonl`
(submission-packaged mirror).

---

## 4.8 What is deferred

- **Full 12-dataset coverage.** 10 of 12 manifest datasets have no agent
  trace yet. Sprint 2 onboards them using the same DAB scaffold runner
  (`run_agent.py`) under the team's OpenRouter configuration.
- **n ≥ 50 trials per query** for the DAB leaderboard submission.
- **Adversarial probe library integration.** Probe outcomes will be
  recorded as additional score-log roles so probe-driven improvements
  show up in the same append-only progression.
- **Regression tests inside `validate_outputs.py`.** The strict artefact
  validator currently guards score-row shape; extending it to guard the
  manifest and the DAB `validate.py` signature is Sprint 2.

---

## Summary

| Item | Interim status |
|---|---|
| Harness architecture | Re-scorer over stored DAB traces; Sentinel-pattern trace summary + regression suite |
| Validator | DAB's own `common_scaffold/validate/validate.py` — no substitute comparator |
| Held-out set | 12 DAB datasets, `query1` per dataset |
| Profiles | `first_run` (baseline trace_overrides) and `submission` (latest trace_overrides) |
| Baseline `pass@1` | **0.5000** (1/2): bookreview PASS, yelp FAIL (answered `4.0` vs `≈3.55`) |
| Submission `pass@1` | **1.0000** (2/2): bookreview PASS, yelp PASS (answered `3.55`) |
| Improvement | **+0.5** pass@1; driven by Layer-2 KB knowledge about yelp's MongoDB-metadata / DuckDB-ratings split |
| Regression gate | `submission ≥ first_run` — passes |
| Trials | `n = 1` per dataset (Sprint 1); `n ≥ 50` is Sprint 2 for the DAB PR |

The harness is intentionally a thin, reproducible wrapper around DAB's own
validator. Every score in this report can be re-derived by anyone with the
DAB clone and the oracle-forge repo, without running the agent or
touching the databases.
