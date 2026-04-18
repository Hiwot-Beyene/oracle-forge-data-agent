"""DuckDB URI override behavior in dab_toolbox_codegen (no network)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from agent.mcp.dab_toolbox_codegen import generate_duckdb_overlay_dict, generate_toolbox_dict


def test_duckdb_source_uses_per_dataset_env_placeholder():
    root = Path(tempfile.mkdtemp())
    ds = root / "query_my_ds"
    ds.mkdir(parents=True)
    (ds / "db_config.yaml").write_text(
        "db_clients:\n  duck1:\n    db_type: duckdb\n    db_path: ./db.duckdb\n",
        encoding="utf-8",
    )
    (ds / "db.duckdb").write_bytes(b"")

    os.environ["DAB_TOOLBOX_DUCKDB_URI_MY_DS"] = "md:test_remote"
    try:
        data = generate_toolbox_dict(root)
    finally:
        os.environ.pop("DAB_TOOLBOX_DUCKDB_URI_MY_DS", None)

    duck_sources = {k: v for k, v in data["sources"].items() if k.startswith("dab-src-duckdb-")}
    assert len(duck_sources) == 1
    _name, spec = next(iter(duck_sources.items()))
    assert spec["kind"] == "duckdb"
    assert spec["database"] == "${DAB_TOOLBOX_DUCKDB_URI_MY_DS}"


def test_duckdb_source_uses_global_env_when_no_per_dataset():
    root = Path(tempfile.mkdtemp())
    ds = root / "query_other"
    ds.mkdir(parents=True)
    (ds / "db_config.yaml").write_text(
        "db_clients:\n  d:\n    db_type: duckdb\n    db_path: ./x.duckdb\n",
        encoding="utf-8",
    )
    (ds / "x.duckdb").write_bytes(b"")

    os.environ["DAB_TOOLBOX_DUCKDB_URI"] = "md:global_db"
    try:
        data = generate_toolbox_dict(root)
    finally:
        os.environ.pop("DAB_TOOLBOX_DUCKDB_URI", None)

    spec = next(s for s in data["sources"].values() if s.get("kind") == "duckdb")
    assert spec["database"] == "${DAB_TOOLBOX_DUCKDB_URI}"


def test_duckdb_source_uses_absolute_path_by_default():
    root = Path(tempfile.mkdtemp())
    ds = root / "query_plain"
    ds.mkdir(parents=True)
    (ds / "db_config.yaml").write_text(
        "db_clients:\n  d:\n    db_type: duckdb\n    db_path: ./f.duckdb\n",
        encoding="utf-8",
    )
    (ds / "f.duckdb").write_bytes(b"")

    for key in ("DAB_TOOLBOX_DUCKDB_URI_PLAIN", "DAB_TOOLBOX_DUCKDB_URI"):
        os.environ.pop(key, None)
    data = generate_toolbox_dict(root)
    spec = next(s for s in data["sources"].values() if s.get("kind") == "duckdb")
    assert spec["database"].endswith("f.duckdb")
    assert not spec["database"].startswith("${")


def test_duckdb_overlay_matches_full_duckdb_slice():
    root = Path(tempfile.mkdtemp())
    for name in ("query_a", "query_b"):
        ds = root / name
        ds.mkdir(parents=True)
        (ds / "db_config.yaml").write_text(
            "db_clients:\n  d:\n    db_type: duckdb\n    db_path: ./x.duckdb\n",
            encoding="utf-8",
        )
        (ds / "x.duckdb").write_bytes(b"")

    full = generate_toolbox_dict(root)
    overlay = generate_duckdb_overlay_dict(root)
    duck_full_tools = {k for k, v in full["tools"].items() if v.get("kind") == "duckdb-sql"}
    assert set(overlay["tools"]) == duck_full_tools
    assert len(overlay["sources"]) == 2
    assert "dab-duckdb-all" in overlay["toolsets"]
    assert len(overlay["toolsets"]["dab-duckdb-all"]) == 2


def test_yelp_legacy_env_wins_after_per_dataset_dab():
    root = Path(tempfile.mkdtemp())
    ds = root / "query_yelp"
    ds.mkdir(parents=True)
    (ds / "db_config.yaml").write_text(
        "db_clients:\n  d:\n    db_type: duckdb\n    db_path: ./y.duckdb\n",
        encoding="utf-8",
    )
    (ds / "y.duckdb").write_bytes(b"")

    os.environ["DUCKDB_YELP_USER_PATH"] = "md:legacy_yelp"
    try:
        data = generate_toolbox_dict(root)
    finally:
        os.environ.pop("DUCKDB_YELP_USER_PATH", None)

    spec = next(s for s in data["sources"].values() if s.get("kind") == "duckdb")
    assert spec["database"] == "${DUCKDB_YELP_USER_PATH}"
