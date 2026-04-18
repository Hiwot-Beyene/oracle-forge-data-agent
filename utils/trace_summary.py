"""Summarize DataAgent message / tool traces for challenge contract and UI."""
from __future__ import annotations

import hashlib
import json
from typing import Any

MAX_SNIPPET = 240


def hash_payload(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]


def truncate(s: str, limit: int = MAX_SNIPPET) -> str:
    s = (s or "").strip()
    if len(s) <= limit:
        return s
    return s[: limit - 3] + "..."


def tool_steps_from_messages(messages: Any) -> list[dict[str, Any]]:
    if not isinstance(messages, list):
        return []
    steps: list[dict[str, Any]] = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        tool_calls = msg.get("tool_calls")
        if not isinstance(tool_calls, list):
            continue
        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function")
            if not isinstance(fn, dict):
                continue
            name = str(fn.get("name") or "")
            raw_args = fn.get("arguments")
            args_str = raw_args if isinstance(raw_args, str) else json.dumps(raw_args or {})
            steps.append(
                {
                    "tool": name,
                    "arguments_preview": truncate(args_str),
                    "arguments_sha256_12": hash_payload(args_str),
                    "tool_call_id": str(tc.get("id") or ""),
                }
            )
    return steps


def tool_failures_in_messages(messages: Any) -> bool:
    if not isinstance(messages, list):
        return False
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "tool":
            continue
        content = msg.get("content")
        if isinstance(content, str) and "execution failed" in content.lower():
            return True
    return False
