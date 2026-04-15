from __future__ import annotations

import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

DAB_ROUTE_STOPWORDS = frozenset(
    """
    the a an is are was were be been being to of and or for in on at by with from as it its this that these those
    what which who how when where why can could should would will may might must shall do does did done
    any all each every both few more most other some such same than then too very just only also not no
    yes about into through over out up down our your their one two first last next per via
    sql query table database data row column select from where join left right inner outer group order limit
    """.split()
)

import duckdb
from flask import Flask, render_template, request
from openai import OpenAI
import yaml
import sqlite3
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)

ROOT = Path(__file__).resolve().parent
LOCAL_ENV_FILE = ROOT / ".env"
TOOLBOX_PATH = ROOT / "agent" / "mcp" / "toolbox"
TOOLS_FILE = ROOT / "agent" / "mcp" / "tools.yaml"
DAB_ENV_FILE = Path("/week8-9/DataAgentBench/.env")
DAB_ROOT = Path("/week8-9/DataAgentBench")
DAB_DUCKDB_FILE = Path("/week8-9/DataAgentBench/query_yelp/query_dataset/yelp_user.db")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MONGO_FORBIDDEN_QUERY_OPS = frozenset({"$where", "$accumulator", "$function"})
AGG_PIPELINE_ALLOWED = frozenset(
    {
        "$match",
        "$project",
        "$group",
        "$sort",
        "$limit",
        "$skip",
        "$count",
        "$addFields",
        "$replaceRoot",
        "$unwind",
    }
)

YELP_DUCK_AGG: dict[str, str] = {
    "avg_rating": "AVG(rating) AS value",
    "count_reviews": "COUNT(*) AS value",
    "sum_rating": "SUM(rating) AS value",
    "min_rating": "MIN(rating) AS value",
    "max_rating": "MAX(rating) AS value",
}

# US states: (full name, USPS) — used only to build safe $regex clauses on description text, not hardcoded cities.
US_STATES_FULL_ABBR: list[tuple[str, str]] = [
    ("Alabama", "AL"), ("Alaska", "AK"), ("Arizona", "AZ"), ("Arkansas", "AR"),
    ("California", "CA"), ("Colorado", "CO"), ("Connecticut", "CT"), ("Delaware", "DE"),
    ("Florida", "FL"), ("Georgia", "GA"), ("Hawaii", "HI"), ("Idaho", "ID"),
    ("Illinois", "IL"), ("Indiana", "IN"), ("Iowa", "IA"), ("Kansas", "KS"),
    ("Kentucky", "KY"), ("Louisiana", "LA"), ("Maine", "ME"), ("Maryland", "MD"),
    ("Massachusetts", "MA"), ("Michigan", "MI"), ("Minnesota", "MN"), ("Mississippi", "MS"),
    ("Missouri", "MO"), ("Montana", "MT"), ("Nebraska", "NE"), ("Nevada", "NV"),
    ("New Hampshire", "NH"), ("New Jersey", "NJ"), ("New Mexico", "NM"), ("New York", "NY"),
    ("North Carolina", "NC"), ("North Dakota", "ND"), ("Ohio", "OH"), ("Oklahoma", "OK"),
    ("Oregon", "OR"), ("Pennsylvania", "PA"), ("Rhode Island", "RI"), ("South Carolina", "SC"),
    ("South Dakota", "SD"), ("Tennessee", "TN"), ("Texas", "TX"), ("Utah", "UT"),
    ("Vermont", "VT"), ("Virginia", "VA"), ("Washington", "WA"), ("West Virginia", "WV"),
    ("Wisconsin", "WI"), ("Wyoming", "WY"), ("District of Columbia", "DC"),
]

YELP_METRICS_SCALAR = "scalar_aggregate"
YELP_METRICS_RANK = "rank_businesses_by_avg_rating"

MONGO_AGG_RESULT_CAP = 500


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def apply_env_files() -> None:
    """Load DataAgentBench/.env then oracle-forge/.env so project keys (e.g. OPENROUTER) override."""
    for path in (DAB_ENV_FILE, LOCAL_ENV_FILE):
        if not path.exists():
            continue
        for key, value in load_env_file(path).items():
            os.environ[key] = value


apply_env_files()
OPENROUTER_ROUTER_MODEL = os.getenv("OPENROUTER_ROUTER_MODEL", "google/gemini-2.0-flash-001")
OPENROUTER_SYNTH_MODEL = os.getenv("OPENROUTER_SYNTH_MODEL", "").strip() or OPENROUTER_ROUTER_MODEL

TOOLBOX_SQL_TOOL_NAMES = frozenset(
    {"postgres-bookreview", "sqlite-bookreview", "mongo-yelp-business", "mongo-yelp-aggregate"}
)


def openrouter_api_key() -> str:
    return (os.getenv("OPENROUTER_API_KEY") or "").strip()


def parse_toolbox_output(raw: str) -> Any:
    lines = raw.splitlines()
    candidate_indices = [
        i
        for i, line in enumerate(lines)
        if line.strip().startswith("{") or line.strip().startswith("[")
    ]
    for idx in candidate_indices:
        candidate = "\n".join(lines[idx:])
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return {"raw_output": raw}


def run_toolbox(tool_name: str, payload: dict[str, Any]) -> Any:
    apply_env_files()
    env = os.environ.copy()
    cmd = [
        str(TOOLBOX_PATH),
        "invoke",
        tool_name,
        json.dumps(payload),
        "--tools-file",
        str(TOOLS_FILE),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    raw = result.stdout if result.stdout else result.stderr
    if result.returncode != 0:
        return {"error": raw}
    return parse_toolbox_output(raw)


def nl_to_sql(source: str, text: str) -> str:
    lower = text.lower()
    if source == "postgres":
        if "table" in lower:
            return (
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name LIMIT 50;"
            )
        if "count" in lower and "book" in lower:
            return "SELECT COUNT(*) AS total_books FROM books_info;"
        return "SELECT title, author, rating_number FROM books_info ORDER BY rating_number DESC LIMIT 10;"
    if source == "sqlite":
        if "table" in lower:
            return "SELECT name FROM sqlite_master WHERE type = 'table';"
        return "SELECT name FROM sqlite_master WHERE type = 'table';"
    if source == "duckdb":
        if "table" in lower:
            return "SHOW TABLES;"
        return "SHOW TABLES;"
    return ""


def normalize_sqlite_style_strftime_for_duckdb(sql: str) -> str:
    """SQLite uses strftime('fmt', col); DuckDB uses strftime(col, 'fmt'). Only rewrite when the first
    argument is single-quoted (SQLite format string). DuckDB-native strftime(\"Date\", '%Y') starts
    with a double quote and must not be touched."""
    pattern = re.compile(
        r"\bstrftime\s*\(\s*"
        r"('(?:[^']|'')*')\s*,\s*"
        r"((?:\"[^\"]+\"|'[^']+'|[A-Za-z_][\w.]*)(?:\s*::\s*[A-Za-z_]+)?)"
        r"\s*\)",
        re.IGNORECASE,
    )
    sql = pattern.sub(lambda m: f"strftime({m.group(2).strip()}, {m.group(1)})", sql)
    return _duckdb_strftime_cast_varchar_date_column(sql)


def _duckdb_strftime_cast_varchar_date_column(sql: str) -> str:
    """DAB stock DuckDB tables often store dates as VARCHAR; strftime needs DATE/TIMESTAMP first arg."""
    pattern = re.compile(
        r"\bstrftime\s*\(\s*"
        r"((?:\"[^\"]+\"|`[^`]+`))\s*,\s*"
        r"('(?:[^']|'')*%[^']*')"
        r"\s*\)",
        re.IGNORECASE,
    )

    def repl(m: re.Match[str]) -> str:
        col = m.group(1).strip()
        fmt = m.group(2)
        if col.upper().startswith("CAST"):
            return m.group(0)
        return f"strftime(CAST({col} AS DATE), {fmt})"

    return pattern.sub(repl, sql)


def run_duckdb(query: str, db_path: Path | None = None) -> Any:
    target = db_path or DAB_DUCKDB_FILE
    if not target.exists():
        return {"error": f"DuckDB file not found: {target}"}
    query = normalize_sqlite_style_strftime_for_duckdb(query)
    policy = assert_readonly_duckdb(query)
    if policy:
        return {"error": policy}
    apply_env_files()
    md_token = (os.getenv("MOTHERDUCK_TOKEN") or "").strip()
    use_md = os.getenv("DUCKDB_LOCAL_USE_MOTHERDUCK", "").strip().lower() in ("1", "true", "yes")
    md_con: Any = None
    try:
        if md_token and use_md:
            md_con = duckdb.connect(f"md:?motherduck_token={md_token}")
            esc = str(target.resolve()).replace("'", "''")
            alias = "dab_local_attached"
            md_con.execute(f"ATTACH '{esc}' AS {alias} (TYPE DUCKDB)")
            md_con.execute(f"USE {alias}")
            rows = md_con.execute(query).fetchdf()
            return rows.to_dict(orient="records")
        with duckdb.connect(str(target), read_only=True) as conn:
            rows = conn.execute(query).fetchdf()
            return rows.to_dict(orient="records")
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    finally:
        if md_con is not None:
            try:
                md_con.close()
            except Exception:  # noqa: BLE001
                pass


def _sql_write_guard(low: str) -> str | None:
    for bad in (" insert ", " update ", " delete ", " attach ", " detach ", " drop ", " create ", " alter ", " replace "):
        if bad in f" {low} ":
            return "Write / DDL keywords are not allowed in local SQL."
    return None


def assert_readonly_sqlite(sql: str) -> str | None:
    s = sql.strip()
    if ";" in s.rstrip(";").strip():
        return "Only a single read-only SQL statement is allowed."
    low = s.lower()
    if not re.match(r"^(select|with|explain|pragma)\b", low):
        return "Local SQLite accepts read-only SELECT/WITH/EXPLAIN/PRAGMA only."
    return _sql_write_guard(low)


def assert_readonly_duckdb(sql: str) -> str | None:
    s = sql.strip()
    if ";" in s.rstrip(";").strip():
        return "Only a single read-only SQL statement is allowed."
    low = s.lower()
    if not re.match(r"^(select|with|show|describe|explain|pragma)\b", low):
        return "Local DuckDB accepts read-only SELECT/WITH/SHOW/DESCRIBE/EXPLAIN/PRAGMA only."
    return _sql_write_guard(low)


def run_sqlite(query: str, db_path: Path) -> Any:
    if not db_path.exists():
        return {"error": f"SQLite file not found: {db_path}"}
    policy = assert_readonly_sqlite(query)
    if policy:
        return {"error": policy}
    try:
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(f"EXPLAIN {query}")
            rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def is_sql_like(text: str) -> bool:
    stripped = text.strip()
    if re.match(r"^(select|with|describe|pragma|explain)\b", stripped, re.IGNORECASE):
        return True
    if re.match(r"^show\s+(tables|databases|columns|create)\b", stripped, re.IGNORECASE):
        return True
    return False


def _walk_bson_keys(obj: Any, *, keys_out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys_out.add(str(k))
            _walk_bson_keys(v, keys_out=keys_out)
    elif isinstance(obj, list):
        for i in obj:
            _walk_bson_keys(i, keys_out=keys_out)


def validate_mongo_filter(flt: dict[str, Any]) -> str | None:
    if not isinstance(flt, dict):
        return "mongo_filter must be a JSON object."
    keys: set[str] = set()
    _walk_bson_keys(flt, keys_out=keys)
    if keys & MONGO_FORBIDDEN_QUERY_OPS:
        return "Filter uses a forbidden operator."
    return None


def validate_mongo_pipeline(pipeline: list[Any]) -> str | None:
    if not isinstance(pipeline, list):
        return "pipeline must be a JSON array."
    for stage in pipeline:
        if not isinstance(stage, dict) or not stage:
            return "Each pipeline stage must be a non-empty object."
        for k in stage:
            if not str(k).startswith("$"):
                return "Pipeline stage keys must be Mongo operators."
            if str(k) not in AGG_PIPELINE_ALLOWED:
                return f"Pipeline stage {k!r} is not allowed for read-only tools."
    return None


def extract_mongo_collections_from_description(desc: str, client_name: str) -> list[str]:
    if not desc.strip():
        return []
    lines = desc.splitlines()
    sec_start: int | None = None
    for i, raw in enumerate(lines):
        line = raw.strip()
        if re.match(rf"^\d+\.\s+{re.escape(client_name)}\b", line):
            sec_start = i
            break
    if sec_start is None:
        return []
    sec_end = len(lines)
    for j in range(sec_start + 1, len(lines)):
        if re.match(r"^\d+\.\s+[A-Za-z_]", lines[j].strip()):
            sec_end = j
            break
    section = "\n".join(lines[sec_start:sec_end])
    m = re.search(
        r"consists\s+of\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+collections?\s*:\s*",
        section,
        re.I,
    )
    if not m:
        return []
    after = section[m.end() :]
    cols: list[str] = []
    for line in after.splitlines():
        lm = re.match(r"^(\s*)-\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$", line)
        if not lm:
            continue
        ind = len(lm.group(1).expandtabs())
        tok = lm.group(2)
        if tok in {"This", "Fields"} or tok.startswith("_"):
            continue
        if ind > 6:
            continue
        cols.append(tok)
    return cols


def sql_tables_referenced(sql: str) -> set[str]:
    if not sql or not isinstance(sql, str):
        return set()
    s = re.sub(r"'(?:[^'\\]|\\.)*'", " ", sql)
    s = re.sub(r'"(?:[^"\\]|\\.)*"', " ", s)
    low = s.lower()
    names: set[str] = set()
    for m in re.finditer(r"\bfrom\s+\"?([a-zA-Z_][\w]*)\"?", low):
        names.add(m.group(1))
    for m in re.finditer(r"\bjoin\s+\"?([a-zA-Z_][\w]*)\"?", low):
        names.add(m.group(1))
    skip = {
        "select",
        "where",
        "group",
        "order",
        "limit",
        "offset",
        "as",
        "on",
        "using",
        "natural",
        "inner",
        "left",
        "right",
        "outer",
        "cross",
        "join",
        "with",
    }
    return {n for n in names if n.lower() not in skip}


def validate_sqlite_plan_schema(plan: dict[str, Any]) -> str | None:
    route = plan.get("route") or {}
    if route.get("executor") != "sqlite-local":
        return None
    q = plan.get("query")
    if not isinstance(q, str) or not q.strip():
        return "SQLite plan is missing query text."
    db_path_s = str(route.get("database") or "").strip()
    if not db_path_s:
        return "SQLite plan is missing database path."
    p = Path(db_path_s)
    refs = sql_tables_referenced(q)
    if not refs:
        return None
    live = {t["table"].lower() for t in live_schema_sqlite_cached(p)}
    if not live:
        return None
    missing = sorted({r for r in refs if r.lower() not in live})
    if missing:
        have = ", ".join(sorted(live))
        return f"SQLite references unknown table(s): {', '.join(missing)}. Actual tables: {have}"
    return None


def validate_duckdb_plan_schema(plan: dict[str, Any]) -> str | None:
    route = plan.get("route") or {}
    if route.get("executor") != "duckdb-local":
        return None
    q = plan.get("query")
    if not isinstance(q, str) or not q.strip():
        return "DuckDB plan is missing query text."
    db_path_s = str(route.get("database") or "").strip()
    if not db_path_s:
        return "DuckDB plan is missing database path."
    p = Path(db_path_s)
    low = q.lower().strip()
    if re.match(r"^(show|describe|pragma)\b", low):
        return None
    refs = sql_tables_referenced(q)
    if not refs:
        return None
    live = {t["table"].lower() for t in live_schema_duckdb_cached(p)}
    if not live:
        return None
    missing = sorted({r for r in refs if r.lower() not in live})
    if missing:
        have = ", ".join(sorted(live))
        return f"DuckDB references unknown table(s): {', '.join(missing)}. Actual tables: {have}"
    return None


def business_id_to_review_ref(business_id: str) -> str | None:
    m = re.match(r"^businessid_(\d+)$", str(business_id).strip(), re.IGNORECASE)
    if not m:
        return None
    return f"businessref_{m.group(1)}"


def review_ref_to_business_id(ref: str) -> str | None:
    m = re.match(r"^businessref_(\d+)$", str(ref).strip(), re.IGNORECASE)
    if not m:
        return None
    return f"businessid_{m.group(1)}"


def _state_regex_clauses(full_name: str, abbr: str) -> list[dict[str, Any]]:
    return [
        {"description": {"$regex": rf",\s*{re.escape(abbr)}\b", "$options": "i"}},
        {"description": {"$regex": rf"\b{re.escape(full_name)}\b", "$options": "i"}},
    ]


def mongo_filter_for_city_state(city: str, state_raw: str) -> dict[str, Any] | None:
    """Build read-only Mongo filter: city token + state (US full name or 2-letter) on description."""
    city = re.sub(r"\s+", " ", city.strip())
    state_raw = state_raw.strip().rstrip(".,;:\"'")
    if len(city) < 2 or len(state_raw) < 2:
        return None
    sk = state_raw.lower()
    sa = state_raw.upper() if len(state_raw) == 2 and state_raw.isalpha() else None
    clauses: list[dict[str, Any]] = [{"description": {"$regex": re.escape(city), "$options": "i"}}]
    matched: list[tuple[str, str]] | None = None
    for full, ab in US_STATES_FULL_ABBR:
        if sk == full.lower() or sa == ab:
            matched = [(full, ab)]
            break
    if matched is None and sa and len(sa) == 2:
        for full, ab in US_STATES_FULL_ABBR:
            if ab == sa:
                matched = [(full, ab)]
                break
    if matched:
        full, ab = matched[0]
        clauses.append({"$or": _state_regex_clauses(full, ab)})
    else:
        clauses.append({"description": {"$regex": re.escape(state_raw), "$options": "i"}})
    return {"$and": clauses}


def extract_city_state_from_question(text: str) -> tuple[str, str] | None:
    """Extract (city, state) from natural language; no city allowlist — pattern-based only."""
    t = text.strip().strip('"').strip("'")
    patterns = [
        re.compile(
            r"located\s+in\s+([^,\n]+?)\s*,\s*([A-Za-z][A-Za-z\.\s\-]{1,40}?)(?=\s*[,\?\"\']|\s+ranked|\s*$)",
            re.I,
        ),
        re.compile(
            r"\b([A-Za-z][A-Za-z\s\-\']{0,80}?)\s*,\s*((?:[A-Z]{2})|(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))\s*"
            r"(?=\s*[,\?\"\']|\s+ranked|\s*$)",
            re.I,
        ),
    ]
    for pat in patterns:
        m = pat.search(t)
        if not m:
            continue
        city = re.sub(r"\s+", " ", m.group(1).strip())
        state = re.sub(r"\s+", " ", m.group(2).strip()).rstrip(".,;:\"'")
        if city.lower().startswith("the "):
            city = city[4:].strip()
        if len(city) >= 2 and len(state) >= 2:
            return city, state
    return None


def yelp_user_duckdb_path(db_options: dict[str, dict[str, str]]) -> Path | None:
    for _key, info in db_options.items():
        if info.get("dataset") == "query_yelp" and info.get("db_type") == "duckdb":
            return Path(info["path"])
    if DAB_DUCKDB_FILE.exists():
        return DAB_DUCKDB_FILE
    return None


def run_yelp_analytics(
    mongo_filter: dict[str, Any],
    db_options: dict[str, dict[str, str]],
    *,
    duckdb_aggregation: str = "avg_rating",
    yelp_metrics_mode: str = YELP_METRICS_SCALAR,
    yelp_rank_limit: int = 5,
    order_desc: bool = True,
) -> Any:
    err = validate_mongo_filter(mongo_filter)
    if err:
        return {"error": err}
    if yelp_metrics_mode not in {YELP_METRICS_SCALAR, YELP_METRICS_RANK}:
        return {"error": f"Unknown yelp_metrics_mode {yelp_metrics_mode!r}."}
    if yelp_metrics_mode == YELP_METRICS_SCALAR and duckdb_aggregation not in YELP_DUCK_AGG:
        return {"error": f"Unknown duckdb_aggregation {duckdb_aggregation!r}."}
    rlim = max(1, min(50, int(yelp_rank_limit)))
    apply_env_files()
    merged = {**os.environ}
    uri = merged.get("MONGO_URI")
    if not uri:
        return {"error": "MONGO_URI is not set."}
    duck_path = yelp_user_duckdb_path(db_options)
    explicit_uri = (os.getenv("YELP_USER_DUCKDB_URI") or os.getenv("DUCKDB_YELP_URI") or "").strip()
    md_token = os.getenv("MOTHERDUCK_TOKEN", "").strip()
    review_fqn = (os.getenv("YELP_DUCKDB_REVIEW_FQN") or "review").strip()
    con: Any = None
    from_review = "review"
    try:
        mc = MongoClient(uri, serverSelectionTimeoutMS=8000)
        cur = mc["yelp_db"]["business"].find(mongo_filter, {"business_id": 1})
        refs: list[str] = []
        for doc in cur:
            ref = business_id_to_review_ref(doc.get("business_id", ""))
            if ref:
                refs.append(ref)
        refs = list(dict.fromkeys(refs))
        if not refs:
            return {
                "businesses_matched": 0,
                "review_refs": [],
                "message": (
                    "No businesses matched this location filter (or business_id could not map to review.business_ref). "
                    "The DAB Yelp Mongo collection is a small subset (~100 businesses) and often does not include "
                    "every city (e.g. Los Angeles may be absent). Descriptions use forms like 'City, ST'. "
                    "For a smoke test, try a city present in your loaded data (e.g. Philadelphia, PA or Indianapolis, IN)."
                ),
            }
        placeholders = ",".join(["?"] * len(refs))
        if explicit_uri:
            con = duckdb.connect(explicit_uri)
            from_review = review_fqn
        elif md_token and duck_path and duck_path.exists():
            try:
                con = duckdb.connect(f"md:?motherduck_token={md_token}")
                esc = str(duck_path.resolve()).replace("'", "''")
                con.execute(f"ATTACH '{esc}' AS yelp_dab (TYPE DUCKDB)")
                from_review = "yelp_dab.review"
            except Exception:  # noqa: BLE001
                con = duckdb.connect(str(duck_path), read_only=True)
                from_review = "review"
        elif duck_path and duck_path.exists():
            con = duckdb.connect(str(duck_path), read_only=True)
            from_review = "review"
        else:
            return {
                "error": (
                    "Yelp DuckDB not reachable: set query_yelp yelp_user.db path, or YELP_USER_DUCKDB_URI, "
                    "or MOTHERDUCK_TOKEN to ATTACH the local file."
                ),
            }

        if yelp_metrics_mode == YELP_METRICS_RANK:
            order_kw = "DESC" if order_desc else "ASC"
            sql = (
                f"SELECT business_ref, CAST(AVG(rating) AS DOUBLE) AS avg_rating, "
                f"COUNT(*)::BIGINT AS review_count FROM {from_review} "
                f"WHERE business_ref IN ({placeholders}) GROUP BY business_ref "
                f"ORDER BY avg_rating {order_kw} LIMIT ?"
            )
            rows = con.execute(sql, [*refs, rlim]).fetchall()
            bids: list[str] = []
            ranking: list[dict[str, Any]] = []
            for br, avgr, cnt in rows:
                bid = review_ref_to_business_id(str(br))
                if not bid:
                    continue
                bids.append(bid)
                ranking.append(
                    {
                        "business_id": bid,
                        "business_ref": str(br),
                        "avg_rating": float(avgr) if avgr is not None else None,
                        "review_count": int(cnt),
                        "name": "",
                    }
                )
            if bids:
                for doc in mc["yelp_db"]["business"].find(
                    {"business_id": {"$in": bids}},
                    {"business_id": 1, "name": 1},
                ):
                    bid = doc.get("business_id")
                    nm = doc.get("name") or ""
                    for row in ranking:
                        if row["business_id"] == bid:
                            row["name"] = nm
            return {
                "yelp_metrics_mode": YELP_METRICS_RANK,
                "businesses_in_filter": len(refs),
                "duckdb_sql_template": sql,
                "duckdb_params": [*refs, rlim],
                "duckdb_from": from_review,
                "ranking": ranking,
            }

        select_expr = YELP_DUCK_AGG[duckdb_aggregation]
        sql = f"SELECT {select_expr} FROM {from_review} WHERE business_ref IN ({placeholders})"
        row = con.execute(sql, refs).fetchone()
        value = row[0] if row else None
        out_val: Any = value
        if isinstance(value, (int, float)) and value is not None:
            out_val = float(value) if duckdb_aggregation == "avg_rating" else value
        return {
            "yelp_metrics_mode": YELP_METRICS_SCALAR,
            "businesses_matched": len(refs),
            "review_business_refs_sample": refs[:15],
            "duckdb_sql_template": sql,
            "duckdb_params": refs,
            "duckdb_from": from_review,
            "aggregation": duckdb_aggregation,
            "value": out_val,
        }
    except PyMongoError as exc:
        return {"error": f"MongoDB error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:  # noqa: BLE001
                pass


def list_toolbox_tools() -> list[str]:
    try:
        parsed = yaml.safe_load(TOOLS_FILE.read_text(encoding="utf-8")) or {}
        tools = parsed.get("tools", {})
        if isinstance(tools, dict):
            return sorted(tools.keys())
        return []
    except Exception:  # noqa: BLE001
        return []


def list_toolbox_tools_detail() -> list[dict[str, str]]:
    try:
        parsed = yaml.safe_load(TOOLS_FILE.read_text(encoding="utf-8")) or {}
        tools = parsed.get("tools", {})
        out: list[dict[str, str]] = []
        if isinstance(tools, dict):
            for name, spec in sorted(tools.items()):
                if isinstance(spec, dict):
                    out.append(
                        {
                            "name": name,
                            "kind": str(spec.get("kind", "")),
                            "source": str(spec.get("source", "")),
                        }
                    )
        return out
    except Exception:  # noqa: BLE001
        return []


def app_runtime_capabilities() -> dict[str, Any]:
    return {
        "executors": [
            {
                "name": "yelp-analytics",
                "description": (
                    "Orchestrates Mongo yelp_db.business + DuckDB review (not a Toolbox YAML tool)."
                ),
            },
            {
                "name": "mongo-local",
                "description": (
                    "Read-only aggregate() on any DAB Mongo database from discover_mongo_dataset_catalog "
                    "(live MONGO_URI; dumps referenced by dump_folder for file-based restores)."
                ),
            },
            {
                "name": "sqlite-local-query",
                "description": "SQL against discovered SQLite files from DAB db_config.yaml.",
            },
            {
                "name": "duckdb-local-query",
                "description": "SQL against discovered DuckDB files from DAB db_config.yaml.",
            },
        ],
        "note": (
            "The Toolbox server only exposes tools defined in tools.yaml (sources + tools). "
            "Other DAB datasets appear here as file-backed DBs until you add matching sources in tools.yaml. "
            "Yelp review metrics: optional YELP_USER_DUCKDB_URI or MOTHERDUCK_TOKEN (+ local file ATTACH) — same data as MotherDuck MCP, not a second query path in this Flask app."
        ),
    }


def discover_file_native_sources() -> dict[str, dict[str, str]]:
    discovered: dict[str, dict[str, str]] = {}
    for config_path in sorted(DAB_ROOT.glob("query_*/db_config.yaml")):
        dataset = config_path.parent.name
        parsed = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        db_clients = parsed.get("db_clients", {})
        if not isinstance(db_clients, dict):
            continue
        for client_name, client in db_clients.items():
            if not isinstance(client, dict):
                continue
            db_type = client.get("db_type")
            if db_type not in {"sqlite", "duckdb"}:
                continue
            rel_path = client.get("db_path")
            if not rel_path:
                continue
            resolved = config_path.parent / rel_path
            key = f"{dataset}:{client_name}"
            discovered[key] = {
                "dataset": dataset,
                "client_name": client_name,
                "db_type": db_type,
                "path": str(resolved),
                "label": f"{dataset} / {client_name} ({db_type})",
            }
    return discovered


def introspect_sqlite_tables(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.exists():
        return out
    try:
        uri = f"file:{path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            for (tname,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall():
                cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{tname}")').fetchall()]
                out.append({"table": tname, "columns": cols})
    except Exception:  # noqa: BLE001
        pass
    return out


_SQLITE_SCHEMA_CACHE: dict[str, tuple[tuple[int, int], list[dict[str, Any]]]] = {}
_DUCKDB_SCHEMA_CACHE: dict[str, tuple[tuple[int, int], list[dict[str, Any]]]] = {}


def live_schema_sqlite_cached(path: Path) -> list[dict[str, Any]]:
    key = str(path.resolve())
    try:
        st = path.stat()
        sig = (st.st_mtime_ns, st.st_size)
    except OSError:
        return []
    hit = _SQLITE_SCHEMA_CACHE.get(key)
    if hit and hit[0] == sig:
        return hit[1]
    val = introspect_sqlite_tables(path)
    _SQLITE_SCHEMA_CACHE[key] = (sig, val)
    return val


def introspect_duckdb_tables(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.exists():
        return out
    try:
        with duckdb.connect(str(path), read_only=True) as con:
            for (tname,) in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall():
                cols = [
                    r[0]
                    for r in con.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema = 'main' AND table_name = ? ORDER BY ordinal_position",
                        [tname],
                    ).fetchall()
                ]
                out.append({"table": tname, "columns": cols})
    except Exception:  # noqa: BLE001
        pass
    return out


def live_schema_duckdb_cached(path: Path) -> list[dict[str, Any]]:
    key = str(path.resolve())
    try:
        st = path.stat()
        sig = (st.st_mtime_ns, st.st_size)
    except OSError:
        return []
    hit = _DUCKDB_SCHEMA_CACHE.get(key)
    if hit and hit[0] == sig:
        return hit[1]
    val = introspect_duckdb_tables(path)
    _DUCKDB_SCHEMA_CACHE[key] = (sig, val)
    return val


def discover_mongo_dataset_catalog() -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for config_path in sorted(DAB_ROOT.glob("query_*/db_config.yaml")):
        dataset_dir = config_path.parent
        hint = dataset_dir / "db_description_withhint.txt"
        base = dataset_dir / "db_description.txt"
        excerpt = ""
        desc_full = ""
        try:
            if base.exists():
                desc_full = base.read_text(encoding="utf-8")
            if hint.exists():
                excerpt = hint.read_text(encoding="utf-8")[:4500]
            elif desc_full:
                excerpt = desc_full[:4500]
        except Exception:  # noqa: BLE001
            excerpt = ""
            desc_full = ""
        parsed = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        clients = parsed.get("db_clients") or {}
        if not isinstance(clients, dict):
            continue
        for client_name, client in clients.items():
            if not isinstance(client, dict):
                continue
            if str(client.get("db_type", "")).lower() not in ("mongo", "mongodb"):
                continue
            cols = extract_mongo_collections_from_description(desc_full, str(client_name))
            dump_folder = str(client.get("dump_folder") or "").strip()
            catalog.append(
                {
                    "key": f"{dataset_dir.name}:{client_name}",
                    "label": f"{dataset_dir.name} / {client_name} (mongodb)",
                    "dataset": dataset_dir.name,
                    "db_name": client.get("db_name", ""),
                    "collections": cols,
                    "dump_folder": dump_folder,
                    "description_excerpt": excerpt,
                    "storage": (
                        "Data is served from the live MongoDB instance (MONGO_URI). "
                        f"Optional BSON dump under dataset {dump_folder!r} for offline/file-backed restores."
                        if dump_folder
                        else "Data is served from the live MongoDB instance (MONGO_URI)."
                    ),
                }
            )
    return catalog


def mongo_pipeline_needs_result_cap(pipeline: list[Any]) -> bool:
    for st in pipeline:
        if isinstance(st, dict) and "$limit" in st:
            return False
    return True


def run_mongo_aggregate_readonly(
    database: str,
    collection: str,
    pipeline: list[Any],
) -> Any:
    if not isinstance(pipeline, list):
        return {"error": "mongo_pipeline must be a JSON array."}
    err = validate_mongo_pipeline(pipeline)
    if err:
        return {"error": err}
    pl = list(pipeline)
    if mongo_pipeline_needs_result_cap(pl):
        pl.append({"$limit": MONGO_AGG_RESULT_CAP})
    apply_env_files()
    uri = os.getenv("MONGO_URI")
    if not uri:
        return {"error": "MONGO_URI is not set."}
    try:
        mc = MongoClient(uri, serverSelectionTimeoutMS=15000)
        cur = mc[database][collection].aggregate(pl, allowDiskUse=True)
        docs = list(cur)
        return json.loads(json_util.dumps(docs))
    except PyMongoError as exc:
        return {"error": f"MongoDB error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def choose_file_db(text: str, db_type: str, options: dict[str, dict[str, str]]) -> dict[str, str] | None:
    lower = text.lower()
    candidates = [v for v in options.values() if v["db_type"] == db_type]
    # Match by dataset token first.
    for item in candidates:
        dataset = item["dataset"].lower()
        dataset_alias = dataset.replace("query_", "")
        if dataset in lower or dataset_alias in lower:
            return item
    # CRM/BANT lead qualification questions usually target query_crmarenapro.
    if db_type in {"sqlite", "duckdb"} and _has_any_intent_term(
        lower, ("lead", "bant", "qualified", "qualification", "opportunity", "salesforce")
    ):
        crm_pool = [x for x in candidates if "crmarenapro" in x.get("dataset", "").lower()]
        if crm_pool:
            if db_type == "sqlite":
                pref = sorted(
                    (x for x in crm_pool if x.get("client_name") == "core_crm"),
                    key=lambda x: x.get("path", ""),
                )
                if pref:
                    return pref[0]
            return sorted(crm_pool, key=lambda x: x.get("path", ""))[0]
    # Fallbacks by obvious domain terms.
    if db_type == "duckdb":
        if heuristic_equity_stock_question(lower):
            by_hint = find_duckdb_dataset_by_hint(options, "stockmarket") or find_duckdb_dataset_by_hint(
                options, "stocktrade"
            )
            if by_hint:
                return by_hint
        for token in ("stock", "yelp", "music", "crm", "sales"):
            for item in candidates:
                if token in lower and token in item["dataset"].lower():
                    return item
    if db_type == "sqlite":
        for token in (
            "agnews",
            "news",
            "article",
            "metadata",
            "patent",
            "googlelocal",
            "review",
            "book",
            "crm",
            "lead",
            "bant",
            "salesforce",
        ):
            for item in candidates:
                if token in lower and token in item["dataset"].lower():
                    return item
    return None


def _has_any_intent_term(lower: str, terms: tuple[str, ...]) -> bool:
    """
    Word-aware term matching to avoid false positives from raw substrings
    (e.g., 'authority' accidentally matching token 'author').
    """
    for term in terms:
        t = term.strip().lower()
        if not t:
            continue
        if " " in t:
            if t in lower:
                return True
            continue
        if re.search(rf"\b{re.escape(t)}\b", lower):
            return True
    return False


def find_duckdb_dataset_by_hint(options: dict[str, dict[str, str]], *needles: str) -> dict[str, str] | None:
    """Pick a discovered DuckDB file when path/dataset contains every hint (e.g. stockmarket)."""
    n = tuple(x.lower() for x in needles)
    for item in options.values():
        if item.get("db_type") != "duckdb":
            continue
        blob = f"{item.get('path', '')} {item.get('dataset', '')} {item.get('label', '')}".lower()
        if all(part in blob for part in n):
            return item
    return None


def heuristic_equity_stock_question(lower: str) -> bool:
    """Signals [DataAgentBench](https://ucbepic.github.io/DataAgentBench/) equity / OHLC workloads (DuckDB)."""
    if any(
        ph in lower
        for ph in (
            "adj close",
            "adjusted close",
            "adjusted closing",
            "adjusted closing price",
            "closing price",
            "open price",
            "stock price",
            "share price",
            "after hours",
            "pre-market",
            "ticker",
            "stock split",
            "dividend",
            "nasdaq",
            "nyse",
            "s&p",
            "ohlc",
            "candlestick",
        )
    ):
        return True
    if "price" in lower and any(s in lower for s in ("inc.", "ltd", "corp.", "plc", "holdings", "company")):
        return True
    if "stock" in lower and "book" not in lower:
        return True
    return False


def extract_year_from_question(text: str) -> str | None:
    m = re.search(r"\b((?:19|20)\d{2})\b", text)
    return m.group(1) if m else None


def infer_equity_ticker_symbol(text: str) -> str | None:
    """Lightweight name→ticker hints for DAB stocktrade tables (one table per symbol). Extend as needed."""
    compact = re.sub(r"[^a-z0-9]+", "", text.lower())
    # Longer keys first to avoid substring collisions.
    hints: list[tuple[str, str]] = [
        ("therealreal", "REAL"),
        ("realreal", "REAL"),
    ]
    for needle, sym in hints:
        if needle in compact:
            return sym
    return None


def nl_to_sql_duckdb_equity(text: str) -> str:
    """Template SQL for stocktrade DuckDB; strftime/VARCHAR handling is normalized in run_duckdb."""
    lower = text.lower()
    year = extract_year_from_question(text) or "2020"
    sym = infer_equity_ticker_symbol(text)
    if not sym:
        return (
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' "
            "ORDER BY table_name LIMIT 300;"
        )
    want_min = any(w in lower for w in ("minimum", "lowest", "min "))
    want_max = any(w in lower for w in ("maximum", "highest", "max "))
    agg = "MAX"
    if want_min and not want_max:
        agg = "MIN"
    elif want_max and not want_min:
        agg = "MAX"
    col = '"Adj Close"'
    if "adjusted" not in lower and "adj" not in lower and "closing" in lower:
        col = '"Close"'
    return (
        f'SELECT {agg}({col}) FROM "{sym}" '
        f"WHERE strftime('%Y', \"Date\") = '{year}'"
    )


def _tokens_for_dab_overlap(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z][a-z0-9]{2,}", text.lower())
        if t not in DAB_ROUTE_STOPWORDS
    }


def dab_dataset_overlap_scores(question: str) -> list[tuple[str, int]]:
    """Score each query_* folder by word overlap with question vs db_description (+ hint)."""
    qtok = _tokens_for_dab_overlap(question)
    if len(qtok) < 2:
        return []
    scores: list[tuple[str, int]] = []
    for desc_path in sorted(DAB_ROOT.glob("query_*/db_description.txt")):
        parts: list[str] = []
        hint = desc_path.parent / "db_description_withhint.txt"
        try:
            if hint.exists():
                parts.append(hint.read_text(encoding="utf-8")[:12000])
        except OSError:
            pass
        try:
            parts.append(desc_path.read_text(encoding="utf-8")[:12000])
        except OSError:
            continue
        blob = "\n".join(parts)
        dtok = _tokens_for_dab_overlap(blob)
        inter = len(qtok & dtok)
        if inter > 0:
            scores.append((desc_path.parent.name, inter))
    scores.sort(key=lambda x: -x[1])
    return scores


def pick_local_db_entry_for_dataset(
    db_options: dict[str, dict[str, str]], dataset_name: str
) -> dict[str, str] | None:
    pool = [v for v in db_options.values() if v.get("dataset") == dataset_name]
    if not pool:
        return None
    duck = [x for x in pool if x.get("db_type") == "duckdb"]
    sql = [x for x in pool if x.get("db_type") == "sqlite"]
    if duck:
        return sorted(duck, key=lambda x: x.get("path", ""))[0]
    if sql:
        return sorted(sql, key=lambda x: x.get("path", ""))[0]
    return None


def fallback_plan_dab_description_overlap(
    user_input: str,
    db_options: dict[str, dict[str, str]],
    *,
    sql_like: bool,
) -> dict[str, Any] | None:
    """When keywords and LLM miss, align the question to a DAB dataset via description token overlap (no per-query hardcoding)."""
    ranked = dab_dataset_overlap_scores(user_input)
    if not ranked:
        return None
    top_name, top_s = ranked[0]
    second_s = ranked[1][1] if len(ranked) > 1 else 0
    if top_s < 2:
        return None
    if second_s == top_s:
        return None
    entry = pick_local_db_entry_for_dataset(db_options, top_name)
    if not entry:
        return None
    eng = entry["db_type"]
    if eng == "duckdb":
        q = user_input if sql_like else nl_to_sql("duckdb", user_input)
        return {
            "route": {
                "executor": "duckdb-local",
                "tool": "duckdb-local-query",
                "database": entry["path"],
                "dataset_db": entry["label"],
                "reason": (
                    f"Routed by DAB db_description overlap ({top_s} tokens) to {top_name}; "
                    "refine SQL or set OPENROUTER_API_KEY for planner-generated queries."
                ),
            },
            "query": q,
        }
    q = user_input if sql_like else nl_to_sql("sqlite", user_input)
    return {
        "route": {
            "executor": "sqlite-local",
            "tool": "sqlite-local-query",
            "database": entry["path"],
            "dataset_db": entry["label"],
            "reason": (
                f"Routed by DAB db_description overlap ({top_s} tokens) to {top_name}; "
                "refine SQL or set OPENROUTER_API_KEY for planner-generated queries."
            ),
        },
        "query": q,
    }


def extract_json_object(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
    try:
        out = json.loads(raw)
        return out if isinstance(out, dict) else None
    except Exception:  # noqa: BLE001
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            out = json.loads(raw[start : end + 1])
            return out if isinstance(out, dict) else None
        except Exception:  # noqa: BLE001
            return None
    return None


def normalize_executor(name: str) -> str:
    n = (name or "").strip().lower().replace("_", "-")
    aliases = {
        "yelpanalytics": "yelp-analytics",
        "duckdblocal": "duckdb-local",
        "sqlitelocal": "sqlite-local",
        "mongolocal": "mongo-local",
        "toolboxchain": "toolbox-chain",
    }
    return aliases.get(n.replace("-", ""), n)


def validate_toolbox_chain_steps(raw: Any) -> list[dict[str, str]] | None:
    if not isinstance(raw, list) or not raw:
        return None
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        tool = str(item.get("tool", "")).strip()
        q = item.get("query")
        if tool not in TOOLBOX_SQL_TOOL_NAMES or not isinstance(q, str) or not q.strip():
            return None
        if tool.startswith("mongo-yelp"):
            return None
        out.append({"tool": tool, "query": q.strip()})
    return out


AGG_ALIASES = {
    "average_rating": "avg_rating",
    "mean_rating": "avg_rating",
    "avg": "avg_rating",
    "count": "count_reviews",
    "total_reviews": "count_reviews",
}


def normalize_duckdb_aggregation(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip().lower().replace("-", "_")
    s = AGG_ALIASES.get(s, s)
    return s if s in YELP_DUCK_AGG else None


def normalize_yelp_metrics_mode(val: Any) -> str:
    if val is None:
        return YELP_METRICS_SCALAR
    s = str(val).strip().lower().replace("-", "_")
    aliases = {
        "scalar": YELP_METRICS_SCALAR,
        "scalaraggregate": YELP_METRICS_SCALAR,
        "rank": YELP_METRICS_RANK,
        "rankbusinessesbyavgrating": YELP_METRICS_RANK,
        "topbusinesses": YELP_METRICS_RANK,
    }
    key = re.sub(r"[^a-z]", "", s)
    return aliases.get(key, s if s in {YELP_METRICS_SCALAR, YELP_METRICS_RANK} else YELP_METRICS_SCALAR)


def infer_yelp_metrics_mode_and_limit(lower: str) -> tuple[str, int]:
    """Distinguish scalar (one number) vs per-business ranking; limit from top N."""
    mtop = re.search(r"\btop\s+(\d+)\b", lower)
    ranked = any(w in lower for w in ("ranked", "ranking", "order by"))
    per_business = any(w in lower for w in ("per business", "each business", "per-business"))
    if mtop or ranked or (per_business and "average" in lower):
        lim = int(mtop.group(1)) if mtop else 5
        return YELP_METRICS_RANK, max(1, min(50, lim))
    return YELP_METRICS_SCALAR, 5


def heuristic_yelp_cross_plan(user_input: str) -> dict[str, Any] | None:
    """Deterministic yelp-analytics plan when the LLM output is missing or unparsable."""
    lower = user_input.lower()
    if not yelp_cross_db_question(lower):
        return None
    loc = extract_city_state_from_question(user_input)
    if loc is None:
        return None
    city, state = loc
    mf = mongo_filter_for_city_state(city, state)
    if mf is None:
        return None
    err = validate_mongo_filter(mf)
    if err:
        return None
    mode, rlim = infer_yelp_metrics_mode_and_limit(lower)
    out: dict[str, Any] = {
        "route": {
            "executor": "yelp-analytics",
            "tool": "yelp-mongo-duckdb",
            "database": "yelp_db.business + Yelp DuckDB review",
            "dataset_db": "",
            "reason": (
                "Heuristic cross-database plan (city/state parsed from the question; "
                "use when the LLM response was empty or not valid JSON)."
            ),
        },
        "query": None,
        "mongo_filter": mf,
        "yelp_metrics_mode": mode,
        "yelp_rank_limit": rlim,
        "order_desc": True,
    }
    if mode == YELP_METRICS_SCALAR:
        out["duckdb_aggregation"] = "avg_rating"
    else:
        out.setdefault("order_desc", True)
    out["mongo_filter_source"] = "structured_city_state"
    return out


def apply_structured_yelp_location_filter(user_input: str, plan: dict[str, Any]) -> None:
    """
    If the question contains a parsable 'City, State', replace mongo_filter with canonical
    description clauses (city + ST or full state). Matches how addresses appear ('Indianapolis, IN'),
    avoiding brittle single-string LLM regex like 'Los Angeles, California'.
    """
    if plan.get("route", {}).get("executor") != "yelp-analytics":
        return
    loc = extract_city_state_from_question(user_input)
    if not loc:
        plan.setdefault("mongo_filter_source", "llm")
        return
    city, state = loc
    mf = mongo_filter_for_city_state(city, state)
    if not mf:
        return
    err = validate_mongo_filter(mf)
    if err:
        return
    plan["mongo_filter"] = mf
    plan["mongo_filter_source"] = "structured_city_state"


def compact_route_candidates_for_llm(candidates: dict[str, Any]) -> dict[str, Any]:
    """Smaller payload for the router LLM; execution still uses full introspection on disk."""
    out = json.loads(json.dumps(candidates))

    def trim_sqlite_duck(opts_key: str) -> None:
        for opt in out.get(opts_key) or []:
            ls = opt.get("live_schema")
            if not isinstance(ls, list):
                continue
            max_tables = 48
            cap = ls if len(ls) <= max_tables else ls[:max_tables]
            trimmed: list[dict[str, Any]] = []
            for ent in cap:
                if not isinstance(ent, dict):
                    continue
                cols = ent.get("columns")
                cols_list = cols if isinstance(cols, list) else []
                trimmed.append(
                    {
                        "table": ent.get("table", ""),
                        "columns": cols_list[:24],
                    }
                )
            opt["live_schema"] = trimmed
            if len(ls) > max_tables:
                opt["live_schema_router_note"] = (
                    f"Router context lists {max_tables} of {len(ls)} tables; full file has more. "
                    "Use SHOW TABLES or information_schema when planning SQL for this file."
                )

    trim_sqlite_duck("sqlite_local_options")
    trim_sqlite_duck("duckdb_local_options")
    yelp_cross = out.get("yelp_cross_database")
    if isinstance(yelp_cross, dict):
        hint = yelp_cross.get("duckdb_path_hint")
        if isinstance(hint, dict):
            hint = dict(hint)
            ls = hint.get("live_schema")
            if isinstance(ls, list):
                hint["live_schema"] = [
                    {
                        "table": x.get("table", ""),
                        "columns": (x.get("columns") if isinstance(x.get("columns"), list) else [])[:24],
                    }
                    for x in ls
                    if isinstance(x, dict)
                ]
            yelp_cross["duckdb_path_hint"] = hint
    return out


def build_route_candidates(db_options: dict[str, dict[str, str]]) -> dict[str, Any]:
    sqlite_dbs = []
    duckdb_dbs = []
    for key, info in db_options.items():
        p = Path(info["path"])
        entry: dict[str, Any] = {"key": key, "label": info["label"], "path": info["path"]}
        if info["db_type"] == "sqlite":
            entry["live_schema"] = live_schema_sqlite_cached(p)
            sqlite_dbs.append(entry)
        elif info["db_type"] == "duckdb":
            entry["live_schema"] = live_schema_duckdb_cached(p)
            duckdb_dbs.append(entry)
    yelp_duck = next((e for e in duckdb_dbs if "query_yelp" in e.get("path", "")), None)
    mongo_datasets = discover_mongo_dataset_catalog()
    return {
        "toolbox_tools": [
            {"tool": "postgres-bookreview", "database": "bookreview_db"},
            {"tool": "sqlite-bookreview", "database": "bookreview sqlite source"},
            {"tool": "mongo-yelp-business", "database": "yelp_db.business (find)"},
            {"tool": "mongo-yelp-aggregate", "database": "yelp_db.business (aggregate)"},
        ],
        "yelp_cross_database": {
            "executor": "yelp-analytics",
            "when": (
                "Question needs Yelp business rows from Mongo (business collection) combined with "
                "review.rating or other metrics in DuckDB (query_yelp user_database / yelp_user.db)."
            ),
            "mongo_fields": (
                "business_id like businessid_<N>, name, review_count, description (address/location prose), "
                "attributes, hours, is_open — no star rating on this collection."
            ),
            "duckdb_review": "review table: business_ref like businessref_<N>, rating (1-5), text, ...",
            "id_rule": "Suffix N matches: Mongo businessid_N <-> DuckDB businessref_N.",
            "duckdb_aggregation_values": list(YELP_DUCK_AGG.keys()),
            "yelp_metrics_modes": [
                YELP_METRICS_SCALAR + " — one aggregate number over all matching businesses' reviews",
                YELP_METRICS_RANK
                + " — GROUP BY business_ref, AVG(rating), ORDER BY avg DESC, LIMIT k; then join names from Mongo",
            ],
            "duckdb_path_hint": yelp_duck,
        },
        "mongo_datasets": mongo_datasets,
        "routing_note": (
            "Use candidates.mongo_datasets for Mongo-backed DAB workloads: each entry lists db_name, collections "
            "(parsed from db_description.txt), and storage notes (live URI vs dump_folder). "
            "Example: AG News article text is Mongo articles_db.articles; companion SQLite metadata.db only has "
            "authors + article_metadata (no article body). "
            "For sqlite_local_options / duckdb_local_options use only table names from live_schema; never invent names."
        ),
        "sqlite_local_options": sqlite_dbs,
        "duckdb_local_options": duckdb_dbs,
    }


def llm_synthesize_toolbox_chain_answer(
    user_question: str,
    step_results: list[dict[str, Any]],
    kb_session_context: str,
) -> dict[str, Any]:
    api_key = openrouter_api_key()
    if not api_key:
        return {"error": "OPENROUTER_API_KEY required for cross-step synthesis", "step_results": step_results}
    try:
        payload = json.dumps(step_results, ensure_ascii=True, default=str)
        max_ch = int(os.getenv("TOOLBOX_CHAIN_SYNTH_MAX_CHARS", "180000"))
        if len(payload) > max_ch:
            payload = payload[:max_ch] + "\n...[truncated for synthesis context]"
        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        sys = (
            "You are a data analyst. The KB context below was loaded from the repo knowledge base for this request "
            "(architecture, domain, corrections, join glossary). Use it to interpret keys and merge multi-database "
            "results per DataAgentBench-style rules. Answer from the data and KB only — do not invent facts. "
            "State the final answer first."
        )
        user_msg = (
            f"User question:\n{user_question}\n\n--- KB (this session, from disk) ---\n"
            f"{kb_session_context or '[KB unavailable]'}\n\n"
            f"--- Query results (JSON per toolbox step) ---\n{payload}"
        )
        r = client.chat.completions.create(
            model=OPENROUTER_SYNTH_MODEL,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user_msg}],
            temperature=0,
        )
        text = (r.choices[0].message.content or "").strip()
        return {
            "answer": text,
            "step_results": step_results,
            "synthesis_model": OPENROUTER_SYNTH_MODEL,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "step_results": step_results}


def execute_toolbox_chain_and_synthesize(user_question: str, plan: dict[str, Any]) -> Any:
    from agent.context_loader import build_agent_session_kb_context

    steps_in = plan.get("steps")
    if not isinstance(steps_in, list):
        return {"error": "Plan missing steps"}
    raw: list[dict[str, Any]] = []
    for s in steps_in:
        if not isinstance(s, dict):
            return {"error": "Invalid step"}
        tool = str(s.get("tool", ""))
        q = str(s.get("query", ""))
        raw.append({"tool": tool, "query": q, "result": run_toolbox(tool, {"query": q})})
    kb = build_agent_session_kb_context(user_question, ROOT)
    return llm_synthesize_toolbox_chain_answer(user_question, raw, kb)


def llm_build_plan(user_input: str, db_options: dict[str, dict[str, str]]) -> dict[str, Any] | None:
    api_key = openrouter_api_key()
    if not api_key:
        return None
    try:
        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        candidates_full = build_route_candidates(db_options)
        candidates = compact_route_candidates_for_llm(candidates_full)
        try:
            from agent.context_loader import build_router_planner_user_payload

            user_payload = build_router_planner_user_payload(
                user_input,
                candidates,
                repo_root=ROOT,
                max_kb_layer_chars=9000,
            )
        except Exception:  # noqa: BLE001
            user_payload = {"question": user_input, "dab_candidates": candidates, "kb_layers": {}}
        system_prompt = (
            "You are a data-agent planner for DataAgentBench-style workloads (see user message challenge_alignment). "
            "The user JSON includes dab_candidates (runtime paths/schemas) and kb_layers loaded from kb/ on disk: "
            "architecture (kb/architecture), domain (kb/domain including schemas and join glossary), corrections (kb/corrections). "
            "If kb_focus.join_key_glossary_dataset_section is present, treat it as the authoritative join-key row for "
            "dataset_hint_for_kb — use it with kb_layers.domain before choosing tools. "
            "Do not assume all tables live in one database; follow kb_layers for multi-DB splits. "
            "When the KB indicates multiple engines are required, use executor toolbox-chain with steps: an array of "
            "{{tool, query}} with one read-only SQL per step (tools from candidates.toolbox_tools only). "
            "Derive filters, projections, and joins from kb_layers and dab_candidates — do not embed task-specific answers. "
            "Return ONLY valid JSON (no markdown fences).\n"
            "Always include keys: executor, tool, database, dataset_db, reason, query.\n"
            "executor ∈ toolbox | toolbox-chain | sqlite-local | duckdb-local | yelp-analytics | mongo-local.\n"
            "toolbox-chain: set tool to toolbox-chain, query to null, and include steps: a JSON array of "
            "{{tool, query}} objects where each tool is from candidates.toolbox_tools and each query is read-only SQL for that engine.\n"
            "tool: exact toolbox name from candidates.toolbox_tools when executor=toolbox; "
            "toolbox-chain when executor=toolbox-chain; "
            "sqlite-local-query | duckdb-local-query for file SQL executors; yelp-mongo-duckdb when executor=yelp-analytics; "
            "mongo-local-aggregate when executor=mongo-local.\n"
            "database: human label for toolbox/yelp-analytics/mongo-local (e.g. articles_db). "
            "For sqlite-local / duckdb-local set database to the chosen path string from "
            "candidates.sqlite_local_options or duckdb_local_options.\n"
            "dataset_db: label field from candidates for file DBs, else empty string.\n"
            "query: SQL for sqlite-local | duckdb-local | toolbox SQL tools when executor=toolbox; null when executor=toolbox-chain.\n"
            "mongo-local: set mongo_database and mongo_collection from candidates.mongo_datasets (use db_name and a "
            "collection from collections[]). Include mongo_pipeline as a JSON array of aggregation stages "
            "(same allowed ops as mongo-yelp-aggregate). For AG News–style questions about article title/description, "
            "use articles_db + articles — not SQLite bookreview. SQLite metadata.db only has authors/article_metadata.\n"
            "AG News categories (World/Sports/Business/Science) are not stored as a column: infer with $match on "
            "title/description using careful regex (word boundaries; avoid bare 'sport' matching idioms like "
            "'sport of'). Prefer league/team/game terms when the user says Sports.\n"
            "mongo-yelp-business: include filterJson as a STRING containing JSON object for find(). "
            "Use $regex on description for city/region text.\n"
            "mongo-yelp-aggregate: include pipelineJson as STRING JSON array; stages must be read-only "
            "($match,$project,$group,$sort,$limit,$skip,$count,$addFields,$replaceRoot,$unwind).\n"
            "yelp-analytics: include mongo_filter as JSON object (NOT a string); the server may replace it "
            "with a canonical City+State filter when the user names a US location in the question. "
            "Set yelp_metrics_mode: scalar_aggregate | rank_businesses_by_avg_rating. "
            "For scalar_aggregate set duckdb_aggregation from candidates.duckdb_aggregation_values. "
            "For rank_businesses_by_avg_rating set yelp_rank_limit (1-50) and order_desc (boolean, default true); "
            "omit duckdb_aggregation or set null.\n"
            "Facts: Mongo yelp_db.business has business_id like businessid_<N>, description with address text, "
            "no star field. DuckDB review has business_ref businessref_<N> and rating; same N links records.\n"
            "Use rank_businesses_by_avg_rating for top-K businesses by per-business average rating in a region.\n"
            "Use scalar_aggregate for a single overall average (or other scalar) over reviews for filtered businesses.\n"
            "Use mongo-yelp-business to list business documents without DuckDB metrics.\n"
            "For sqlite-local / duckdb-local: only reference tables present in that option's live_schema.\n"
            "DuckDB SQL is NOT SQLite: strftime takes (timestamp_or_date, format), e.g. "
            "strftime(\"Date\", '%Y') = '2020' — not strftime('%Y', \"Date\"). "
            "Alternatives: year(\"Date\"::DATE) = 2020, or EXTRACT(YEAR FROM CAST(\"Date\" AS DATE)).\n"
            "Stock / equity DuckDB benchmarks often use one table per ticker symbol (see live_schema table names); "
            "map company names to the correct ticker table (e.g. The RealReal → REAL), not an arbitrary symbol.\n"
            "SQLite table list query: SELECT name FROM sqlite_master WHERE type = 'table'; "
            "DuckDB: SHOW TABLES;\n"
            "If input is already SQL (SELECT/WITH/SHOW), route to correct engine and copy verbatim to query.\n"
        )
        user_prompt = json.dumps(user_payload, ensure_ascii=True)
        req = dict(
            model=OPENROUTER_ROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        try:
            response = client.chat.completions.create(
                **req,
                response_format={"type": "json_object"},
            )
        except Exception:  # noqa: BLE001
            response = client.chat.completions.create(**req)
        content = response.choices[0].message.content or ""
        parsed = extract_json_object(content)
        if not parsed:
            return None
        ex = normalize_executor(str(parsed.get("executor", "")))
        if ex not in {"toolbox", "toolbox-chain", "sqlite-local", "duckdb-local", "yelp-analytics", "mongo-local"}:
            return None
        route = {
            "executor": ex,
            "tool": parsed.get("tool", ""),
            "database": parsed.get("database", ""),
            "dataset_db": parsed.get("dataset_db", ""),
            "reason": f"{parsed.get('reason', 'LLM plan')} (model: {OPENROUTER_ROUTER_MODEL})",
        }
        out: dict[str, Any] = {"route": route, "query": parsed.get("query")}
        if ex == "toolbox-chain":
            steps = validate_toolbox_chain_steps(parsed.get("steps"))
            if not steps:
                return None
            route["tool"] = "toolbox-chain"
            route["database"] = "multi-toolbox"
            out["steps"] = steps
            out["query"] = None
        elif ex == "mongo-local":
            route["tool"] = "mongo-local-aggregate"
            dbn = (
                str(
                    parsed.get("mongo_database")
                    or parsed.get("mongo_db")
                    or parsed.get("db_name")
                    or ""
                ).strip()
            )
            coll = str(parsed.get("mongo_collection") or parsed.get("collection") or "").strip()
            pl_raw: Any = parsed.get("mongo_pipeline")
            if pl_raw is None:
                pj = parsed.get("pipelineJson")
                if isinstance(pj, list):
                    pl_raw = pj
                elif isinstance(pj, str):
                    try:
                        pl_raw = json.loads(pj)
                    except json.JSONDecodeError:
                        pl_raw = None
            if not dbn or not coll or not isinstance(pl_raw, list):
                return None
            err = validate_mongo_pipeline(pl_raw)
            if err:
                return None
            route["database"] = dbn
            out["mongo_database"] = dbn
            out["mongo_collection"] = coll
            out["mongo_pipeline"] = pl_raw
            out["query"] = None
        elif ex == "yelp-analytics":
            mf = parsed.get("mongo_filter")
            if isinstance(mf, str):
                mf = extract_json_object(mf)
            if not isinstance(mf, dict):
                return None
            err = validate_mongo_filter(mf)
            if err:
                return None
            mode = normalize_yelp_metrics_mode(parsed.get("yelp_metrics_mode", YELP_METRICS_SCALAR))
            out["mongo_filter"] = mf
            out["yelp_metrics_mode"] = mode
            out["order_desc"] = bool(parsed.get("order_desc", True))
            if mode == YELP_METRICS_RANK:
                try:
                    lim = int(parsed.get("yelp_rank_limit", parsed.get("limit", 5)))
                except (TypeError, ValueError):
                    lim = 5
                out["yelp_rank_limit"] = max(1, min(50, lim))
            else:
                da = normalize_duckdb_aggregation(parsed.get("duckdb_aggregation", "avg_rating")) or "avg_rating"
                if da not in YELP_DUCK_AGG:
                    return None
                out["duckdb_aggregation"] = da
        elif ex == "toolbox":
            tool = parsed.get("tool", "")
            if tool == "mongo-yelp-aggregate":
                pj = parsed.get("pipelineJson")
                if isinstance(pj, list):
                    pj = json.dumps(pj)
                if not isinstance(pj, str):
                    return None
                try:
                    pl = json.loads(pj)
                except json.JSONDecodeError:
                    return None
                err = validate_mongo_pipeline(pl)
                if err:
                    return None
                out["pipelineJson"] = pj
            elif tool == "mongo-yelp-business":
                fj = parsed.get("filterJson")
                if fj is None and isinstance(parsed.get("mongo_filter"), dict):
                    fj = json.dumps(parsed["mongo_filter"])
                if fj is None:
                    fj = "{}"
                if isinstance(fj, dict):
                    fj = json.dumps(fj)
                if not isinstance(fj, str):
                    return None
                try:
                    fj_obj = json.loads(fj)
                except json.JSONDecodeError:
                    return None
                err = validate_mongo_filter(fj_obj)
                if err:
                    return None
                out["filterJson"] = fj
        return out
    except Exception:  # noqa: BLE001
        return None


def yelp_cross_db_question(lower: str) -> bool:
    ratingish = any(
        w in lower
        for w in ("rating", "star", "avg", "average", "mean", "rank", "ranked", "top ")
    )
    yelpish = "yelp" in lower or "business" in lower
    if "book" in lower and "yelp" not in lower:
        return False
    return ratingish and yelpish


def plan_execution_error(reason: str) -> dict[str, Any]:
    return {
        "route": {
            "executor": "error",
            "tool": "",
            "database": "",
            "dataset_db": "",
            "reason": reason,
        },
        "query": None,
    }


def build_plan(user_input: str, db_options: dict[str, dict[str, str]]) -> dict[str, Any]:
    lower = user_input.lower()
    sql_like = is_sql_like(user_input)

    # Context-first: KB layers + dab_candidates are assembled inside llm_build_plan (see build_router_planner_user_payload).
    # Heuristics and keyword fallbacks run only if the planner is unavailable or returns nothing.
    api_key = openrouter_api_key()
    if api_key:
        llm_plan = llm_build_plan(user_input, db_options)
        if llm_plan:
            apply_structured_yelp_location_filter(user_input, llm_plan)
            return llm_plan

    if yelp_cross_db_question(lower):
        heur = heuristic_yelp_cross_plan(user_input)
        if heur:
            return heur
        if not api_key:
            return plan_execution_error(
                "Yelp questions that combine business metadata with review ratings need either "
                "OPENROUTER_API_KEY (LLM planner) or a recognizable 'City, State' in the question "
                "for the heuristic path."
            )
        return plan_execution_error(
            "Planner could not produce a JSON plan and the question did not match the "
            "city/state heuristic. Retry or name the city and state explicitly (e.g. City, Indiana)."
        )

    # Postgres route: bookreview books table.
    if any(token in lower for token in ("books_info", "bookreview postgres", "postgres bookreview")):
        query = user_input if sql_like else nl_to_sql("postgres", user_input)
        return {
            "route": {
                "executor": "toolbox",
                "tool": "postgres-bookreview",
                "database": "bookreview_db",
                "reason": "Detected explicit Postgres/bookreview intent.",
            },
            "query": query,
        }

    # Explicit DuckDB route via dataset mention or keywords.
    duckdb_terms = (
        "stock",
        "sales_pipeline",
        "user_database",
        "yelp",
        "trading",
        "equity",
        "ohlc",
        "adjusted close",
        "adjusted closing",
        "closing price",
        "share price",
        "ticker",
        "nasdaq",
        "nyse",
    )
    if re.search(r"\bduckdb\b", lower) or _has_any_intent_term(lower, duckdb_terms) or heuristic_equity_stock_question(lower):
        selected = choose_file_db(user_input, "duckdb", db_options)
        if not selected:
            return plan_execution_error(
                "DuckDB was requested but no db_config.yaml DuckDB file could be inferred. "
                "Name the dataset (e.g. query_yelp) or enable the LLM planner."
            )
        stock_dataset = selected.get("dataset", "").lower()
        stockish = stock_dataset in {"query_stockmarket", "query_stockindex"} and heuristic_equity_stock_question(lower)
        query = user_input if sql_like else (nl_to_sql_duckdb_equity(user_input) if stockish else nl_to_sql("duckdb", user_input))
        return {
            "route": {
                "executor": "duckdb-local",
                "tool": "duckdb-local-query",
                "database": selected["path"],
                "dataset_db": selected["label"],
                "reason": (
                    "Detected DuckDB-oriented query intent with dataset-aware routing from discovered DAB sources."
                ),
            },
            "query": query,
        }

    # Explicit SQLite route via dataset mention or keywords.
    sqlite_terms = (
        "review",
        "metadata",
        "tracks",
        "patent_publication",
        "patent",
        "author",
        "crm",
        "lead",
        "bant",
        "salesforce",
        "package",
        "github",
        "google local",
        "googlelocal",
    )
    if re.search(r"\bsqlite\b", lower) or _has_any_intent_term(lower, sqlite_terms):
        selected = choose_file_db(user_input, "sqlite", db_options)
        if not selected:
            return plan_execution_error(
                "SQLite was requested but no db_config.yaml SQLite file could be inferred. "
                "Name the dataset (e.g. query_agnews) or enable the LLM planner."
            )
        query = user_input if sql_like else nl_to_sql("sqlite", user_input)
        return {
            "route": {
                "executor": "sqlite-local",
                "tool": "sqlite-local-query",
                "database": selected["path"],
                "dataset_db": selected["label"],
                "reason": "Detected SQLite-oriented query intent.",
            },
            "query": query,
        }

    fb = fallback_plan_dab_description_overlap(user_input, db_options, sql_like=sql_like)
    if fb:
        return fb

    return plan_execution_error(
        "No routing signal matched this question (keywords, LLM planner, or DAB description overlap). "
        "Set OPENROUTER_API_KEY for full routing, name a dataset (e.g. query_agnews), or paste SQL. "
        "See https://ucbepic.github.io/DataAgentBench/"
    )


def trace_resolved(plan: dict[str, Any]) -> Any:
    ex = plan.get("route", {}).get("executor")
    if ex == "toolbox-chain":
        return json.dumps({"steps": plan.get("steps")}, indent=2, default=str)
    if ex == "mongo-local":
        return json.dumps(
            {
                "mongo_database": plan.get("mongo_database"),
                "mongo_collection": plan.get("mongo_collection"),
                "mongo_pipeline": plan.get("mongo_pipeline"),
            },
            indent=2,
            default=str,
        )
    if ex == "yelp-analytics":
        payload: dict[str, Any] = {
            "mongo_filter": plan.get("mongo_filter"),
            "mongo_filter_source": plan.get("mongo_filter_source", "unknown"),
            "yelp_metrics_mode": plan.get("yelp_metrics_mode", YELP_METRICS_SCALAR),
        }
        if plan.get("yelp_metrics_mode") == YELP_METRICS_RANK:
            payload["yelp_rank_limit"] = plan.get("yelp_rank_limit", 5)
            payload["order_desc"] = plan.get("order_desc", True)
        else:
            payload["duckdb_aggregation"] = plan.get("duckdb_aggregation", "avg_rating")
        return json.dumps(payload, indent=2, default=str)
    if plan.get("pipelineJson"):
        return plan["pipelineJson"]
    if plan.get("filterJson"):
        return plan["filterJson"]
    return plan.get("query")


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    response: Any = None
    error = ""
    execution_trace: dict[str, Any] | None = None
    user_input = ""
    file_db_options = discover_file_native_sources()

    if request.method == "POST":
        user_input = request.form.get("input", "").strip()
        if not user_input:
            error = "Please enter a question or query."
        else:
            plan = build_plan(user_input, file_db_options)
            execution_trace = dict(plan["route"])
            sql = plan.get("query")
            tool = plan["route"]["tool"]
            executor = plan["route"]["executor"]

            if executor == "error":
                error = plan["route"].get("reason", "Planner error.")
            elif executor == "yelp-analytics":
                if "mongo_filter" not in plan:
                    error = "Planner returned yelp-analytics without mongo_filter."
                else:
                    response = run_yelp_analytics(
                        plan["mongo_filter"],
                        file_db_options,
                        duckdb_aggregation=plan.get("duckdb_aggregation", "avg_rating"),
                        yelp_metrics_mode=plan.get("yelp_metrics_mode", YELP_METRICS_SCALAR),
                        yelp_rank_limit=int(plan.get("yelp_rank_limit", 5) or 5),
                        order_desc=bool(plan.get("order_desc", True)),
                    )
            elif executor == "toolbox-chain":
                response = execute_toolbox_chain_and_synthesize(user_input, plan)
            elif executor == "toolbox":
                payload: dict[str, Any] = {}
                if sql:
                    payload["query"] = sql
                if plan.get("filterJson") is not None:
                    payload["filterJson"] = plan["filterJson"]
                if plan.get("pipelineJson") is not None:
                    payload["pipelineJson"] = plan["pipelineJson"]
                response = run_toolbox(tool, payload)
            elif executor == "mongo-local":
                pl = plan.get("mongo_pipeline")
                dbn = plan.get("mongo_database")
                coll = plan.get("mongo_collection")
                if not isinstance(pl, list) or not dbn or not coll:
                    error = "mongo-local plan missing mongo_database, mongo_collection, or mongo_pipeline."
                else:
                    response = run_mongo_aggregate_readonly(str(dbn), str(coll), pl)
            elif executor == "sqlite-local":
                sch_err = validate_sqlite_plan_schema(plan)
                if sch_err:
                    error = sch_err
                else:
                    db_path = Path(plan["route"]["database"])
                    if not sql:
                        error = "SQLite plan missing query text."
                    else:
                        response = run_sqlite(sql, db_path)
            elif executor == "duckdb-local":
                sch_err = validate_duckdb_plan_schema(plan)
                if sch_err:
                    error = sch_err
                else:
                    db_path = Path(plan["route"]["database"])
                    if not sql:
                        error = "DuckDB plan missing query text."
                    else:
                        response = run_duckdb(sql, db_path)
            else:
                error = "Unsupported execution route."

            if execution_trace is not None:
                execution_trace["resolved_query"] = trace_resolved(plan)
    return render_template(
        "index.html",
        response=response,
        error=error,
        execution_trace=execution_trace,
        user_input=user_input,
        toolbox_tools=list_toolbox_tools(),
        toolbox_tools_detail=list_toolbox_tools_detail(),
        app_capabilities=app_runtime_capabilities(),
        discovered_datasets=sorted(
            (v["label"], v["path"]) for v in file_db_options.values()
        ),
        openrouter_configured=bool(openrouter_api_key()),
    )


if __name__ == "__main__":
    _port = int(os.getenv("PORT", "8080"))
    _host = os.getenv("FLASK_HOST", "0.0.0.0")
    _debug = os.getenv("FLASK_DEBUG", "").strip().lower() in ("1", "true", "yes")
    app.run(host=_host, port=_port, debug=_debug, use_reloader=_debug)
