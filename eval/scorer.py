"""DAB-aligned validation: load common_scaffold.validate, score answers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def load_validate_fn(dab_root: Path):
    vpath = dab_root / "common_scaffold" / "validate" / "validate.py"
    if not vpath.is_file():
        raise FileNotFoundError(f"DAB validate not found: {vpath}")
    spec = importlib.util.spec_from_file_location("dab_validate", vpath)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod.validate


def score_answer(
    validate,
    query_dir: Path,
    llm_answer: str,
) -> dict[str, Any]:
    return validate(query_dir, (llm_answer or "").strip(), reason=None)
