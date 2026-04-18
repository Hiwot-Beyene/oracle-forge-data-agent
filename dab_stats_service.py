"""
Compute DataAgentBench aggregate stats using the same functions as the CLI scripts
without modifying DAB.

Oracle Forge stores traces under ``query_*/query*/logs/data_agent/``, which matches
``stats_scripts/avg_pass_k.avg_pass_k`` — not ``results-<model>/`` (used by
``avg_accuracy.py``), so this service exposes only pass@k aggregates for the UI.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from utils.dab_paths import dab_root


def _ensure_dab_import_path(dab: Path) -> None:
    root = str(dab.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def discover_datasets(dab_root_path: Path | None = None) -> list[str]:
    """Match ``avg_pass_k.py`` __main__ dataset discovery."""
    dab = dab_root_path or dab_root()
    return sorted(
        d.name.replace("query_", "")
        for d in dab.iterdir()
        if d.is_dir() and d.name.startswith("query_") and d.name != "query_dataset"
    )


def compute_dab_stats_table(dab_root_path: Path | None = None) -> dict[str, Any]:
    """
    Per dataset (same as ``stats_scripts/avg_pass_k.avg_pass_k``):

    - ``avg_pass_k``: dict ``k ->`` averaged pass@k across queries with logs.
    - ``run_count_min`` / ``run_count_max``: min/max ``run_*`` count across queries
      that contributed to pass@k (for interpreting large ``k`` columns).
    """
    dab = dab_root_path or dab_root()
    _ensure_dab_import_path(dab)

    from common_scaffold.validate.pass_k import K_LIST
    from stats_scripts.accuracy import discover_runs, find_result_dir
    from stats_scripts.avg_pass_k import avg_pass_k

    rows: list[dict[str, Any]] = []
    for dataset in discover_datasets(dab):
        row: dict[str, Any] = {"dataset": dataset}

        query_base = dab / f"query_{dataset}"
        run_counts: list[int] = []
        for folder in sorted(query_base.iterdir()):
            if not folder.is_dir() or not folder.name.startswith("query"):
                continue
            try:
                qid = int(folder.name.replace("query", ""))
            except ValueError:
                continue
            query_dir = query_base / f"query{qid}"
            result_dir = find_result_dir(query_dir)
            if result_dir is None:
                continue
            runs = discover_runs(result_dir)
            if runs:
                run_counts.append(len(runs))

        if run_counts:
            row["run_count_min"] = min(run_counts)
            row["run_count_max"] = max(run_counts)
        else:
            row["run_count_min"] = None
            row["run_count_max"] = None

        _pk_model, pk_avg = avg_pass_k(dataset)
        if pk_avg is None:
            row["avg_pass_k"] = None
        else:
            row["avg_pass_k"] = {int(k): float(v) for k, v in pk_avg.items()}
        rows.append(row)

    return {
        "dab_root": str(dab.resolve()),
        "k_list": list(K_LIST),
        "rows": rows,
    }
