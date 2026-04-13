"""
Oracle Forge — Unified KB Injection Test Runner
===============================================
Pedantic rubric-based testing for modular architecture docs.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
KB_ARCH_DIR = SCRIPT_DIR.parent
REPO_ROOT = KB_ARCH_DIR.parent.parent

# Load environment
for candidate in [REPO_ROOT / ".env", Path(".env")]:
    if candidate.exists():
        load_dotenv(candidate)
        break

# ── OpenRouter client ───────────────────────────────────────────────────────
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    API_KEY = "sk-placeholder"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/team-mistral/oracle-forge",
        "X-Title": "Oracle Forge Unified KB Tests",
    },
)

MODEL = os.getenv("INJECTION_TEST_MODEL", "anthropic/claude-3.7-sonnet")

# ── document registry ───────────────────────────────────────────────────────
DOCUMENTS = {
    "system_overview": {
        "doc_file":  KB_ARCH_DIR / "architecture_system_overview.md",
        "test_file": SCRIPT_DIR / "architecture_system_overview_test.md",
        "priority":  1,
    },
    "claude_memory": {
        "doc_file":  KB_ARCH_DIR / "claude_memory_layers.md",
        "test_file": SCRIPT_DIR / "claude_memory_layers_test.md",
        "priority":  2,
    },
    "claude_autodream": {
        "doc_file":  KB_ARCH_DIR / "claude_autodream.md",
        "test_file": SCRIPT_DIR / "claude_autodream_test.md",
        "priority":  3,
    },
    "tool_scoping": {
        "doc_file":  KB_ARCH_DIR / "claude_tool_scoping.md",
        "test_file": SCRIPT_DIR / "claude_tool_scoping_test.md",
        "priority":  4,
    },
    "openai_context": {
        "doc_file":  KB_ARCH_DIR / "openai_six_layers.md",
        "test_file": SCRIPT_DIR / "openai_six_layers_test.md",
        "priority":  5,
    },
    "openai_enrichment": {
        "doc_file":  KB_ARCH_DIR / "openai_table_enrichment.md",
        "test_file": SCRIPT_DIR / "openai_table_enrichment_test.md",
        "priority":  6,
    },
}


def load_document(path: Path) -> str:
    if not path.exists():
        sys.exit(f"ERROR: Document not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def extract_qa_pairs(test_content: str) -> list[dict]:
    pairs = []
    blocks = re.split(r"### Question \d+", test_content)
    for block in blocks[1:]:
        q_match = re.search(r'"(.+?)"', block, re.DOTALL)
        concepts_match = re.search(
            r"Required concepts:\s*\n((?:\s*-[^\n]+\n?)+)", block
        )
        forbidden_match = re.search(
            r"Forbidden contradictions:\s*\n((?:\s*-[^\n]+\n?)+)", block
        )
        if not q_match or not concepts_match:
            continue

        concepts = [
            c.strip().lstrip("- ").strip()
            for c in concepts_match.group(1).strip().splitlines()
            if c.strip().startswith("-")
        ]
        forbidden = []
        if forbidden_match:
            forbidden = [
                c.strip().lstrip("- ").strip()
                for c in forbidden_match.group(1).strip().splitlines()
                if c.strip().startswith("-")
            ]

        pairs.append({
            "question":  q_match.group(1).strip(),
            "concepts":  concepts,
            "forbidden": forbidden,
        })
    return pairs


def call_openrouter(document_text: str, question: str) -> str:
    if API_KEY == "sk-placeholder":
        return "ERROR: OPENROUTER_API_KEY NOT SET."
    
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": (
                    "The following is the ONLY document you have access to. "
                    "Answer the question using ONLY the information in this document.\n\n"
                    f"DOCUMENT:\n{document_text}\n\n"
                    f"QUESTION:\n{question}"
                ),
            }
        ],
    )
    return response.choices[0].message.content.strip()


def grade_with_rubric(question: str, actual: str,
                      concepts: list[str], forbidden: list[str]) -> dict:
    if API_KEY == "sk-placeholder":
        return {"score": 0, "reasoning": "No API Key", "concepts_found": [], "concepts_missing": concepts, "contradictions_found": []}

    concepts_json = json.dumps(concepts)
    forbidden_json = json.dumps(forbidden)

    grader_prompt = f"""You are a pedantic technical grader. Grade this answer against the REQUIRED CONCEPTS.
If a concept is clearly present in the answer (even in different words), it is FOUND.
If a concept is absent or only vaguely implied, it is MISSING.

QUESTION: {question}
ANSWER: {actual}

REQUIRED CONCEPTS (CHECKLIST): {concepts_json}
FORBIDDEN CONTRADICTIONS: {forbidden_json}

GRADING RULES:
1. Every required concept must be checked.
2. If any forbidden contradiction is present, the score is capped at 50.
3. If all required concepts are found and no forbidden content is present, the score MUST be 100.

Respond with valid JSON:
{{
  "concepts_found": ["list found concepts exactly as they appeared in the CHECKLIST"],
  "concepts_missing": ["list missing concepts exactly as they appeared in the CHECKLIST"],
  "contradictions_found": [],
  "score": <0-100 recalculated as (len(found)/len(required))*100>,
  "reasoning": "one sentence"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": grader_prompt}],
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        data = json.loads(raw)
        # Force strict score calculation
        total = len(concepts)
        found = len(data.get("concepts_found", []))
        score = round((found / total) * 100) if total > 0 else 100
        if len(data.get("contradictions_found", [])) > 0:
            score = min(score, 50)
        data["score"] = score
        return data
    except:
        return {"score": 0, "reasoning": "Grader Output Error", "concepts_found": [], "concepts_missing": concepts, "contradictions_found": []}


def write_results(test_file: Path, results: list[dict], doc_key: str) -> None:
    content = test_file.read_text(encoding="utf-8")
    marker = "## Test result"
    if marker in content:
        content = content[: content.index(marker)].rstrip()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["", "## Test result", "", f"**Run timestamp:** {timestamp}", f"**Document:** {doc_key}"]
    for i, r in enumerate(results, start=1):
        g = r["grade"]
        lines += [
            f"### Q{i}: {g['score']}/100",
            f"**Concepts found:**",
            *[f"  - [x] {c}" for c in g.get("concepts_found", [])],
            f"**Concepts missing:**",
            *[f"  - [ ] {c}" for c in g.get("concepts_missing", [])],
            f"**Actual answer:**",
            r["actual"],
            f"**Grader reasoning:** {g.get('reasoning', 'No reasoning provided')}",
            "---"
        ]

    test_file.write_text(content + "\n" + "\n".join(lines), encoding="utf-8")


def run_test_for_document(doc_key: str) -> bool:
    print(f"Testing {doc_key}...")
    entry = DOCUMENTS[doc_key]
    doc_text = load_document(entry["doc_file"])
    qa_pairs = extract_qa_pairs(entry["test_file"].read_text(encoding="utf-8"))
    
    results = []
    for pair in qa_pairs:
        actual = call_openrouter(doc_text, pair["question"])
        grade = grade_with_rubric(pair["question"], actual, pair["concepts"], pair["forbidden"])
        results.append({"question": pair["question"], "actual": actual, "grade": grade})
    
    write_results(entry["test_file"], results, doc_key)
    return all(r["grade"].get("score", 0) == 100 for r in results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", choices=list(DOCUMENTS.keys()))
    args = parser.parse_args()
    
    targets = [args.doc] if args.doc else sorted(DOCUMENTS.keys(), key=lambda k: DOCUMENTS[k]["priority"])
    for doc_key in targets:
        run_test_for_document(doc_key)

if __name__ == "__main__":
    main()
