"""Load eval/config.yaml with env substitution; resolve paths from repo root."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    return _REPO_ROOT


def _expand_env_in_str(s: str) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return os.environ.get(key, "")

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, s)


def _walk_expand(obj: Any) -> Any:
    if isinstance(obj, str):
        return _expand_env_in_str(obj)
    if isinstance(obj, dict):
        return {k: _walk_expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_expand(x) for x in obj]
    return obj


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or (_REPO_ROOT / "eval" / "config.yaml")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg = _walk_expand(raw)
    dab = (cfg.get("dab_root") or "").strip()

    # Accept explicit config only when it resolves to a real DAB root.
    resolved_from_cfg = None
    if dab and not dab.startswith("/path/to/"):
        p = Path(dab)
        resolved_from_cfg = (_REPO_ROOT / p).resolve() if not p.is_absolute() else p.resolve()
    if resolved_from_cfg and (resolved_from_cfg / "common_scaffold" / "validate" / "validate.py").is_file():
        cfg["dab_root"] = str(resolved_from_cfg)
    else:
        # Robust fallback order:
        # 1) env DAB_ROOT if valid
        # 2) known machine path /wek8/DataAgentBench
        # 3) sibling checkout ../DataAgentBench
        candidates = []
        env_dab = (os.environ.get("DAB_ROOT") or "").strip()
        if env_dab and not env_dab.startswith("/path/to/"):
            candidates.append(Path(env_dab).resolve())
        candidates.append(Path("/wek8/DataAgentBench"))
        candidates.append((_REPO_ROOT.parent / "DataAgentBench").resolve())

        chosen = None
        for cand in candidates:
            if (cand / "common_scaffold" / "validate" / "validate.py").is_file():
                chosen = cand
                break
        if not chosen:
            raise RuntimeError(
                "Could not resolve DataAgentBench root. "
                "Set DAB_ROOT to a valid checkout containing common_scaffold/validate/validate.py."
            )
        cfg["dab_root"] = str(chosen)

    for key in ("held_out_manifest", "score_log", "trace_sidecar"):
        if key in cfg and cfg[key]:
            rel = Path(cfg[key])
            if not rel.is_absolute():
                cfg[key] = str((_REPO_ROOT / rel).resolve())
    return cfg


def resolve_profile(cfg: dict[str, Any], name: str) -> dict[str, Any]:
    profiles = cfg.get("profiles") or {}
    if name not in profiles:
        raise KeyError(f"Unknown profile {name!r}; defined: {list(profiles)}")
    return profiles[name]
