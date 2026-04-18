#!/usr/bin/env python3
"""
run_probes.py — Automated adversarial probe runner for Oracle Forge data agent.

Runs all 20 probes against the live agent, records observed failures, and saves
results. With --update-docs it writes real data back into probes/probes.md and
probes/results/improvement_log.md, replacing all aspirational placeholder text.

Usage (from project root):
    python probes/run_probes.py                              # Run all probes
    python probes/run_probes.py --probe 1.1                  # Run one probe
    python probes/run_probes.py --probe 1.1 --probe 2.3      # Run several
    python probes/run_probes.py --update-docs                # Baseline run + write to docs
    python probes/run_probes.py --update-docs --mode fixed   # Post-fix run (appends to log)
    python probes/run_probes.py --probe 1.1 --update-docs

Mode semantics:
    baseline (default) — fills "Score Before Fix" and "Baseline Pass Rate" columns.
                         Overwrites improvement_log.md with a fresh baseline entry.
    fixed             — fills "Score After Fix" and "Fixed Pass Rate" columns.
                         Reads existing baseline numbers from probes.md to compute
                         improvement. Appends a post-fix entry to improvement_log.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent  # oracle-forge-data-agent/
sys.path.insert(0, str(ROOT))

# Import agent execution functions directly from app.py
from app import (
    YELP_METRICS_SCALAR,
    build_plan,
    discover_file_native_sources,
    execute_toolbox_chain_and_synthesize,
    run_duckdb,
    run_mongo_aggregate_readonly,
    run_sqlite,
    run_toolbox,
    run_yelp_analytics,
)

PROBES_DIR = Path(__file__).resolve().parent  # probes/
RESULTS_DIR = PROBES_DIR / "results"
PROBES_MD = PROBES_DIR / "probes.md"
IMPROVEMENT_LOG = RESULTS_DIR / "improvement_log.md"

# ---------------------------------------------------------------------------
# Probe definitions — 20 adversarial probes across 4 DAB failure categories
# ---------------------------------------------------------------------------
PROBES: list[dict[str, Any]] = [
    # ── Category 1: Multi-Database Routing ──────────────────────────────────
    {
        "id": "1.1",
        "category": "multi_db_routing",
        "dataset": "yelp",
        "title": "Yelp Business-Review Join",
        "query": "List the names and average star ratings of businesses that have at least 10 reviews mentioning 'service'",
    },
    {
        "id": "1.2",
        "category": "multi_db_routing",
        "dataset": "crmarenapro",
        "title": "CRMArenaPro Customer-Ticket Correlation",
        "query": (
            "Calculate the correlation between customer lifetime value and number of support tickets opened. "
            "Show top 10 customers with highest ticket-to-value ratio."
        ),
    },
    {
        "id": "1.3",
        "category": "multi_db_routing",
        "dataset": "agnews",
        "title": "AG News Article-Category Classification",
        "query": "Count how many sports articles were published in the last 7 days from sources with credibility score above 0.8",
    },
    {
        "id": "1.4",
        "category": "multi_db_routing",
        "dataset": "bookreview",
        "title": "BookReview Book-Reviewer Aggregation",
        "query": (
            "Find the top 5 reviewers who have given the highest average ratings, "
            "but only include reviewers who have reviewed at least 3 books published after 2010"
        ),
    },
    {
        "id": "1.5",
        "category": "multi_db_routing",
        "dataset": "googlelocal",
        "title": "Google Local Business-Review Sentiment",
        "query": (
            "Find all restaurants in San Francisco with average rating above 4.0 "
            "that have at least one review mentioning 'slow service' in the last 30 days"
        ),
    },
    # ── Category 2: Ill-Formatted Key Mismatch ──────────────────────────────
    {
        "id": "2.1",
        "category": "ill_formatted_keys",
        "dataset": "crmarenapro",
        "title": "CRMArenaPro Customer ID Format (CUST-XXXXX vs Integer)",
        "query": "Show the total order value for each customer who opened a high-priority support ticket in Q3 2024",
    },
    {
        "id": "2.2",
        "category": "ill_formatted_keys",
        "dataset": "crmarenapro",
        "title": "CRMArenaPro Product Code vs SKU",
        "query": "List all products that have never been ordered, along with their category and list price",
    },
    {
        "id": "2.3",
        "category": "ill_formatted_keys",
        "dataset": "bookreview",
        "title": "BookReview Book ID Field Name Mismatch",
        "query": "Find the average rating for each book published in 2020 or later",
    },
    {
        "id": "2.4",
        "category": "ill_formatted_keys",
        "dataset": "agnews",
        "title": "AG News Title-Based Join (No ID Match)",
        "query": "What is the most common news category for articles from high-credibility sources (score > 0.9)?",
    },
    {
        "id": "2.5",
        "category": "ill_formatted_keys",
        "dataset": "crmarenapro",
        "title": "CRMArenaPro Order ID Format (ORD-YYYY-XXXXX)",
        "query": "Find all support tickets related to orders placed in December 2024",
    },
    # ── Category 3: Unstructured Text Extraction ─────────────────────────────
    {
        "id": "3.1",
        "category": "unstructured_text",
        "dataset": "yelp",
        "title": "Yelp Review Keyword Counting",
        "query": "How many reviews mention 'wait time' or 'waiting' and have a rating of 2 stars or less?",
    },
    {
        "id": "3.2",
        "category": "unstructured_text",
        "dataset": "crmarenapro",
        "title": "CRMArenaPro Support Ticket Sentiment",
        "query": "Calculate the percentage of support tickets that express negative sentiment, grouped by customer segment",
    },
    {
        "id": "3.3",
        "category": "unstructured_text",
        "dataset": "googlelocal",
        "title": "Google Local Review Attribute Extraction",
        "query": "Which restaurants have the most reviews mentioning 'friendly staff' or 'great service'? Show top 10.",
    },
    {
        "id": "3.4",
        "category": "unstructured_text",
        "dataset": "agnews",
        "title": "AG News Article Category Prediction",
        "query": (
            "Find all articles from the last 30 days that discuss 'artificial intelligence' "
            "but are NOT categorized as Sci/Tech"
        ),
    },
    {
        "id": "3.5",
        "category": "unstructured_text",
        "dataset": "bookreview",
        "title": "BookReview Review-Text Rating Consistency",
        "query": (
            "Find reviews where the text expresses strong negative sentiment but the rating is 4 or 5 stars. "
            "Count how many such inconsistent reviews exist."
        ),
    },
    # ── Category 4: Domain Knowledge Gap ────────────────────────────────────
    {
        "id": "4.1",
        "category": "domain_knowledge",
        "dataset": "yelp",
        "title": '"Active Customer" Definition (Yelp)',
        "query": "Show the geographic distribution of active users across different states",
    },
    {
        "id": "4.2",
        "category": "domain_knowledge",
        "dataset": "crmarenapro",
        "title": '"Churn" Definition (CRMArenaPro)',
        "query": "Calculate the churn rate for enterprise customers in Q4 2024",
    },
    {
        "id": "4.3",
        "category": "domain_knowledge",
        "dataset": "agnews",
        "title": '"Recent" Temporal Scope (AG News)',
        "query": "Show the most common topics in recent business news",
    },
    {
        "id": "4.4",
        "category": "domain_knowledge",
        "dataset": "crmarenapro",
        "title": '"High-Value Customer" Threshold (CRMArenaPro)',
        "query": "Compare the average support ticket resolution time for high-value customers versus regular customers",
    },
    {
        "id": "4.5",
        "category": "domain_knowledge",
        "dataset": "yelp",
        "title": '"Rating" vs "Stars" Distinction (Yelp)',
        "query": (
            "Find businesses where the average rating is above 4.0 "
            "but the most recent 10 reviews average below 3.0"
        ),
    },
    # ── Bonus: Complex Multi-Category ───────────────────────────────────────
    {
        "id": "5.1",
        "category": "multi_category",
        "dataset": "crmarenapro",
        "title": "Complex Multi-Category Probe (CRMArenaPro)",
        "query": (
            "Identify high-value customers who have shown signs of churn risk "
            "(multiple recent support tickets with negative sentiment) but have not been contacted "
            "by sales in the last 30 days. Show their lifetime value and recommended next action."
        ),
    },
]

PROBE_BY_ID: dict[str, dict[str, Any]] = {p["id"]: p for p in PROBES}

# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def execute_plan(user_input: str, plan: dict[str, Any], db_options: dict) -> tuple[Any, str]:
    """Dispatch a plan dict to the correct executor; return (response, error_str)."""
    executor = plan["route"]["executor"]
    sql = plan.get("query")
    tool = plan["route"].get("tool", "")

    if executor == "error":
        return None, plan["route"].get("reason", "Planner error")

    if executor == "yelp-analytics":
        if "mongo_filter" not in plan:
            return None, "yelp-analytics plan missing mongo_filter"
        resp = run_yelp_analytics(
            plan["mongo_filter"],
            db_options,
            duckdb_aggregation=plan.get("duckdb_aggregation", "avg_rating"),
            yelp_metrics_mode=plan.get("yelp_metrics_mode", YELP_METRICS_SCALAR),
            yelp_rank_limit=int(plan.get("yelp_rank_limit", 5) or 5),
            order_desc=bool(plan.get("order_desc", True)),
        )
        if isinstance(resp, dict) and "error" in resp:
            return None, resp["error"]
        return resp, ""

    if executor == "toolbox-chain":
        resp = execute_toolbox_chain_and_synthesize(user_input, plan)
        if isinstance(resp, dict) and "error" in resp:
            return resp, resp["error"]
        return resp, ""

    if executor == "toolbox":
        payload: dict[str, Any] = {}
        if sql:
            payload["query"] = sql
        if plan.get("filterJson") is not None:
            payload["filterJson"] = plan["filterJson"]
        if plan.get("pipelineJson") is not None:
            payload["pipelineJson"] = plan["pipelineJson"]
        resp = run_toolbox(tool, payload)
        if isinstance(resp, dict) and "error" in resp:
            return None, resp["error"]
        return resp, ""

    if executor == "mongo-local":
        pl = plan.get("mongo_pipeline")
        dbn = plan.get("mongo_database")
        coll = plan.get("mongo_collection")
        if not isinstance(pl, list) or not dbn or not coll:
            return None, "mongo-local plan missing database/collection/pipeline"
        resp = run_mongo_aggregate_readonly(str(dbn), str(coll), pl)
        if isinstance(resp, dict) and "error" in resp:
            return None, resp["error"]
        return resp, ""

    if executor == "sqlite-local":
        db_path = Path(plan["route"].get("database", ""))
        if not sql:
            return None, "SQLite plan missing query text"
        resp = run_sqlite(sql, db_path)
        if isinstance(resp, dict) and "error" in resp:
            return None, resp["error"]
        return resp, ""

    if executor == "duckdb-local":
        db_path = Path(plan["route"].get("database", ""))
        if not sql:
            return None, "DuckDB plan missing query text"
        resp = run_duckdb(sql, db_path)
        if isinstance(resp, dict) and "error" in resp:
            return None, resp["error"]
        return resp, ""

    return None, f"Unknown executor: {executor!r}"


def _truncate(obj: Any, max_chars: int = 400) -> str:
    s = json.dumps(obj, default=str, ensure_ascii=False)
    return s if len(s) <= max_chars else s[:max_chars] + "…"


def describe_failure(plan: dict, response: Any, error: str) -> str:
    """Generate a human-readable observed-failure description for probes.md."""
    executor = plan["route"]["executor"]
    reason = plan["route"].get("reason", "")
    sql = plan.get("query")
    lines: list[str] = [f"Executor selected: {executor}"]
    if reason:
        lines.append(f"Routing reason: {reason}")
    if sql:
        lines.append(f"Generated query: {sql[:200]}")
    if executor == "error":
        lines.append(f"Planning failed — no executor chosen. Reason: {error}")
    elif error:
        lines.append(f"Execution error: {error}")
    elif response is not None:
        lines.append(f"Response (truncated): {_truncate(response)}")
    else:
        lines.append("No response and no error returned.")
    return "\n".join(lines)


def run_probe(probe: dict[str, Any], db_options: dict) -> dict[str, Any]:
    """Run a single probe against the live agent; return a result dict."""
    t0 = time.time()
    try:
        plan = build_plan(probe["query"], db_options)
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.time() - t0) * 1000)
        return {
            "id": probe["id"],
            "title": probe["title"],
            "category": probe["category"],
            "dataset": probe["dataset"],
            "query": probe["query"],
            "executor": "exception",
            "plan_reason": "",
            "plan_query": None,
            "response": None,
            "error": str(exc),
            "duration_ms": duration_ms,
            "passed": False,
            "observed_failure": f"Exception during build_plan: {exc}",
        }

    try:
        response, error = execute_plan(probe["query"], plan, db_options)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        response = None

    duration_ms = int((time.time() - t0) * 1000)
    passed = response is not None and not error

    return {
        "id": probe["id"],
        "title": probe["title"],
        "category": probe["category"],
        "dataset": probe["dataset"],
        "query": probe["query"],
        "executor": plan["route"]["executor"],
        "plan_reason": plan["route"].get("reason", ""),
        "plan_query": plan.get("query"),
        "response": response,
        "error": error or None,
        "duration_ms": duration_ms,
        "passed": passed,
        "observed_failure": describe_failure(plan, response, error or ""),
    }


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------

def save_results(results: list[dict[str, Any]], timestamp: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"run_{timestamp}.json"
    out_path.write_text(
        json.dumps(
            {"run_timestamp": timestamp, "probes": {r["id"]: r for r in results}},
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    return out_path


# ---------------------------------------------------------------------------
# probes.md updater helpers
# ---------------------------------------------------------------------------

def _replace_probe_observed_failure(content: str, probe_id: str, text: str) -> str:
    """Replace the content inside the ``` block after **Observed Failure:** for one probe."""
    marker = f"#### Probe {probe_id}:"
    idx = content.find(marker)
    if idx == -1:
        return content
    next_idx = content.find("#### Probe ", idx + len(marker))
    if next_idx == -1:
        next_idx = len(content)
    section = content[idx:next_idx]

    new_section = re.sub(
        r"(\*\*Observed Failure:\*\*\n```\n).*?(\n```)",
        lambda m: m.group(1) + text + m.group(2),
        section,
        flags=re.DOTALL,
    )
    return content[:idx] + new_section + content[next_idx:]


def _replace_probe_score_before(content: str, probe_id: str, score: int) -> str:
    marker = f"#### Probe {probe_id}:"
    idx = content.find(marker)
    if idx == -1:
        return content
    next_idx = content.find("#### Probe ", idx + len(marker))
    if next_idx == -1:
        next_idx = len(content)
    section = content[idx:next_idx]
    new_section = section.replace("**Score Before Fix:** ___ / 1", f"**Score Before Fix:** {score} / 1")
    return content[:idx] + new_section + content[next_idx:]


def _replace_probe_score_after(content: str, probe_id: str, score: int) -> str:
    marker = f"#### Probe {probe_id}:"
    idx = content.find(marker)
    if idx == -1:
        return content
    next_idx = content.find("#### Probe ", idx + len(marker))
    if next_idx == -1:
        next_idx = len(content)
    section = content[idx:next_idx]
    new_section = section.replace("**Score After Fix:** ___ / 1", f"**Score After Fix:** {score} / 1")
    return content[:idx] + new_section + content[next_idx:]


def _parse_table_baseline(content: str) -> dict[str, str]:
    """Extract Baseline Pass Rate values from an existing summary table in probes.md."""
    result: dict[str, str] = {}
    for cat in [
        "Multi-Database Routing",
        "Ill-Formatted Key Mismatch",
        "Unstructured Text Extraction",
        "Domain Knowledge Gap",
    ]:
        m = re.search(
            r'\|\s*' + re.escape(cat) + r'\s*\|\s*\d+\s*\|\s*([^|\n]+?)\s*\|',
            content,
        )
        if m:
            result[cat] = m.group(1).strip()
    # TOTAL row: | **TOTAL** | **20** | **X% (N/M)** | ...
    m = re.search(
        r'\|\s*\*\*TOTAL\*\*\s*\|\s*\*\*\d+\*\*\s*\|\s*\*\*([^|\n*]+?)\*\*\s*\|',
        content,
    )
    if m:
        result["TOTAL"] = m.group(1).strip()
    return result


def _calc_improvement(baseline_str: str, fixed_pass: int, fixed_total: int) -> str:
    """Return improvement in percentage-points, e.g. '+40pp'. Returns 'TBD' if baseline unknown."""
    if not baseline_str or baseline_str == "TBD" or fixed_total == 0:
        return "TBD"
    m = re.match(r'(\d+)%', baseline_str)
    if not m:
        return "TBD"
    baseline_pct = int(m.group(1))
    fixed_pct = int(fixed_pass / fixed_total * 100)
    delta = fixed_pct - baseline_pct
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta}pp"


def _build_summary_table(
    results: list[dict[str, Any]],
    mode: str = "baseline",
    existing_content: str = "",
) -> str:
    """
    Build the summary table for probes.md.

    baseline mode: fills Baseline Pass Rate; Fixed Pass Rate = TBD.
    fixed mode:    fills Fixed Pass Rate; reads Baseline from existing_content;
                   calculates Improvement in percentage-points.
    """
    cat_map = {
        "multi_db_routing": "Multi-Database Routing",
        "ill_formatted_keys": "Ill-Formatted Key Mismatch",
        "unstructured_text": "Unstructured Text Extraction",
        "domain_knowledge": "Domain Knowledge Gap",
    }
    stats: dict[str, dict[str, int]] = {v: {"total": 0, "pass": 0} for v in cat_map.values()}
    for r in results:
        key = cat_map.get(r["category"])
        if key:
            stats[key]["total"] += 1
            if r["passed"]:
                stats[key]["pass"] += 1

    def fmt(s: dict[str, int]) -> str:
        if s["total"] == 0:
            return "TBD"
        pct = int(s["pass"] / s["total"] * 100)
        return f"{pct}% ({s['pass']}/{s['total']})"

    baseline_vals = _parse_table_baseline(existing_content) if mode == "fixed" else {}

    total_pass = sum(s["pass"] for s in stats.values())
    total_total = sum(s["total"] for s in stats.values())
    total_fmt = f"{int(total_pass/total_total*100)}% ({total_pass}/{total_total})" if total_total else "TBD"

    rows = [
        "| Category | Probes Count | Baseline Pass Rate | Fixed Pass Rate | Improvement |",
        "|----------|--------------|-------------------|-----------------|-------------|",
    ]

    for cat_key in [
        "Multi-Database Routing",
        "Ill-Formatted Key Mismatch",
        "Unstructured Text Extraction",
        "Domain Knowledge Gap",
    ]:
        s = stats[cat_key]
        if mode == "baseline":
            baseline_col = fmt(s)
            fixed_col = "TBD"
            improvement = "TBD"
        else:
            baseline_col = baseline_vals.get(cat_key, "TBD")
            fixed_col = fmt(s)
            improvement = _calc_improvement(baseline_col, s["pass"], s["total"])
        rows.append(f"| {cat_key} | {s['total']} | {baseline_col} | {fixed_col} | {improvement} |")

    if mode == "baseline":
        total_baseline = total_fmt
        total_fixed = "TBD"
        total_improvement = "TBD"
    else:
        total_baseline = baseline_vals.get("TOTAL", "TBD")
        total_fixed = total_fmt
        total_improvement = _calc_improvement(total_baseline, total_pass, total_total)

    rows.append(
        f"| **TOTAL** | **{total_total}** | **{total_baseline}** | **{total_fixed}** | **{total_improvement}** |"
    )
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# probes.md top-level updater
# ---------------------------------------------------------------------------

def update_probes_md(results: list[dict[str, Any]], timestamp: str, mode: str = "baseline") -> None:
    content = PROBES_MD.read_text(encoding="utf-8")

    # 1. Replace summary stats table
    new_table = _build_summary_table(results, mode=mode, existing_content=content)
    content = re.sub(
        r"\| Category \| Probes Count \| Baseline Pass Rate.*?\| \*\*TOTAL\*\*.*?\|",
        new_table,
        content,
        flags=re.DOTALL,
    )

    # 2. Per-probe: observed failure + appropriate score field
    for r in results:
        if mode == "baseline":
            content = _replace_probe_observed_failure(content, r["id"], r["observed_failure"])
            content = _replace_probe_score_before(content, r["id"], 1 if r["passed"] else 0)
        else:
            content = _replace_probe_score_after(content, r["id"], 1 if r["passed"] else 0)

    # 3. Stamp the run date in the Maintenance Log table
    run_date = timestamp[:10]
    total_pass = sum(1 for r in results if r["passed"])
    total = len(results)
    mode_label = "Baseline run" if mode == "baseline" else "Post-fix run"
    maintenance_row = (
        f"| {run_date} | all | {mode_label} | "
        f"{int(total_pass/total*100) if total else 0}% ({total_pass}/{total}) | TBD | Martha |"
    )
    content = content.replace(
        "| [Date] | [ID] | [Initial run/Fix applied] | [%] | [%] | [Name] |",
        maintenance_row,
    )

    PROBES_MD.write_text(content, encoding="utf-8")
    print(f"  Updated {PROBES_MD.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# improvement_log.md updater
# ---------------------------------------------------------------------------

def update_improvement_log(
    results: list[dict[str, Any]],
    timestamp: str,
    run_path: Path,
    mode: str = "baseline",
) -> None:
    run_date = timestamp[:10]
    total = len(results)
    total_pass = sum(1 for r in results if r["passed"])
    pass_pct = int(total_pass / total * 100) if total else 0

    cat_map = {
        "multi_db_routing": "Multi-DB Routing",
        "ill_formatted_keys": "Key Mismatch",
        "unstructured_text": "Text Extraction",
        "domain_knowledge": "Domain Knowledge",
        "multi_category": "Multi-Category",
    }

    failures_by_cat: dict[str, list[str]] = {}
    passes_by_cat: dict[str, list[str]] = {}
    for r in results:
        label = cat_map.get(r["category"], r["category"])
        if r["passed"]:
            passes_by_cat.setdefault(label, []).append(r["id"])
        else:
            failures_by_cat.setdefault(label, []).append(r["id"])

    failure_lines = "\n".join(
        f"  - {cat}: probes {', '.join(ids)} failed"
        for cat, ids in sorted(failures_by_cat.items())
    ) or "  - None"

    if mode == "baseline":
        content = f"""# Probe Library Improvement Log

Run `python probes/run_probes.py --update-docs` to add new entries.
Run `python probes/run_probes.py --update-docs --mode fixed` after applying fixes.

---

## Run: {run_date} (baseline)
- **Results file:** {run_path.name}
- **Overall pass rate:** {pass_pct}% ({total_pass}/{total})
- **Key failures:**
{failure_lines}

---

_Post-fix runs will appear here after fixes are applied and re-run._
"""
        IMPROVEMENT_LOG.write_text(content, encoding="utf-8")

    else:  # fixed — append a new section
        passing_lines = "\n".join(
            f"  - {cat}: probes {', '.join(ids)} now pass"
            for cat, ids in sorted(passes_by_cat.items())
        ) or "  - None"

        new_section = f"""
---

## Run: {run_date} (post-fix)
- **Results file:** {run_path.name}
- **Overall pass rate (fixed):** {pass_pct}% ({total_pass}/{total})
- **Probes now passing:**
{passing_lines}
- **Still failing:**
{failure_lines}
"""
        existing = (
            IMPROVEMENT_LOG.read_text(encoding="utf-8")
            if IMPROVEMENT_LOG.exists()
            else "# Probe Library Improvement Log\n\n"
        )
        # Remove trailing sentinel line so the new section replaces it
        existing = re.sub(r"\n_Post-fix runs will appear.*?_\s*$", "", existing, flags=re.DOTALL)
        IMPROVEMENT_LOG.write_text(existing.rstrip() + "\n" + new_section, encoding="utf-8")

    print(f"  Updated {IMPROVEMENT_LOG.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {
    "multi_db_routing": "Multi-DB Routing",
    "ill_formatted_keys": "Ill-Formatted Keys",
    "unstructured_text": "Unstructured Text",
    "domain_knowledge": "Domain Knowledge",
    "multi_category": "Multi-Category",
}


def print_summary(results: list[dict[str, Any]], mode: str) -> None:
    print("\n" + "=" * 70)
    print(f"PROBE RUN SUMMARY  [{mode.upper()}]")
    print("=" * 70)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"Overall: {passed}/{total} passed ({int(passed/total*100) if total else 0}%)\n")

    by_cat: dict[str, list[dict]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)

    for cat, items in sorted(by_cat.items()):
        cat_pass = sum(1 for r in items if r["passed"])
        label = CATEGORY_LABELS.get(cat, cat)
        print(f"  {label}: {cat_pass}/{len(items)}")
        for r in items:
            icon = "✓" if r["passed"] else "✗"
            ms = r["duration_ms"]
            exec_ = r["executor"]
            err = f"  [{r['error'][:60]}]" if r["error"] else ""
            print(f"    {icon} {r['id']:4s}  {exec_:20s}  {ms:5d}ms{err}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run adversarial probes against the Oracle Forge data agent."
    )
    parser.add_argument(
        "--probe",
        action="append",
        metavar="ID",
        help="Probe ID(s) to run (e.g. 1.1, 2.3). Repeatable. Default: all.",
    )
    parser.add_argument(
        "--update-docs",
        action="store_true",
        help="Write results back into probes/probes.md and improvement_log.md.",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "fixed"],
        default="baseline",
        help=(
            "baseline (default): fills Score Before Fix + Baseline Pass Rate columns. "
            "fixed: fills Score After Fix + Fixed Pass Rate columns; appends to improvement log."
        ),
    )
    args = parser.parse_args()

    # Select probes
    if args.probe:
        unknown = [p for p in args.probe if p not in PROBE_BY_ID]
        if unknown:
            print(f"Unknown probe IDs: {unknown}")
            print(f"Valid IDs: {sorted(PROBE_BY_ID)}")
            sys.exit(1)
        selected = [PROBE_BY_ID[p] for p in args.probe]
    else:
        selected = PROBES

    print(f"Running {len(selected)} probe(s)  [mode={args.mode}]…")
    db_options = discover_file_native_sources()

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    results: list[dict[str, Any]] = []

    for probe in selected:
        print(f"  [{probe['id']:4s}] {probe['title'][:55]}…", end=" ", flush=True)
        result = run_probe(probe, db_options)
        results.append(result)
        status = "PASS" if result["passed"] else f"FAIL ({result['executor']})"
        print(f"{status}  ({result['duration_ms']}ms)")

    print_summary(results, args.mode)

    run_path = save_results(results, timestamp)
    print(f"\nResults saved: {run_path.relative_to(ROOT)}")

    if args.update_docs:
        print("\nUpdating documentation…")
        update_probes_md(results, timestamp, mode=args.mode)
        update_improvement_log(results, timestamp, run_path, mode=args.mode)
        print("Done.")


if __name__ == "__main__":
    main()
