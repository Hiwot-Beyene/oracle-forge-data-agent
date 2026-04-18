"""Compare harness score_log roles; exit non-zero if submission regresses vs first_run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.config_loader import load_config


def load_runs(score_log: Path) -> dict[str, dict]:
    by_role: dict[str, dict] = {}
    if not score_log.is_file():
        return by_role
    for line in score_log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        role = row.get("run_role")
        if role:
            by_role[role] = row
    return by_role


def main() -> int:
    p = argparse.ArgumentParser(description="Regression check on harness score_log")
    p.add_argument("--score-log", type=Path, default=None)
    args = p.parse_args()
    cfg = load_config()
    log_path = args.score_log or Path(cfg["score_log"])
    runs = load_runs(log_path)
    first = runs.get("first_run")
    sub = runs.get("submission")
    if not first or not sub:
        print("Need both first_run and submission rows in score log.", file=sys.stderr)
        return 2
    metric_name = "pass_at_1_stratified"
    if metric_name not in first or metric_name not in sub:
        metric_name = "pass_at_1"
    p0 = float(first.get(metric_name, 0))
    p1 = float(sub.get(metric_name, 0))
    ok = p1 >= p0
    print(
        json.dumps(
            {
                "metric": metric_name,
                "first_run_metric_value": p0,
                "submission_metric_value": p1,
                "regression_ok": ok,
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
