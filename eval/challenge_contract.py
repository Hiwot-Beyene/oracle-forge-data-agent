"""
Map DataAgentBench final_agent.json to the TRP1 pedagogical contract:
  { answer, query_trace, confidence }

confidence is a discrete enum (never a fake float): high | medium | low | unknown
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Literal

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.trace_summary import tool_failures_in_messages, tool_steps_from_messages

ConfidenceLevel = Literal["high", "medium", "low", "unknown"]


def _read_validation_last(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    last: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            last = json.loads(line)
        except json.JSONDecodeError:
            continue
    return last


def derive_confidence(
    data: dict[str, Any],
    *,
    validation_is_valid: bool | None = None,
) -> ConfidenceLevel:
    """Heuristic confidence from final_agent fields and optional DAB validation."""
    term = str(data.get("terminate_reason") or "")
    answer = str(data.get("final_result") or "").strip()
    messages = data.get("messages")

    if validation_is_valid is True:
        return "high"
    if validation_is_valid is False:
        return "low"

    if "agent_run_failed" in term or term.lower().startswith("error"):
        return "low"
    if not answer:
        return "low"
    if tool_failures_in_messages(messages):
        return "low"
    if term == "return_answer" and answer:
        return "medium"
    return "unknown"


def build_challenge_contract(
    final_agent_path: Path,
    *,
    extra: dict[str, Any] | None = None,
    validation_is_valid: bool | None = None,
) -> dict[str, Any]:
    """
    Build the challenge-aligned JSON object from a DAB final_agent.json path.
    """
    path = final_agent_path.resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("final_agent.json root must be an object")

    run_dir = path.parent
    tool_log = run_dir / "tool_calls.jsonl"
    llm_log = run_dir / "llm_calls.jsonl"
    val_log = run_dir / "validation.jsonl"

    val_last = _read_validation_last(val_log)
    effective_valid: bool | None = validation_is_valid
    if effective_valid is None and isinstance(val_last, dict) and "is_valid" in val_last:
        effective_valid = bool(val_last["is_valid"])

    messages = raw.get("messages")
    steps = tool_steps_from_messages(messages)

    contract: dict[str, Any] = {
        "schema": "oracle_forge.challenge_contract.v1",
        "answer": str(raw.get("final_result") or ""),
        "confidence": derive_confidence(raw, validation_is_valid=effective_valid),
        "query_trace": {
            "final_agent_path": str(path),
            "terminate_reason": str(raw.get("terminate_reason") or ""),
            "duration_sec": raw.get("duration"),
            "llm_call_count": raw.get("llm_call_count"),
            "tool_steps": steps,
            "artifact_paths": {
                "tool_calls_jsonl": str(tool_log) if tool_log.is_file() else None,
                "llm_calls_jsonl": str(llm_log) if llm_log.is_file() else None,
                "validation_jsonl": str(val_log) if val_log.is_file() else None,
            },
            "validation_last": val_last,
        },
    }
    if extra:
        contract["extra"] = extra
    return contract


def append_contract_jsonl(contract: dict[str, Any], jsonl_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(contract, ensure_ascii=True) + "\n")
