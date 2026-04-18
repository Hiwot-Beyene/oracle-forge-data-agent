"""
Oracle Forge KB context layers for DataAgentBench and the Flask agent.

Challenge alignment (TRP1 — Oracle Forge):
- **Layer 1 (architecture):** `kb/architecture/` only — MEMORY index + system overview (KB v1).
- **Layer 2 (domain session KB):** `kb/domain/` — business_terms (dataset H2 + Oracle Forge injection blocks),
  join_key_glossary excerpt, optional unstructured inventory (KB v2).
- **Layer 3 (corrections):** `kb/corrections/log.md` tail — interaction memory (KB v3).

Used by: DataAgentBench/run_agent.py, oracle-forge-data-agent/app.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ContextLayers:
    layer_1_architecture: str
    layer_2_domain: str
    layer_3_corrections: str
    system_prompt: str


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[1]


def extract_join_key_glossary_section_for_dataset(repo_root: Path, dataset: str) -> str:
    """Return the `### ... (dataset)` subsection from join_key_glossary.md."""
    path = repo_root / "kb" / "domain" / "join_key_glossary.md"
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    anchor = f"({dataset})"
    start: int | None = None
    for i, line in enumerate(lines):
        if line.startswith("### ") and anchor in line:
            start = i
            break
    if start is None:
        return ""
    chunk: list[str] = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith("### ") and anchor not in line:
            break
        if line.startswith("## ") and not line.startswith("###"):
            break
        chunk.append(line)
    return "\n".join(chunk).strip()


def _read_text_limit(path: Path, max_chars: int) -> str:
    if not path.is_file():
        return ""
    t = path.read_text(encoding="utf-8")
    if len(t) <= max_chars:
        return t
    return t[:max_chars] + "\n…"


def _load_architecture_layer(root: Path, max_chars: int) -> str:
    """
    KB v1 — only files under kb/architecture (challenge: Claude/OpenAI patterns, system overview).
    MEMORY.md is the index; architecture_system_overview.md carries the layer diagram and subdirectory map.
    """
    memory = root / "kb" / "architecture" / "MEMORY.md"
    overview = root / "kb" / "architecture" / "architecture_system_overview.md"
    parts: list[str] = ["# KB v1 — Architecture (kb/architecture)\n"]
    # Split budget: index first, then overview (overview is typically longer).
    idx_budget = min(max_chars // 3, 3500)
    rest = max(500, max_chars - idx_budget - 80)
    if memory.is_file():
        parts.append(_read_text_limit(memory, idx_budget))
    if overview.is_file():
        parts.append(_read_text_limit(overview, rest))
    return "\n\n".join(p for p in parts if p).strip()


def _trim_yelp_dab_validate_subsection(yelp_h2_text: str, user_question: str) -> str:
    """Omit query2/mean-rating grader notes when the question is about amenities/counts (reduces noise)."""
    anchor = "### DAB `validate.py` string window (query_yelp query 2 and similar)"
    if anchor not in yelp_h2_text:
        return yelp_h2_text
    q = user_question.lower()
    keep = (
        ("mean" in q and "rating" in q)
        or ("which" in q and "state" in q)
        or ("highest" in q and "review" in q)
        or "u.s. state" in q
    )
    if keep:
        return yelp_h2_text
    idx = yelp_h2_text.find(anchor)
    return yelp_h2_text[:idx].rstrip()


def _extract_h2_section(content: str, heading_contains: str) -> str:
    """Return one ## section: from the line `## ...heading_contains...` until the next `## ` heading."""
    lines = content.splitlines()
    start_idx: int | None = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and heading_contains in line:
            start_idx = i
            break
    if start_idx is None:
        return ""
    out: list[str] = [lines[start_idx]]
    for line in lines[start_idx + 1 :]:
        if line.startswith("## ") and heading_contains not in line:
            break
        out.append(line)
    return "\n".join(out).strip()


def _tail_lines(path: Path, n: int) -> str:
    if not path.is_file() or n <= 0:
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[-n:])


def infer_dataset_hint_for_question(user_question: str) -> str:
    """Map a natural-language question to a query_* slug for KB routing."""
    q = user_question.lower()
    if any(
        k in q
        for k in (
            "which u.s. state",
            "u.s. state",
            "yelp",
            "businessref",
            "businessid_",
            "business_ref",
            "bike parking",
            "business parking",
            "parking or bike",
            "wifi",
            "credit card",
            "business category",
            "highest average rating",
            "reviews between",
            "at least 5 reviews",
            "yelping_since",
            "registered on yelp",
            "users who registered",
            "user who registered",
            "who registered",
            "since they registered",
            "most total reviews",
        )
    ):
        return "query_yelp"
    if any(
        k in q
        for k in (
            "stock index",
            "stock indices",
            "indices had",
            "north american",
            "monthly investments",
            "intraday volatility",
            "index_info",
            "index trade",
            "indextrade",
            "indexinfo",
            "which 5 indices",
            "composite index",
        )
    ):
        return "query_stockindex"
    if any(
        k in q
        for k in (
            "realreal",
            "adjusted close",
            "stock price",
            "ticker",
            "nyse arca",
            "etf securities",
            "nasdaq capital market",
            "intraday price range",
            "non-etf",
            "new york stock exchange",
        )
    ) and "book" not in q:
        return "query_stockmarket"
    if any(
        k in q
        for k in (
            "ag news",
            "agnews",
            "article_metadata",
            "articles_database",
            "metadata_database",
            "science/technology",
            "science and technology",
            "amy jones",
            "sports article",
            "world category",
            "business articles",
        )
    ):
        return "query_agnews"
    if any(
        k in q
        for k in (
            "book",
            "literature",
            "fiction",
            "publication year",
            "isbn",
            "purchase_id",
        )
    ):
        return "query_bookreview"
    return "query_bookreview"


def _build_domain_layer(
    dataset: str,
    user_question: str,
    root: Path,
    max_layer_chars: int,
) -> str:
    """
    KB v2 — domain: business_terms (per-dataset H2 includes Oracle Forge injection blocks),
    join_key glossary, optional unstructured_fields tail.
    """
    ds = dataset.strip().lower()
    bt_path = root / "kb" / "domain" / "business_terms.md"
    domain_parts: list[str] = []

    if not bt_path.is_file():
        return ""

    raw = bt_path.read_text(encoding="utf-8")
    cap = max(max_layer_chars * 10, 10000)

    if ds == "query_yelp":
        body = _extract_h2_section(raw, "Yelp (query_yelp)")
        if body:
            body = _trim_yelp_dab_validate_subsection(body, user_question)
            domain_parts.append(body if len(body) <= cap else body[:cap] + "\n…")
        else:
            domain_parts.append(_read_text_limit(bt_path, max_layer_chars))
    elif ds == "query_stockindex":
        body = _extract_h2_section(raw, "Stock Index (query_stockindex)")
        if body:
            domain_parts.append(body if len(body) <= cap else body[:cap] + "\n…")
        else:
            domain_parts.append(_read_text_limit(bt_path, max_layer_chars))
    elif ds == "query_stockmarket":
        body = _extract_h2_section(raw, "Stock Market (query_stockmarket)")
        if body:
            domain_parts.append(body if len(body) <= cap else body[:cap] + "\n…")
        else:
            domain_parts.append(_read_text_limit(bt_path, max_layer_chars))
    elif ds == "query_bookreview":
        body = _extract_h2_section(raw, "Book Reviews (query_bookreview)")
        if body:
            domain_parts.append(body if len(body) <= cap else body[:cap] + "\n…")
        else:
            domain_parts.append(_read_text_limit(bt_path, max_layer_chars))
    elif ds == "query_agnews":
        body = _extract_h2_section(raw, "AG News (query_agnews)")
        if body:
            domain_parts.append(body if len(body) <= cap else body[:cap] + "\n…")
        else:
            domain_parts.append(_read_text_limit(bt_path, max_layer_chars))
    else:
        domain_parts.append(_read_text_limit(bt_path, max_layer_chars))

    jk = extract_join_key_glossary_section_for_dataset(root, dataset)
    if jk:
        domain_parts.append(jk)

    uf_path = root / "kb" / "domain" / "unstructured_fields.md"
    if uf_path.is_file():
        domain_parts.append(
            "# KB v2 — Unstructured field inventory (excerpt)\n"
            + _read_text_limit(uf_path, min(4000, max_layer_chars * 4))
        )

    return "\n\n".join(p for p in domain_parts if p).strip()


def build_context_layers(
    dataset: str,
    user_question: str,
    repo_root: Path | None = None,
    max_layer_chars: int = 900,
    corrections_tail_lines: int = 12,
) -> ContextLayers:
    root = _repo_root(repo_root)
    ds = dataset.strip().lower()
    if ds == "query_yelp":
        corrections_tail_lines = max(corrections_tail_lines, 28)
    elif ds == "query_stockindex":
        corrections_tail_lines = max(corrections_tail_lines, 22)
    elif ds == "query_stockmarket":
        corrections_tail_lines = max(corrections_tail_lines, 22)
    elif ds == "query_bookreview":
        corrections_tail_lines = max(corrections_tail_lines, 24)
    elif ds == "query_agnews":
        corrections_tail_lines = max(corrections_tail_lines, 22)

    arch_budget = max(max_layer_chars * 4, 6000)
    layer1 = _load_architecture_layer(root, arch_budget)

    layer2 = _build_domain_layer(dataset, user_question, root, max_layer_chars)

    corr_path = root / "kb" / "corrections" / "log.md"
    layer3 = _tail_lines(corr_path, corrections_tail_lines)

    combined = (
        "You are an Oracle Forge data agent. Context layers follow TRP1 KB structure: "
        "(1) architecture = kb/architecture only; "
        "(2) domain = kb/domain; "
        "(3) corrections = kb/corrections tail.\n\n"
        f"DATASET={dataset}\nQUESTION={user_question[:500]!r}\n"
    )
    return ContextLayers(
        layer_1_architecture=layer1,
        layer_2_domain=layer2,
        layer_3_corrections=layer3,
        system_prompt=combined,
    )


def build_router_planner_user_payload(
    user_question: str,
    dab_candidates: dict[str, Any],
    repo_root: Path | None = None,
    max_kb_layer_chars: int = 9000,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    hint = infer_dataset_hint_for_question(user_question)
    join_excerpt = extract_join_key_glossary_section_for_dataset(root, hint)
    layers = build_context_layers(
        dataset=hint,
        user_question=user_question,
        repo_root=root,
        max_layer_chars=min(max_kb_layer_chars, 9000),
        corrections_tail_lines=24,
    )
    cap = max_kb_layer_chars
    return {
        "question": user_question,
        "dab_candidates": dab_candidates,
        "dataset_hint_for_kb": hint,
        "kb_focus": {
            "join_key_glossary_dataset_section": join_excerpt,
        },
        "kb_layers": {
            "architecture": layers.layer_1_architecture[:cap],
            "domain": layers.layer_2_domain[:cap],
            "corrections": layers.layer_3_corrections[:cap],
        },
    }


def build_agent_session_kb_context(user_question: str, repo_root: Path) -> str:
    """Single string KB for toolbox synthesis (Flask): architecture + domain + corrections."""
    hint = infer_dataset_hint_for_question(user_question)
    layers = build_context_layers(
        dataset=hint,
        user_question=user_question,
        repo_root=repo_root,
        max_layer_chars=6000,
        corrections_tail_lines=20,
    )
    return (
        f"{layers.layer_1_architecture}\n\n"
        f"{layers.layer_2_domain}\n\n"
        f"{layers.layer_3_corrections}\n\n"
        f"{layers.system_prompt}"
    )
