# Evaluation (DataAgentBench alignment)

## Primary metric: pass@1 (stratified)

For each query, **pass@1** is computed from multi-trial correctness (`n_pass / n_trials`).  
Benchmark score is then **stratified**:

1. average query pass@1 within each dataset
2. average those per-dataset values across datasets

- **Benchmark set:** `eval/held_out/manifest.yaml` — can run all query folders and multi-trial scoring via `python -m eval.harness`.

## DAB alignment

Scoring uses DataAgentBench `common_scaffold/validate/validate.py`, which loads each query’s `validate.py` and compares to `ground_truth.csv`.

## Failure taxonomy

Aligned with `kb/corrections/log.md` and **`probes/probes.md`** (programme-required location at repository root):

| Code | Category |
|------|-----------|
| FM1 | Tool / iteration / empty answer |
| FM2 | Wrong cross-engine plan |
| FM3 | Schema / join-key mismatch |
| FM4 | Dialect / extraction / numeric semantics |

## Score log

Append-only JSONL: `eval/scores/score_log.jsonl` (mirrored to `results/harness_score_log.jsonl`).

- `pass_at_1_stratified`: challenge-aligned primary metric
- `pass_at_1_flat`: raw attempt-level pass fraction
- `per_dataset`: dataset-level averages
- `per_query`: query-level attempt stats

Compare **`first_run`** vs **`submission`** profiles in `eval/config.yaml`.

## Corrections linkage

Failed attempts are exported to `eval/scores/failure_backlog.jsonl` with failure category tags.  
Generate a corrections-ready template with:

```bash
python -m eval.correction_loop
```

## Adversarial probes

The challenge requires **`probes/probes.md`** at repo root (15+ probes, 3+ categories). Do not relocate that file under `eval/`.
