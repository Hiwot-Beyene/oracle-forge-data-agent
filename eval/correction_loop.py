#!/usr/bin/env python3
"""Build a corrections-ready backlog from latest harness failures."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.config_loader import load_config, repo_root


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _latest_run_failures(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    latest_run_id = rows[-1].get("run_id")
    if latest_run_id:
        return [r for r in rows if r.get("run_id") == latest_run_id]
    return rows


def _write_md(path: Path, failures: list[dict]) -> None:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for f in failures:
        grouped[(f.get("dataset", ""), f.get("query_id", ""))].append(f)

    lines = [
        "# Corrections backlog from latest eval",
        "",
        "Use these entries as direct inputs for `kb/corrections/log.md` updates.",
        "",
    ]
    for (dataset, query_id), rows in sorted(grouped.items()):
        lines.append(f"## {dataset} / {query_id}")
        lines.append("")
        lines.append(f"- Failed trials: {len(rows)}")
        categories = sorted({str(r.get("failure_category", "unknown")) for r in rows})
        lines.append(f"- Failure categories: {', '.join(categories)}")
        for row in rows[:5]:
            lines.append(f"- Example reason: {row.get('validate_reason') or 'N/A'}")
            lines.append(f"- Trace: {row.get('final_agent')}")
        lines.extend(
            [
                "- Template:",
                "  - [Query / pattern]:",
                "  - [Dataset]:",
                "  - [What was wrong]:",
                "  - [Correct approach]:",
                "  - [Join attempted]:",
                "  - [Mismatch cause]:",
                "  - [Fix applied]:",
                "  - [Source logs]:",
                "",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate correction backlog from harness failures.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root() / "kb" / "corrections" / "pending_from_eval.md",
        help="Markdown output path",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    backlog = Path(cfg.get("failure_backlog") or (repo_root() / "eval" / "scores" / "failure_backlog.jsonl"))
    failures = _latest_run_failures(_read_jsonl(backlog))
    _write_md(args.output, failures)

    print(
        json.dumps(
            {
                "status": "ok",
                "source_backlog": str(backlog),
                "output": str(args.output),
                "n_failures_latest_run": len(failures),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
