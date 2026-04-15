#!/usr/bin/env python3
"""Run held-out validation against stored DAB traces; append to score_log (+ optional trace sidecar)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.config_loader import load_config, resolve_profile, repo_root
from eval.scorer import load_validate_fn, score_answer
from eval.trace_logger import summarize_final_agent


def _load_manifest(path: Path) -> dict:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_profile(
    profile_name: str,
    *,
    dry_run: bool,
    config_path: Path | None = None,
) -> dict:
    cfg = load_config(config_path)
    prof = resolve_profile(cfg, profile_name)
    dab_root = Path(cfg["dab_root"])
    manifest_path = Path(cfg["held_out_manifest"])
    manifest = _load_manifest(manifest_path)

    validate = load_validate_fn(dab_root)
    overrides = prof.get("trace_overrides") or {}
    default_suffix = prof.get("default_run_suffix") or "run_2"
    items = manifest.get("items")
    if items:
        datasets = [x["dataset"] if isinstance(x, dict) else x for x in items]
        item_suffix = {}
        for x in items:
            if isinstance(x, dict) and x.get("run_suffix"):
                item_suffix[x["dataset"]] = x["run_suffix"]
    else:
        datasets = manifest.get("datasets") or []
        item_suffix = {}
    query_id = manifest.get("query_id") or "query1"

    per_query = []
    trace_summaries = []
    n_pass = 0
    for ds in datasets:
        suf = overrides.get(ds) or item_suffix.get(ds) or default_suffix
        query_dir = dab_root / ds / query_id
        final_path = query_dir / "logs" / "data_agent" / suf / "final_agent.json"
        if not final_path.exists():
            per_query.append(
                {
                    "dataset": ds,
                    "run_suffix_used": suf,
                    "final_agent": str(final_path),
                    "skipped": True,
                    "reason": "missing_trace",
                }
            )
            continue
        data = json.loads(final_path.read_text(encoding="utf-8"))
        ans = (data.get("final_result") or "").strip()
        vr = score_answer(validate, query_dir, ans)
        ok = bool(vr.get("is_valid"))
        if ok:
            n_pass += 1
        per_query.append(
            {
                "dataset": ds,
                "run_suffix_used": suf,
                "is_valid": ok,
                "validate_reason": vr.get("reason"),
                "final_agent": str(final_path),
            }
        )
        trace_summaries.append({"dataset": ds, **summarize_final_agent(final_path)})

    evaluated = [x for x in per_query if not x.get("skipped")]
    n_total = len(evaluated)
    pass_at_1 = (n_pass / n_total) if n_total else 0.0

    row = {
        "schema_version": 1,
        "run_id": f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{prof['label']}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_role": prof["label"],
        "profile": profile_name,
        "default_run_suffix": default_suffix,
        "trace_overrides": overrides or None,
        "dab_root": str(dab_root),
        "manifest": str(manifest_path),
        "n_total": n_total,
        "n_pass": n_pass,
        "pass_at_1": round(pass_at_1, 4),
        "per_query": per_query,
    }

    if not dry_run:
        score_log = Path(cfg["score_log"])
        score_log.parent.mkdir(parents=True, exist_ok=True)
        with score_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

        side = cfg.get("trace_sidecar")
        if side:
            side_path = Path(side)
            side_path.parent.mkdir(parents=True, exist_ok=True)
            trace_row = {
                "timestamp_utc": row["timestamp_utc"],
                "run_role": row["run_role"],
                "profile": profile_name,
                "trace_summaries": trace_summaries,
            }
            with side_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(trace_row) + "\n")

        results_dir = repo_root() / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        mirror = results_dir / "harness_score_log.jsonl"
        with mirror.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="Oracle Forge DAB held-out harness")
    ap.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Profile name from eval/config.yaml (repeatable)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--config", type=Path, default=None, help="Override eval/config.yaml path")
    ap.add_argument(
        "--reset-log",
        action="store_true",
        help="Truncate score_log and trace sidecar before writing (fresh run)",
    )
    args = ap.parse_args()
    profs = args.profiles or ["first_run", "submission"]
    cfg = load_config(args.config)
    if args.reset_log:
        for key in ("score_log", "trace_sidecar"):
            p = Path(cfg[key])
            if p.is_file():
                p.unlink()
        mirror = repo_root() / "results" / "harness_score_log.jsonl"
        if mirror.is_file():
            mirror.unlink()

    for name in profs:
        row = run_profile(name, dry_run=args.dry_run, config_path=args.config)
        print(json.dumps(row, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
