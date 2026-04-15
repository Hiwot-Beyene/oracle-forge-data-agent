#!/usr/bin/env python3
"""Strict validation of challenge evaluation artifacts and evidence quality."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.config_loader import load_config, repo_root


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        _fail(f"Missing file: {path}")
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            _fail(f"{path} has invalid JSONL at line {i}: {e}")
    return rows


def _validate_score_rows(rows: list[dict]) -> None:
    if len(rows) < 2:
        _fail("score_log.jsonl must contain at least two data points (first_run and submission).")

    by_role = {r.get("run_role"): r for r in rows if r.get("run_role")}
    if "first_run" not in by_role or "submission" not in by_role:
        _fail("score_log.jsonl must include both run_role=first_run and run_role=submission.")

    required = {"schema_version", "run_id", "timestamp_utc", "run_role", "n_total", "n_pass", "pass_at_1", "per_query"}
    for r in rows:
        missing = sorted(required - set(r))
        if missing:
            _fail(f"score_log row missing keys {missing}: role={r.get('run_role')}")
        if not isinstance(r["per_query"], list) or not r["per_query"]:
            _fail(f"score_log row per_query must be a non-empty list: role={r.get('run_role')}")
        if int(r["n_total"]) <= 0:
            _fail(f"score_log n_total must be > 0: role={r.get('run_role')}")

    p0 = float(by_role["first_run"]["pass_at_1"])
    p1 = float(by_role["submission"]["pass_at_1"])
    if p1 < p0:
        _fail(f"submission pass@1 regressed: first_run={p0}, submission={p1}")


def _validate_trace_sidecar(path: Path, score_rows: list[dict]) -> None:
    traces = _read_jsonl(path)
    if len(traces) < 2:
        _fail("trace_summary.jsonl must contain at least two rows.")
    score_roles = {r["run_role"] for r in score_rows if r.get("run_role")}
    trace_roles = {r.get("run_role") for r in traces if r.get("run_role")}
    if not {"first_run", "submission"}.issubset(trace_roles):
        _fail("trace_summary.jsonl must contain run_role=first_run and run_role=submission.")
    if not score_roles.issubset(trace_roles):
        _fail("trace_summary.jsonl is missing roles present in score_log.jsonl.")


def _validate_probes(path: Path) -> None:
    if not path.is_file():
        _fail(f"Missing probes file: {path}")
    text = path.read_text(encoding="utf-8")
    lines = [x for x in text.splitlines() if x.strip().startswith("| P")]
    if len(lines) < 15:
        _fail(f"probes.md must contain at least 15 probe rows, found {len(lines)}.")

    categories = set()
    bad_tokens = {"n/a", "same as", "held-out", "pending", "tbd", "todo"}
    for ln in lines:
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 7:
            _fail(f"Malformed probe row (expected 7 columns): {ln}")
        category = cols[2].lower()
        categories.add(category)
        for idx in (0, 1, 2, 3, 4, 5, 6):
            if not cols[idx]:
                _fail(f"Probe row has empty required column {idx+1}: {ln}")
        post_fix = cols[6].lower()
        if any(tok in post_fix for tok in bad_tokens):
            _fail(
                "Probe post-fix score must be explicit and measurable "
                f"(no placeholders). Bad row: {ln}"
            )
        if not re.search(r"(pass@1|[0-9]+/[0-9]+|[0-9]+\.[0-9]+)", cols[6], flags=re.I):
            _fail(f"Probe post-fix score must contain measurable value: {ln}")

    if len(categories) < 3:
        _fail(f"probes.md must cover at least 3 failure categories, found {len(categories)}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate challenge evaluation artifacts.")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    score_log = Path(cfg["score_log"])
    trace_sidecar = Path(cfg["trace_sidecar"])
    mirror = repo_root() / "results" / "harness_score_log.jsonl"
    probes = repo_root() / "probes" / "probes.md"

    rows = _read_jsonl(score_log)
    _validate_score_rows(rows)
    _validate_trace_sidecar(trace_sidecar, rows)
    _ = _read_jsonl(mirror)
    _validate_probes(probes)

    print(
        json.dumps(
            {
                "status": "ok",
                "checks": [
                    "score_log shape + regression",
                    "trace_summary coverage",
                    "results mirror present",
                    "probes format + 15+ rows + 3+ categories + measurable post-fix scores",
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
