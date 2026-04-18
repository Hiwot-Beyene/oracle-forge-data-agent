# Evaluation harness

Uses **DataAgentBench** `common_scaffold/validate/validate.py` and each query’s `validate.py` + `ground_truth.csv`.

## Challenge-aligned scope

- Full benchmark: 12 datasets, all query folders (`query1..queryN`), configured by `eval/held_out/manifest.yaml`.
- Multi-trial runs: default `trial_count: 5`, expected run folder pattern `run_<trial>`.
- Stratified scoring: per-query pass@1 -> per-dataset average -> benchmark average.

## Run (repository root)

```bash
export DAB_ROOT=/path/to/DataAgentBench

# Option A: score existing traces
python -m eval.harness --reset-log

# Option B: generate missing traces, then score
python -m eval.harness --reset-log --execute-missing --llm gpt-5-mini --iterations 100

# Option C: regenerate all traces, then score
python -m eval.harness --reset-log --execute-all --llm gpt-5-mini --iterations 100

python -m eval.regression_suite
python -m eval.validate_outputs
python -m eval.correction_loop
```

## Benchmark UI workflow

The app now runs in benchmark-only mode. Start it with:

```bash
cd /week8-9/oracle-forge-data-agent
python3 app.py
```

From the UI:

1. select dataset + question text (query picker)
2. click **Run One Trial** (auto assigns next `run_<n>`)
3. or click **Run Until N** to fill trials up to target
4. click **Export Submission JSON** for PR-ready DAB rows

Generated files:

- `results/benchmark_submission_rows.jsonl` (normalized rows cache)
- `results/benchmark_ops_log.jsonl` (validation + runtime metadata)
- `results/dab_submission_<timestamp>.json` (leaderboard payload)

## Key flags

- `--profile first_run` / `--profile submission` (repeatable; default runs both).
- `--execute-missing` runs `DataAgentBench/run_agent.py` only for missing traces.
- `--execute-all` reruns all benchmark attempts from manifest.
- `--no-hints` disables `--use_hints` when invoking DAB runner.
- `--dry-run` prints JSON only, without writing logs.

## Outputs

- `eval/scores/score_log.jsonl`: run-level metrics with `pass_at_1_stratified`, `pass_at_1_flat`, `per_dataset`, `per_query`.
- `eval/scores/trace_summary.jsonl`: per-attempt trace summaries.
- `eval/scores/failure_backlog.jsonl`: failed attempts linked to correction categories.
- `results/harness_score_log.jsonl`: mirror of score log.
- `kb/corrections/pending_from_eval.md`: auto-generated correction backlog template (`python -m eval.correction_loop`).

## Regression rule

- `submission` must not regress against `first_run` on `pass_at_1_stratified` (fallback `pass_at_1` for legacy rows).
