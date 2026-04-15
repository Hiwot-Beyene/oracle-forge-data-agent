# Results

- **`harness_score_log.jsonl`** — append-only mirror of `eval/scores/score_log.jsonl`, written whenever you run `python -m eval.harness` from the repository root (see `eval/README.md`).
- DAB PR JSON and leaderboard screenshots belong here per programme checklist when available.

If `harness_score_log.jsonl` is missing, generate it:

```bash
cd /path/to/oracle-forge-data-agent
python -m eval.harness --reset-log
```

Then run `python -m eval.regression_suite` to confirm `submission` pass@1 ≥ `first_run`.
