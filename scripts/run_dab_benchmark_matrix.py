#!/usr/bin/env python3
"""
Batch driver for DataAgentBench trials with resume support.

Writes (under ``--output-dir`` if writable, else ``results/``, else ``var/benchmark_outputs/``):
  - team_results_<timestamp>.json — aggregate summary
  - benchmark_batch_resume.jsonl — completed (dataset, query_number, trial) keys
  - benchmark_pr_template.md — PR title/body stub for ucbepic/DataAgentBench

Usage:
  cd oracle-forge-data-agent
  python3 scripts/run_dab_benchmark_matrix.py --dab-root /path/to/DataAgentBench --trials 1 --llm google/gemini-2.0-flash-001
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from benchmark_service import BenchmarkService  # noqa: E402
from utils.dab_paths import dab_root  # noqa: E402


def _writable_results_dir(forge: Path, preferred: Path | None) -> Path:
    """Prefer ``results/``; fall back to ``var/benchmark_outputs`` if not writable (e.g. root-owned)."""
    candidates: list[Path] = []
    if preferred is not None:
        candidates.append(preferred)
    candidates.extend([forge / "results", forge / "var" / "benchmark_outputs"])
    for cand in candidates:
        try:
            cand.mkdir(parents=True, exist_ok=True)
            probe = cand / ".write_probe"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return cand
        except OSError:
            continue
    return forge


def _load_done(path: Path) -> set[tuple[str, int, int]]:
    done: set[tuple[str, int, int]] = set()
    if not path.is_file():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
            done.add((str(o["dataset"]), int(o["query_number"]), int(o["trial"])))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return done


def _append_resume(path: Path, dataset: str, query_number: int, trial: int, ok: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "dataset": dataset,
                    "query_number": query_number,
                    "trial": trial,
                    "ok": ok,
                    "ts": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=True,
            )
            + "\n"
        )


def main() -> int:
    p = argparse.ArgumentParser(description="Run DAB matrix with resume log.")
    p.add_argument("--dab-root", type=Path, default=None, help="DataAgentBench root (default: DAB_ROOT env or utils.dab_paths)")
    p.add_argument("--forge-root", type=Path, default=_ROOT)
    p.add_argument("--trials", type=int, default=1, help="Trials per query (e.g. 50 for full submission)")
    p.add_argument("--llm", type=str, default=os.getenv("BENCHMARK_LLM", "gpt-4o-mini"))
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--no-hints", action="store_true")
    p.add_argument("--dataset", type=str, default="", help="Optional: single dataset slug (e.g. yelp)")
    p.add_argument("--resume-file", type=Path, default=None)
    p.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for team_results JSON and PR template (default: results/ or var/benchmark_outputs/)",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    dab = (args.dab_root or dab_root()).resolve()
    forge = args.forge_root.resolve()
    out_base = _writable_results_dir(
        forge,
        args.output_dir.resolve() if args.output_dir is not None else None,
    )
    resume_path = (args.resume_file or (out_base / "benchmark_batch_resume.jsonl")).resolve()
    done = _load_done(resume_path)

    svc = BenchmarkService(dab, forge)
    catalog = svc.discover_catalog()
    if args.dataset.strip():
        catalog = [x for x in catalog if x["dataset_slug"] == args.dataset.strip()]
    if not catalog:
        print(json.dumps({"error": "no_datasets_matched", "dab_root": str(dab)}))
        return 2

    results_dir = out_base
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_json = results_dir / f"team_results_{ts}.json"

    trial_results: list[dict] = []
    scheduled = 0
    skipped = 0

    for ds in catalog:
        slug = ds["dataset_slug"]
        for q in ds["queries"]:
            qn = int(q["query_number"])
            for trial in range(max(1, args.trials)):
                key = (slug, qn, trial)
                if key in done:
                    skipped += 1
                    continue
                scheduled += 1
                if args.dry_run:
                    trial_results.append({"dataset": slug, "query_number": qn, "trial": trial, "dry_run": True})
                    continue
                bq = svc.get_query(slug, qn)
                if bq is None:
                    trial_results.append({"dataset": slug, "query_number": qn, "trial": trial, "ok": False, "error": "get_query failed"})
                    _append_resume(resume_path, slug, qn, trial, False)
                    continue
                res = svc.run_single_trial(
                    bq,
                    llm=args.llm,
                    iterations=args.iterations,
                    use_hints=not args.no_hints,
                )
                ok = bool(res.get("ok"))
                trial_results.append(
                    {
                        "dataset": slug,
                        "query_number": qn,
                        "trial": trial,
                        "ok": ok,
                        "is_valid": (res.get("ops") or {}).get("is_valid") if ok else None,
                        "run_name": res.get("run_name"),
                    }
                )
                _append_resume(resume_path, slug, qn, trial, ok)

    summary = {
        "schema": "oracle_forge.team_results.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dab_root": str(dab),
        "forge_root": str(forge),
        "llm": args.llm,
        "iterations": args.iterations,
        "trials_per_query": max(1, args.trials),
        "scheduled_runs": scheduled,
        "skipped_already_done": skipped,
        "dry_run": args.dry_run,
        "trial_results": trial_results,
    }
    out_json.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")

    pr_path = results_dir / "benchmark_pr_template.md"
    pr_path.write_text(
        "\n".join(
            [
                "# DataAgentBench PR template",
                "",
                "**Title:** [Team Name] — TRP1 FDE Programme, April 2026",
                "",
                "## Summary",
                "",
                f"- Batch artifact: `{out_json.name}`",
                f"- Resume log: `{resume_path.name}`",
                "- Replace this stub with pass@1, trial count, and architecture pointers from `agent/AGENT.md`.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps({"wrote": str(out_json), "resume": str(resume_path), "pr_template": str(pr_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
