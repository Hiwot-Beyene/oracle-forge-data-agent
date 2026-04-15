from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import re


DEFAULT_ARCHITECTURE_FILES = (
    "MEMORY.md",
    "architecture_system_overview.md",
    "claude_tool_scoping.md",
    "oracle_forge_mapping.md",
)

DEFAULT_DOMAIN_FILES = (
    "business_terms.md",
    "join_key_glossary.md",
    "unstructured_fields.md",
)

DATASET_ALIASES = {
    "bookreview": "query_bookreview",
    "query_bookreview": "query_bookreview",
    "book_review": "query_bookreview",
    "yelp": "query_yelp",
    "query_yelp": "query_yelp",
    "agnews": "query_agnews",
    "query_agnews": "query_agnews",
    "crmarenapro": "query_crmarenapro",
    "query_crmarenapro": "query_crmarenapro",
    "deps_dev_v1": "query_DEPS_DEV_V1",
    "query_deps_dev_v1": "query_DEPS_DEV_V1",
    "github_repos": "query_GITHUB_REPOS",
    "query_github_repos": "query_GITHUB_REPOS",
    "googlelocal": "query_googlelocal",
    "query_googlelocal": "query_googlelocal",
    "music_brainz_20k": "query_music_brainz_20k",
    "query_music_brainz_20k": "query_music_brainz_20k",
    "pancancer_atlas": "query_PANCANCER_ATLAS",
    "query_pancancer_atlas": "query_PANCANCER_ATLAS",
    "patents": "query_PATENTS",
    "query_patents": "query_PATENTS",
    "stockindex": "query_stockindex",
    "query_stockindex": "query_stockindex",
    "stockmarket": "query_stockmarket",
    "query_stockmarket": "query_stockmarket",
}


@dataclass
class ContextLayers:
    layer_1_architecture: str
    layer_2_domain: str
    layer_3_corrections: str
    system_prompt: str
    warnings: List[str] = field(default_factory=list)


def build_context_layers(
    dataset: Optional[str],
    user_question: str,
    repo_root: Optional[Path] = None,
    max_layer_chars: int = 9000,
    corrections_tail_lines: int = 120,
) -> ContextLayers:
    root = _resolve_repo_root(repo_root)
    warnings: List[str] = []

    layer_1 = _build_architecture_layer(root, warnings, max_layer_chars=max_layer_chars)
    layer_2 = _build_domain_layer(
        root=root,
        dataset=dataset,
        warnings=warnings,
        max_layer_chars=max_layer_chars,
    )
    layer_3 = _build_corrections_layer(
        root=root,
        warnings=warnings,
        tail_lines=corrections_tail_lines,
        max_layer_chars=max_layer_chars,
    )

    system_prompt = _assemble_system_prompt(
        question=user_question,
        dataset=dataset,
        layer_1=layer_1,
        layer_2=layer_2,
        layer_3=layer_3,
    )
    return ContextLayers(
        layer_1_architecture=layer_1,
        layer_2_domain=layer_2,
        layer_3_corrections=layer_3,
        system_prompt=system_prompt,
        warnings=warnings,
    )


def _resolve_repo_root(repo_root: Optional[Path]) -> Path:
    if repo_root:
        return repo_root
    return Path(__file__).resolve().parents[1]


def _build_architecture_layer(root: Path, warnings: List[str], max_layer_chars: int) -> str:
    architecture_dir = root / "kb" / "architecture"
    chunks: List[str] = []

    for filename in DEFAULT_ARCHITECTURE_FILES:
        content = _read_text(architecture_dir / filename, warnings)
        if content:
            chunks.append(f"### {filename}\n{content}")

    if not chunks:
        return "[Architecture layer unavailable: no KB architecture files found.]"
    return _truncate("\n\n".join(chunks), max_layer_chars)


def _build_domain_layer(
    root: Path,
    dataset: Optional[str],
    warnings: List[str],
    max_layer_chars: int,
) -> str:
    domain_dir = root / "kb" / "domain"
    chunks: List[str] = []

    for filename in DEFAULT_DOMAIN_FILES:
        content = _read_text(domain_dir / filename, warnings)
        if content:
            chunks.append(f"### {filename}\n{content}")

    schemas_path = domain_dir / "schemas.md"
    schema_content = _read_text(schemas_path, warnings)
    canonical_dataset = _canonical_dataset(dataset)

    if schema_content:
        scoped_schema = _extract_dataset_scoped_schema(schema_content, canonical_dataset)
        chunks.append(f"### schemas.md (scoped)\n{scoped_schema}")
    if canonical_dataset is None:
        warnings.append("Dataset was not provided or not recognized; schema scope is broad.")

    if not chunks:
        return "[Domain layer unavailable: no KB domain files found.]"
    return _truncate("\n\n".join(chunks), max_layer_chars)


def _build_corrections_layer(
    root: Path,
    warnings: List[str],
    tail_lines: int,
    max_layer_chars: int,
) -> str:
    corrections_path = root / "kb" / "corrections" / "log.md"
    content = _read_text(corrections_path, warnings, required=False)

    if not content:
        return (
            "[No corrections log entries found yet. On every failed or low-confidence run, "
            "append a structured entry: query -> failure cause -> corrected approach.]"
        )

    lines = [line for line in content.splitlines() if line.strip()]
    recent = "\n".join(lines[-tail_lines:])
    return _truncate(recent, max_layer_chars)


def _assemble_system_prompt(
    question: str,
    dataset: Optional[str],
    layer_1: str,
    layer_2: str,
    layer_3: str,
) -> str:
    dataset_value = _canonical_dataset(dataset) or "unspecified"
    parts = [
        "You are the Oracle Forge data agent.",
        f"Target dataset: {dataset_value}",
        "Apply architecture and tool-scoping rules first, then domain semantics, then corrections memory.",
        "Always show database/tool choices, join-key normalization decisions, and confidence.",
        "",
        "## Layer 1: Architecture Rules",
        layer_1,
        "",
        "## Layer 2: Domain Knowledge",
        layer_2,
        "",
        "## Layer 3: Corrections Memory",
        layer_3,
        "",
        "## User Question",
        question,
    ]
    return "\n".join(parts)


def _canonical_dataset(dataset: Optional[str]) -> Optional[str]:
    if not dataset:
        return None
    key = dataset.strip().lower()
    return DATASET_ALIASES.get(key, DATASET_ALIASES.get(key.replace("-", "_")))


def _extract_dataset_scoped_schema(content: str, canonical_dataset: Optional[str]) -> str:
    if not canonical_dataset:
        return content

    match = re.search(r"^##\s+(.+)$", content, flags=re.MULTILINE)
    if not match:
        return content

    sections = _split_markdown_sections(content)
    selected: List[str] = []
    wanted = canonical_dataset.lower()

    for heading, body in sections:
        h = heading.lower()
        if wanted in h:
            selected.append(f"## {heading}\n{body}".rstrip())

    if selected:
        return "\n\n".join(selected)

    # Fallback: include authoritative selection block if dataset section is not detected.
    for heading, body in sections:
        if "authoritative table selection guide" in heading.lower():
            selected.append(f"## {heading}\n{body}".rstrip())
            break
    return "\n\n".join(selected) if selected else content


def _split_markdown_sections(content: str) -> List[tuple[str, str]]:
    lines = content.splitlines()
    sections: List[tuple[str, str]] = []
    current_heading: Optional[str] = None
    current_body: List[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_body).strip()))
            current_heading = line[3:].strip()
            current_body = []
        elif current_heading is not None:
            current_body.append(line)

    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_body).strip()))
    return sections


def _read_text(path: Path, warnings: List[str], required: bool = True) -> str:
    if not path.exists():
        if required:
            warnings.append(f"Missing required context file: {path}")
        return ""
    content = path.read_text(encoding="utf-8").strip()
    if required and not content:
        warnings.append(f"Context file is empty: {path}")
    return content


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 40] + "\n\n[truncated for prompt budget]"


def infer_canonical_dataset_from_question(question: str) -> Optional[str]:
    """Map question text to a canonical query_* id to scope which KB/domain files matter (schema + join rows). Not an answer cache."""
    if not question:
        return None
    lower = question.lower()
    for alias, canonical in DATASET_ALIASES.items():
        if len(alias) < 4:
            continue
        if alias in lower or canonical.lower() in lower:
            return canonical
    if "realreal" in re.sub(r"[^a-z0-9]+", "", lower):
        return "query_stockmarket"
    if all(w in lower for w in ("decade", "rating", "book")) or (
        "publication" in lower and "rating" in lower and ("distinct" in lower or "average" in lower)
    ):
        return "query_bookreview"
    return None


# Challenge brief: multi-layer context (architecture + domain + corrections) — see repo docs.
DAB_CHALLENGE_ROUTER_HINT = (
    "DataAgentBench expects routing across PostgreSQL, MongoDB, SQLite, and DuckDB using real schemas and "
    "domain semantics — not a single default database. Use dab_candidates for machine-readable paths and "
    "live_schema; use kb_layers for join keys and column meaning."
)


def extract_join_key_glossary_section_for_dataset(
    repo_root: Path, canonical_dataset: Optional[str]
) -> str:
    """
    Per-dataset row under ## Per-Dataset Join Keys in kb/domain/join_key_glossary.md.
    Matches headings like '### Book Reviews (query_bookreview)' when canonical_dataset is query_bookreview.
    """
    if not canonical_dataset:
        return ""
    path = repo_root / "kb" / "domain" / "join_key_glossary.md"
    if not path.exists():
        return ""
    needle = canonical_dataset.strip().lower()
    lines = path.read_text(encoding="utf-8").splitlines()
    out: List[str] = []
    capture = False
    for line in lines:
        if line.startswith("### "):
            if capture:
                break
            rest = line[4:].strip().lower()
            if needle in rest:
                capture = True
        elif capture and line.startswith("## ") and not line.startswith("###"):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def build_agent_session_kb_context(
    user_question: str,
    repo_root: Optional[Path] = None,
    *,
    max_domain_chars: int = 6000,
    corrections_tail_lines: int = 80,
) -> str:
    """
    Knowledge loaded for this agent request from kb/ (challenge: architecture + domain + corrections;
    see kb/domain/kb_v2_domain.md). Used after toolbox steps to answer without hardcoded task logic.
    """
    root = _resolve_repo_root(repo_root)
    ds = infer_canonical_dataset_from_question(user_question)
    layers = build_context_layers(
        dataset=ds,
        user_question=user_question,
        repo_root=root,
        max_layer_chars=max_domain_chars,
        corrections_tail_lines=corrections_tail_lines,
    )
    jk = extract_join_key_glossary_section_for_dataset(root, ds)
    chunks: List[str] = [
        "### Architecture layer (kb/architecture)\n" + layers.layer_1_architecture,
    ]
    if jk:
        chunks.append("### Join key glossary (dataset-scoped row)\n" + jk)
    chunks.append("### Domain layer (kb/domain)\n" + layers.layer_2_domain)
    chunks.append("### Corrections memory (kb/corrections)\n" + layers.layer_3_corrections)
    return "\n\n".join(chunks).strip()


def build_router_planner_user_payload(
    user_question: str,
    route_candidates_compact: Dict[str, Any],
    repo_root: Optional[Path] = None,
    *,
    max_kb_layer_chars: int = 3200,
    corrections_tail_lines: int = 80,
) -> Dict[str, Any]:
    """
    Planner message: dab_candidates + KB from disk (kb/architecture, kb/domain, kb/corrections).
    Aligns with kb/domain/kb_v2_domain.md and three-layer context; not hardcoded task answers.
    """
    root = _resolve_repo_root(repo_root)
    dataset = infer_canonical_dataset_from_question(user_question)
    layers = build_context_layers(
        dataset=dataset,
        user_question=user_question,
        repo_root=repo_root,
        max_layer_chars=max_kb_layer_chars,
        corrections_tail_lines=corrections_tail_lines,
    )
    payload: Dict[str, Any] = {
        "question": user_question,
        "dab_candidates": route_candidates_compact,
        "kb_layers": {
            "architecture": layers.layer_1_architecture,
            "domain": layers.layer_2_domain,
            "corrections": layers.layer_3_corrections,
        },
        "kb_warnings": layers.warnings,
        "dataset_hint_for_kb": dataset,
        "challenge_alignment": DAB_CHALLENGE_ROUTER_HINT,
    }
    jk = extract_join_key_glossary_section_for_dataset(root, dataset)
    if jk:
        payload["kb_focus"] = {"join_key_glossary_dataset_section": jk}
    return payload


if __name__ == "__main__":
    sample = build_context_layers(
        dataset="query_yelp",
        user_question="Which businesses have highest average rating by city?",
    )
    print(sample.system_prompt[:2000])
    if sample.warnings:
        print("\nWARNINGS:")
        for w in sample.warnings:
            print(f"- {w}")
