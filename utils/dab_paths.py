"""Single place for DataAgentBench path resolution (overridable via env)."""
from __future__ import annotations

import os
from pathlib import Path

_DEFAULT_DAB = "/week8-9/DataAgentBench"


def dab_root() -> Path:
    return Path((os.getenv("DAB_ROOT") or _DEFAULT_DAB).strip()).expanduser().resolve()


def dab_env_file(forge_default_sibling: bool = True) -> Path:
    """
    DAB `.env` path. If unset, default sibling layout:
 ``<forge_parent>/DataAgentBench/.env`` when forge_default_sibling and FORGE_ROOT set,
    else ``dab_root() / '.env'`` is NOT used by legacy app — keep compatibility with app.py
    which used fixed path. Prefer explicit DAB_ENV_FILE.
    """
    explicit = (os.getenv("DAB_ENV_FILE") or "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    fr = (os.getenv("ORACLE_FORGE_ROOT") or "").strip()
    if forge_default_sibling and fr:
        return (Path(fr).resolve().parent / "DataAgentBench" / ".env").resolve()
    return dab_root() / ".env"


def dab_duckdb_yelp_file() -> Path:
    return Path(
        (os.getenv("DAB_DUCKDB_YELP_FILE") or "").strip()
        or str(dab_root() / "query_yelp" / "query_dataset" / "yelp_user.db")
    ).expanduser().resolve()
