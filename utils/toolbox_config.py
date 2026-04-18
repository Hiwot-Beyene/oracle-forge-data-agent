"""Merge MCP toolbox YAML configs (shared by Flask app, tests, and tooling)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def forge_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolved_toolbox_config_paths(forge_root: Path | None = None) -> list[Path]:
    root = forge_root or forge_repo_root()
    raw = (os.getenv("MCP_TOOLBOX_CONFIGS") or "").strip()
    if raw:
        out: list[Path] = []
        for part in raw.split(","):
            p = Path(part.strip())
            if not p.is_absolute():
                p = root / p
            out.append(p.resolve())
        return out
    generated = root / "agent" / "mcp" / "tools_dab_generated.yaml"
    if generated.is_file():
        return [generated.resolve()]
    return [(root / "agent" / "mcp" / "tools.yaml").resolve()]


def toolbox_configs_cli_value(forge_root: Path | None = None) -> str:
    return ",".join(str(p) for p in resolved_toolbox_config_paths(forge_root))


def merged_toolbox_tools(forge_root: Path | None = None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for path in resolved_toolbox_config_paths(forge_root):
        if not path.is_file():
            continue
        try:
            parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        tools = parsed.get("tools")
        if isinstance(tools, dict):
            merged.update(tools)
    return merged


def merged_toolbox_sources(forge_root: Path | None = None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for path in resolved_toolbox_config_paths(forge_root):
        if not path.is_file():
            continue
        try:
            parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        srcs = parsed.get("sources")
        if isinstance(srcs, dict):
            merged.update(srcs)
    return merged


def sql_tool_names(forge_root: Path | None = None) -> frozenset[str]:
    tools = merged_toolbox_tools(forge_root)
    return frozenset(
        n
        for n, spec in tools.items()
        if isinstance(spec, dict) and str(spec.get("kind", "")).endswith("-sql")
    )


def tool_kind(tool_name: str, forge_root: Path | None = None) -> str:
    spec = merged_toolbox_tools(forge_root).get(tool_name)
    return str(spec.get("kind", "")) if isinstance(spec, dict) else ""
