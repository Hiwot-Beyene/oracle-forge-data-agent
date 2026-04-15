"""Summarize agent traces (Sentinel-style) for harness sidecar logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_final_agent(final_agent_path: Path) -> dict[str, Any]:
    """Lightweight trace summary from DataAgentBench final_agent.json."""
    if not final_agent_path.is_file():
        return {"error": "missing", "path": str(final_agent_path)}
    data = json.loads(final_agent_path.read_text(encoding="utf-8"))
    msgs = data.get("messages") or []
    tool_calls = 0
    for m in msgs:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            tool_calls += len(m["tool_calls"])
    return {
        "path": str(final_agent_path),
        "duration_sec": data.get("duration"),
        "terminate_reason": data.get("terminate_reason"),
        "final_result_len": len((data.get("final_result") or "")),
        "assistant_messages": sum(1 for m in msgs if m.get("role") == "assistant"),
        "tool_call_count": tool_calls,
    }
