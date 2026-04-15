# Evaluation (DataAgentBench alignment)

## Primary metric: pass@1

For each query instance, **pass@1** is the fraction of held-out instances where `validate.py` accepts `final_agent.json` → `final_result` against `ground_truth.csv`.

- **Held-out set:** `eval/held_out/manifest.yaml` — evaluated by `python -m eval.harness` (see `eval/README.md`).

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

Append-only JSONL: `eval/scores/score_log.jsonl` (mirrored to `results/harness_score_log.jsonl` on each harness run). Compare **`first_run`** vs **`submission`** profiles in `eval/config.yaml`.

## Adversarial probes

The challenge requires **`probes/probes.md`** at repo root (15+ probes, 3+ categories). Do not relocate that file under `eval/`.
