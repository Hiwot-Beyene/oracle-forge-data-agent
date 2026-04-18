#!/usr/bin/env python3
"""Emit challenge contract JSON from a DataAgentBench final_agent.json path."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.challenge_contract import append_contract_jsonl, build_challenge_contract  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Export TRP1 challenge contract from final_agent.json")
    p.add_argument("--final-agent", type=Path, required=True, help="Path to final_agent.json")
    p.add_argument(
        "--append-jsonl",
        type=Path,
        default=None,
        help="If set, append one JSON line to this file (e.g. results/challenge_contracts.jsonl)",
    )
    p.add_argument("--dataset", type=str, default="", help="Optional dataset slug for extra metadata")
    p.add_argument("--query-id", type=str, default="", help="Optional query id for extra metadata")
    p.add_argument("--run-name", type=str, default="", help="Optional run folder name")
    args = p.parse_args()

    fa = args.final_agent.resolve()
    if not fa.is_file():
        print(json.dumps({"error": f"not_found: {fa}"}), file=sys.stderr)
        return 2

    extra: dict = {}
    if args.dataset:
        extra["dataset"] = args.dataset
    if args.query_id:
        extra["query_id"] = args.query_id
    if args.run_name:
        extra["run_name"] = args.run_name

    contract = build_challenge_contract(fa, extra=extra or None)
    print(json.dumps(contract, ensure_ascii=True, indent=2))
    if args.append_jsonl:
        append_contract_jsonl(contract, args.append_jsonl.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
