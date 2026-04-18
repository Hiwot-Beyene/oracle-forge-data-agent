#!/usr/bin/env python3
"""Run DAB-aligned validation with optional fresh execution and stratified scoring."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.config_loader import load_config, resolve_profile, repo_root
from eval.scorer import load_validate_fn, score_answer
from eval.trace_logger import summarize_final_agent


def _load_manifest(path: Path) -> dict[str, Any]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _dataset_slug(dataset_dir: str) -> str:
    return dataset_dir.replace("query_", "", 1)


def _discover_query_ids(dab_root: Path, dataset_dir: str) -> list[str]:
    ds_dir = dab_root / dataset_dir
    found = []
    for p in sorted(ds_dir.glob("query*")):
        if p.is_dir() and p.name.startswith("query") and p.name[5:].isdigit():
            found.append(p.name)
    return found


def _expand_manifest_cases(
    manifest: dict[str, Any],
    *,
    dab_root: Path,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    items = manifest.get("items")
    if items:
        out = []
        for item in items:
            if isinstance(item, str):
                out.append({"dataset": item, "query_id": manifest.get("query_id") or "query1", "trial": 0})
                continue
            out.append(
                {
                    "dataset": item["dataset"],
                    "query_id": item.get("query_id") or manifest.get("query_id") or "query1",
                    "trial": int(item.get("trial", 0)),
                    "run_suffix": item.get("run_suffix"),
                }
            )
        return out

    datasets = manifest.get("datasets") or []
    if not datasets:
        return []
    query_ids_cfg = manifest.get("query_ids")
    single_query = manifest.get("query_id")
    trial_count = int(manifest.get("trial_count", manifest.get("trials", 1)))
    trial_count = max(1, trial_count)

    out: list[dict[str, Any]] = []
    for ds in datasets:
        if query_ids_cfg == "all":
            query_ids = _discover_query_ids(dab_root, ds)
        elif isinstance(query_ids_cfg, list) and query_ids_cfg:
            query_ids = [str(x) for x in query_ids_cfg]
        else:
            query_ids = [single_query or "query1"]
        for qid in query_ids:
            for trial in range(trial_count):
                out.append({"dataset": ds, "query_id": qid, "trial": trial})
    return out


def _resolve_run_suffix(
    case: dict[str, Any],
    *,
    profile: dict[str, Any],
    overrides: dict[str, str],
) -> str:
    ds = case["dataset"]
    qid = case["query_id"]
    key_q = f"{ds}/{qid}"
    key_t = f"{ds}/{qid}/trial_{case['trial']}"
    if case.get("run_suffix"):
        return str(case["run_suffix"])
    if key_t in overrides:
        return overrides[key_t]
    if key_q in overrides:
        return overrides[key_q]
    if ds in overrides:
        return overrides[ds]

    pattern = profile.get("default_run_suffix_pattern")
    if pattern:
        return str(pattern).format(dataset=ds, query_id=qid, trial=case["trial"])
    return str(profile.get("default_run_suffix") or f"run_{case['trial']}")


def _run_dab_agent(
    *,
    dab_root: Path,
    dataset_dir: str,
    query_id: str,
    run_suffix: str,
    llm: str,
    iterations: int,
    use_hints: bool,
) -> dict[str, Any]:
    runner = dab_root / "run_agent.py"
    dataset = _dataset_slug(dataset_dir)
    qid_int = int(query_id.replace("query", "", 1))
    cmd = [
        sys.executable,
        str(runner),
        "--dataset",
        dataset,
        "--query_id",
        str(qid_int),
        "--llm",
        llm,
        "--iterations",
        str(iterations),
        "--root_name",
        run_suffix,
    ]
    if use_hints:
        cmd.append("--use_hints")
    run_env = os.environ.copy()
    _forge = dab_root.resolve().parent / "oracle-forge-data-agent"
    if _forge.is_dir():
        run_env["ORACLE_FORGE_ROOT"] = str(_forge)
    proc = subprocess.run(
        cmd, cwd=str(dab_root), env=run_env, capture_output=True, text=True, check=False
    )
    return {
        "command": cmd,
        "exit_code": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-1200:],
        "stderr_tail": (proc.stderr or "")[-1200:],
    }


def _classify_failure(reason: str | None) -> str:
    text = (reason or "").lower()
    if any(x in text for x in ("no number", "not found", "empty", "no bant", "missing")):
        return "FM1_output_or_termination"
    if any(x in text for x in ("cross-engine", "engine", "collection")):
        return "FM2_cross_engine_plan"
    if any(x in text for x in ("join", "key", "zero-row", "mismatch")):
        return "FM3_join_key_or_schema"
    return "FM4_semantic_or_extraction"


def _pass_at_k(n: int, c: int, k: int) -> float:
    if n <= 0 or c <= 0:
        return 0.0
    if k <= 1:
        return c / n
    if n - c < k:
        return 1.0
    from math import comb

    return 1.0 - comb(n - c, k) / comb(n, k)


def run_profile(
    profile_name: str,
    *,
    dry_run: bool,
    config_path: Path | None = None,
    execute_missing: bool = False,
    execute_all: bool = False,
    llm: str = "gpt-5-mini",
    iterations: int = 100,
    use_hints: bool = True,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    prof = resolve_profile(cfg, profile_name)
    dab_root = Path(cfg["dab_root"])
    manifest_path = Path(cfg["held_out_manifest"])
    manifest = _load_manifest(manifest_path)

    validate = load_validate_fn(dab_root)
    overrides = prof.get("trace_overrides") or {}
    cases = _expand_manifest_cases(manifest, dab_root=dab_root, profile=prof)

    attempts: list[dict[str, Any]] = []
    trace_summaries = []
    execution_events = []
    failure_backlog = []

    for case in cases:
        ds = case["dataset"]
        qid = case["query_id"]
        suffix = _resolve_run_suffix(case, profile=prof, overrides=overrides)
        query_dir = dab_root / ds / qid
        final_path = query_dir / "logs" / "data_agent" / suffix / "final_agent.json"

        should_execute = execute_all or (execute_missing and not final_path.exists())
        if should_execute:
            execution_events.append(
                {
                    "dataset": ds,
                    "query_id": qid,
                    "trial": case["trial"],
                    "run_suffix_used": suffix,
                    "event": _run_dab_agent(
                        dab_root=dab_root,
                        dataset_dir=ds,
                        query_id=qid,
                        run_suffix=suffix,
                        llm=llm,
                        iterations=iterations,
                        use_hints=use_hints,
                    ),
                }
            )

        if not final_path.exists():
            attempts.append(
                {
                    "dataset": ds,
                    "query_id": qid,
                    "trial": case["trial"],
                    "run_suffix_used": suffix,
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
        reason = vr.get("reason")
        attempt = {
            "dataset": ds,
            "query_id": qid,
            "trial": case["trial"],
            "run_suffix_used": suffix,
            "is_valid": ok,
            "validate_reason": reason,
            "final_agent": str(final_path),
        }
        attempts.append(attempt)
        trace_summaries.append({"dataset": ds, "query_id": qid, "trial": case["trial"], **summarize_final_agent(final_path)})
        if not ok:
            failure_backlog.append(
                {
                    "dataset": ds,
                    "query_id": qid,
                    "trial": case["trial"],
                    "run_suffix_used": suffix,
                    "validate_reason": reason,
                    "failure_category": _classify_failure(reason),
                    "final_agent": str(final_path),
                }
            )

    evaluated = [x for x in attempts if not x.get("skipped")]
    n_total = len(evaluated)
    n_pass = sum(1 for x in evaluated if x.get("is_valid"))
    pass_flat = (n_pass / n_total) if n_total else 0.0

    by_dq: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in evaluated:
        by_dq[(rec["dataset"], rec["query_id"])].append(rec)

    per_query = []
    by_dataset_scores: dict[str, list[float]] = defaultdict(list)
    for (ds, qid), rows in sorted(by_dq.items()):
        n = len(rows)
        c = sum(1 for x in rows if x.get("is_valid"))
        q_pass_1 = _pass_at_k(n, c, 1)
        q_pass_5 = _pass_at_k(n, c, 5)
        by_dataset_scores[ds].append(q_pass_1)
        per_query.append(
            {
                "dataset": ds,
                "query_id": qid,
                "n_attempts": n,
                "n_pass": c,
                "pass_at_1": round(q_pass_1, 4),
                "pass_at_5": round(q_pass_5, 4),
                "attempts": rows,
            }
        )

    per_dataset = []
    for ds, vals in sorted(by_dataset_scores.items()):
        per_dataset.append(
            {
                "dataset": ds,
                "n_queries": len(vals),
                "pass_at_1_dataset_avg": round(mean(vals), 4),
            }
        )

    pass_stratified = mean([x["pass_at_1_dataset_avg"] for x in per_dataset]) if per_dataset else 0.0
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{prof['label']}"
    row = {
        "schema_version": 2,
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_role": prof["label"],
        "profile": profile_name,
        "dab_root": str(dab_root),
        "manifest": str(manifest_path),
        "n_total": n_total,
        "n_pass": n_pass,
        "pass_at_1": round(pass_stratified, 4),
        "pass_at_1_stratified": round(pass_stratified, 4),
        "pass_at_1_flat": round(pass_flat, 4),
        "n_missing_traces": sum(1 for x in attempts if x.get("skipped")),
        "execution": {
            "execute_missing": execute_missing,
            "execute_all": execute_all,
            "llm": llm,
            "iterations": iterations,
            "use_hints": use_hints,
            "events": execution_events,
        },
        "per_dataset": per_dataset,
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

        backlog_path = Path(cfg.get("failure_backlog") or (repo_root() / "eval" / "scores" / "failure_backlog.jsonl"))
        backlog_path.parent.mkdir(parents=True, exist_ok=True)
        with backlog_path.open("a", encoding="utf-8") as f:
            for row_fail in failure_backlog:
                out = {"run_id": run_id, "run_role": prof["label"], "profile": profile_name, **row_fail}
                f.write(json.dumps(out) + "\n")

        results_dir = repo_root() / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        mirror = results_dir / "harness_score_log.jsonl"
        with mirror.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="Oracle Forge DAB benchmark harness")
    ap.add_argument("--profile", action="append", dest="profiles", help="Profile name from eval/config.yaml (repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--config", type=Path, default=None, help="Override eval/config.yaml path")
    ap.add_argument("--execute-missing", action="store_true", help="Run DAB agent for missing traces before scoring")
    ap.add_argument("--execute-all", action="store_true", help="Run DAB agent for every manifest case before scoring")
    ap.add_argument("--llm", default="gpt-5-mini", help="Model passed to DataAgentBench run_agent.py")
    ap.add_argument("--iterations", type=int, default=100, help="Iteration cap passed to DataAgentBench run_agent.py")
    ap.add_argument("--no-hints", action="store_true", help="Disable --use_hints when invoking DataAgentBench")
    ap.add_argument(
        "--reset-log",
        action="store_true",
        help="Truncate score_log, trace sidecar, failure backlog, and results mirror before writing",
    )
    args = ap.parse_args()
    profs = args.profiles or ["first_run", "submission"]
    cfg = load_config(args.config)
    if args.reset_log:
        for key in ("score_log", "trace_sidecar", "failure_backlog"):
            p_raw = cfg.get(key)
            if not p_raw:
                continue
            p = Path(p_raw)
            if p.is_file():
                p.unlink()
        mirror = repo_root() / "results" / "harness_score_log.jsonl"
        if mirror.is_file():
            mirror.unlink()

    for name in profs:
        row = run_profile(
            name,
            dry_run=args.dry_run,
            config_path=args.config,
            execute_missing=args.execute_missing,
            execute_all=args.execute_all,
            llm=args.llm,
            iterations=args.iterations,
            use_hints=not args.no_hints,
        )
        print(json.dumps(row, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
