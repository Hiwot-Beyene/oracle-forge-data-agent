# Evaluation harness

Uses **DataAgentBench** `common_scaffold/validate/validate.py` and each query’s `validate.py` + `ground_truth.csv`. Paths come from **`eval/config.yaml`** and **`DAB_ROOT`** (see `.env.example`); no hardcoded benchmark paths in code beyond config defaults.

## Run (repository root)

```bash
export DAB_ROOT=/path/to/DataAgentBench   # optional if sibling ../DataAgentBench exists

python -m eval.harness --reset-log
python -m eval.regression_suite
python -m eval.validate_outputs
```

- **`--profile first_run`** / **`--profile submission`** — repeat flag; default runs both profiles from `eval/config.yaml`.
- **`--dry-run`** — print JSON only; do not append logs.
- **`--reset-log`** — truncate `eval/scores/score_log.jsonl`, `eval/scores/trace_summary.jsonl`, and `results/harness_score_log.jsonl` before writing.

## Run roles (strict meaning)

- **`first_run`**: immutable baseline role used for "before" measurement (defaults to `run_1` in `config.yaml`).
- **`submission`**: candidate/final role used for "after" measurement (defaults to `run_2` + explicit `trace_overrides`).
- Regression policy is strict: `submission.pass_at_1 >= first_run.pass_at_1`.

## Layout

| File | Role |
|------|------|
| `harness.py` | CLI: validate stored traces, append score log + trace sidecar + `results/` mirror |
| `scorer.py` | Load DAB `validate`, score one answer |
| `trace_logger.py` | Summarize `final_agent.json` (tool counts, duration) |
| `regression_suite.py` | Exit 1 if `submission.pass_at_1` < `first_run.pass_at_1` |
| `validate_outputs.py` | Exit 1 if artifacts/evidence violate challenge requirements |
| `config.yaml` / `config_loader.py` | Repo-relative paths, profiles, `trace_overrides` |
| `held_out/manifest.yaml` | Held-out datasets × `query1` |
| `scores/score_log.jsonl` | Append-only aggregate metrics |

## Docs

- Scoring: `kb/evaluation/README.md`
- Adversarial probes (challenge location): **`probes/probes.md`** (repo root, not under `eval/`)
