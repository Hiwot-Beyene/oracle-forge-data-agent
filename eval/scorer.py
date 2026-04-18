"""DAB-aligned validation: load common_scaffold.validate, score answers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


def _ensure_dab_on_syspath(dab_root: Path) -> None:
    """Per-query ``validate.py`` files import ``common_scaffold.*``; that package lives at DAB root."""
    root = str(dab_root.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def load_validate_fn(dab_root: Path):
    dab_root = dab_root.resolve()
    _ensure_dab_on_syspath(dab_root)
    vpath = dab_root / "common_scaffold" / "validate" / "validate.py"
    if not vpath.is_file():
        raise FileNotFoundError(f"DAB validate not found: {vpath}")
    spec = importlib.util.spec_from_file_location("dab_validate", vpath)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    inner = mod.validate

    def validate_with_path(query_dir: Path, llm_answer: str, reason: str | None = None):
        _ensure_dab_on_syspath(dab_root)
        return inner(query_dir, llm_answer, reason)

    return validate_with_path


def score_answer(
    validate,
    query_dir: Path,
    llm_answer: str,
) -> dict[str, Any]:
    return validate(query_dir, (llm_answer or "").strip(), reason=None)
