"""
Oracle Forge — KB Evaluation Injection Test Runner
====================================================
Production-grade injection test runner for KB evaluation documents.
Every expected answer is a checklist of required concepts.
Score = (concepts present / total concepts) * 100.
100/100 requires every required concept present and nothing contradicted.

Usage:
    python3 run_injection_tests.py                           # run all evaluation tests
    python3 run_injection_tests.py --doc dab_overview        # run one document
    python3 run_injection_tests.py --doc failure_taxonomy

Requirements:
    pip3 install openai python-dotenv

Environment:
    OPENROUTER_API_KEY in repo-root .env, DataAgentBench/.env, or exported.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
KB_EVAL_DIR = SCRIPT_DIR.parent
REPO_ROOT = KB_EVAL_DIR.parent.parent

for candidate in [
    REPO_ROOT / ".env",
    REPO_ROOT / "DataAgentBench" / ".env",
    Path("/DataAgentBench/.env"),
    Path(".env"),
]:
    if candidate.exists():
        load_dotenv(candidate)
        break

# ── OpenRouter client ───────────────────────────────────────────────────────
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    sys.exit(
        "ERROR: OPENROUTER_API_KEY not set.\n"
        "Add it to your .env file:\n  OPENROUTER_API_KEY=sk-or-v1-..."
    )

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/team-mistral/oracle-forge",
        "X-Title": "Oracle Forge KB Evaluation Injection Tests",
    },
)

MODEL = os.getenv("INJECTION_TEST_MODEL", "google/gemini-2.0-flash-001")

# ── document registry ───────────────────────────────────────────────────────
DOCUMENTS = {
    "dab_overview": {
        "doc_file":  KB_EVAL_DIR / "dab_overview.md",
        "test_file": SCRIPT_DIR / "dab_overview_test.md",
        "priority":  1,
    },
    "failure_taxonomy": {
        "doc_file":  KB_EVAL_DIR / "failure_taxonomy.md",
        "test_file": SCRIPT_DIR / "failure_taxonomy_test.md",
        "priority":  2,
    },
}


def load_document(path: Path) -> str:
    if not path.exists():
        sys.exit(f"ERROR: Document not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def extract_qa_pairs(test_content: str) -> list[dict]:
    """
    Parse structured Q&A blocks from test file.
    Each block must follow this format:

        ### Question N
        "question text"

        Required concepts:
        - concept one
        - concept two

        Forbidden contradictions:
        - contradiction one
    """
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
    """Injection test call — document is the ONLY context."""
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": (
                    "The following is the ONLY document you have access to. "
                    "Answer the question using ONLY the information in this document. "
                    "Do not use any external knowledge or assumptions.\n\n"
                    f"DOCUMENT:\n{document_text}\n\n"
                    f"QUESTION:\n{question}"
                ),
            }
        ],
    )
    return response.choices[0].message.content.strip()


def grade_with_rubric(question: str, actual: str,
                      concepts: list[str], forbidden: list[str]) -> dict:
    """
    Structured rubric grader.
    Score = concepts_present / total_concepts * 100
    Any forbidden contradiction immediately caps score at 50.
    """
    concepts_json = json.dumps(concepts)
    forbidden_json = json.dumps(forbidden)

    grader_prompt = f"""You are a strict technical grader for a knowledge base injection test.

QUESTION ASKED:
{question}

ACTUAL ANSWER TO GRADE:
{actual}

YOUR TASK:
Check the actual answer against this exact checklist.

REQUIRED CONCEPTS (every one must be present for 100/100):
{concepts_json}

FORBIDDEN CONTRADICTIONS (any one present caps score at 50/100):
{forbidden_json}

GRADING RULES:
1. For each required concept, check if the actual answer contains that concept — even if worded differently.
2. Concept is PRESENT if the core fact is clearly stated. Concept is MISSING if it is absent or only vaguely implied.
3. Score = (concepts_present / total_concepts) * 100, rounded to nearest integer.
4. If any forbidden contradiction is present in the actual answer, cap score at 50 regardless of concepts found.
5. Do not give partial credit for vague mentions — the concept must be clearly stated.

Respond with valid JSON only. No markdown, no explanation outside the JSON:
{{
  "concepts_found": ["list each required concept that is clearly present"],
  "concepts_missing": ["list each required concept that is absent or only vaguely implied"],
  "contradictions_found": ["list any forbidden contradictions present in the actual answer"],
  "score": <integer 0-100>,
  "reasoning": "one sentence explaining the score"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": grader_prompt}],
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        result = json.loads(raw)
        n_required = len(concepts)
        n_found = len(result.get("concepts_found", []))
        n_forbidden = len(result.get("contradictions_found", []))
        if n_required > 0:
            calculated = round((n_found / n_required) * 100)
            if n_forbidden > 0:
                calculated = min(calculated, 50)
            result["score"] = calculated
        return result
    except (json.JSONDecodeError, KeyError):
        return {
            "concepts_found":       [],
            "concepts_missing":     concepts,
            "contradictions_found": [],
            "score":                0,
            "reasoning":            f"Grader returned unparseable output: {raw[:200]}",
        }


def write_results(test_file: Path, results: list[dict], doc_key: str) -> None:
    """Write rubric results into the ## Test result section of the test file."""
    content = test_file.read_text(encoding="utf-8")
    marker = "## Test result"
    if marker in content:
        content = content[: content.index(marker)].rstrip()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    all_pass = all(r["grade"]["score"] == 100 for r in results)
    avg_score = round(sum(r["grade"]["score"]
                      for r in results) / len(results), 1)
    overall = "PASS" if all_pass else "FAIL"

    lines = [
        "",
        "## Test result",
        "",
        f"**Run timestamp:** {timestamp}",
        f"**Model used:** {MODEL}",
        f"**Document tested:** kb/evaluation/{doc_key}.md",
        f"**Overall result:** {overall}",
        f"**Average score:** {avg_score}/100",
        "",
    ]

    for i, r in enumerate(results, start=1):
        g = r["grade"]
        status = "PASS" if g["score"] == 100 else "FAIL"
        lines += [
            f"### Question {i} — {status} ({g['score']}/100)",
            "",
            f"**Question:** {r['question']}",
            "",
            f"**Concepts found ({len(g['concepts_found'])}/{len(r['concepts'])}):**",
        ]
        for c in g["concepts_found"]:
            lines.append(f"  - [x] {c}")
        if g["concepts_missing"]:
            lines.append("")
            lines.append(f"**Concepts missing:**")
            for c in g["concepts_missing"]:
                lines.append(f"  - [ ] {c}")
        if g["contradictions_found"]:
            lines.append("")
            lines.append("**Contradictions found (score capped at 50):**")
            for c in g["contradictions_found"]:
                lines.append(f"  - [!] {c}")
        lines += [
            "",
            f"**Actual answer:**",
            r["actual"],
            "",
            f"**Grader reasoning:** {g['reasoning']}",
            "",
            "---",
            "",
        ]

    test_file.write_text(content + "\n" + "\n".join(lines), encoding="utf-8")
    print(f"  Results written -> {test_file.name}")


def run_test_for_document(doc_key: str) -> bool:
    entry = DOCUMENTS[doc_key]
    doc_file = entry["doc_file"]
    test_file = entry["test_file"]

    print(f"\n{'='*60}")
    print(f"Testing: {doc_key}")
    print(f"  Document : {doc_file}")
    print(f"  Test file: {test_file}")

    if not test_file.exists():
        print(f"  SKIP: test file not found")
        return True

    doc_text = load_document(doc_file)
    test_text = test_file.read_text(encoding="utf-8")
    qa_pairs = extract_qa_pairs(test_text)

    if not qa_pairs:
        print("  SKIP: no Q&A pairs with 'Required concepts' found")
        return True

    print(f"  Found {len(qa_pairs)} test question(s). Running in parallel...")

    def _run_one(idx_pair):
        idx, pair = idx_pair
        actual = call_openrouter(doc_text, pair["question"])
        grade = grade_with_rubric(
            pair["question"], actual,
            pair["concepts"], pair["forbidden"]
        )
        return idx, pair, actual, grade

    results = [None] * len(qa_pairs)
    with ThreadPoolExecutor(max_workers=len(qa_pairs)) as executor:
        futures = {executor.submit(_run_one, (i, p)): i
                   for i, p in enumerate(qa_pairs)}
        for future in as_completed(futures):
            idx, pair, actual, grade = future.result()
            n_req = len(pair["concepts"])
            n_fnd = len(grade["concepts_found"])
            print(f"  Q{idx+1}: {pair['question'][:80]}...")
            print(
                f"       -> {grade['score']}/100  concepts: {n_fnd}/{n_req}  contradictions: {len(grade['contradictions_found'])}")
            results[idx] = {
                "question": pair["question"],
                "concepts": pair["concepts"],
                "actual":   actual,
                "grade":    grade,
            }

    write_results(test_file, results, doc_key)
    return all(r["grade"]["score"] == 100 for r in results)


def main():
    parser = argparse.ArgumentParser(
        description="Oracle Forge KB Evaluation injection test runner")
    parser.add_argument("--doc", choices=list(DOCUMENTS.keys()), default=None)
    args = parser.parse_args()

    print("Oracle Forge — KB Evaluation Injection Test Runner (rubric grading)")
    print(f"Model     : {MODEL}")
    print(f"Timestamp : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    targets = [args.doc] if args.doc else sorted(
        DOCUMENTS.keys(), key=lambda k: DOCUMENTS[k]["priority"]
    )

    passed, failed = [], []
    for doc_key in targets:
        ok = run_test_for_document(doc_key)
        (passed if ok else failed).append(doc_key)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Passed : {len(passed)} — {passed}")
    print(f"  Failed : {len(failed)} — {failed}")

    if failed:
        print("\nFailed documents must be revised before committing.")
        for f in failed:
            print(f"  python3 run_injection_tests.py --doc {f}")
        sys.exit(1)
    else:
        print("\nAll evaluation injection tests passed at 100/100.")


if __name__ == "__main__":
    main()
