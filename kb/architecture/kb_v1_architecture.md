# Oracle Forge KB structure and discipline

## What this is

This document describes how the Oracle Forge Knowledge Base is organized, the rules that govern it, and the Karpathy method that keeps it from becoming noise.

## The four KB subdirectories

### kb/architecture/

- Contains documents about how the agent itself works: memory architecture, tool scoping rules, context loading order, this structural overview.
- Documents here are written for the agent about the agent.
- These documents change when the agent architecture changes — not when DAB datasets change.
- They do not change when new schemas are loaded or when domain terms shift.
- Files: MEMORY.md, tool_scoping.md, claude_code_memory.md, openai_agent_context.md, kb_v1_architecture.md.

### kb/domain/

- Contains documents about the data the agent works with: schema descriptions per DAB dataset, join key formats across database systems, unstructured field inventory, business term definitions.
- These documents change when datasets are loaded, when failure patterns reveal schema misunderstandings, or when domain terms are corrected after observed agent failures.
- Files: schemas.md, join_key_glossary.md, unstructured_fields.md, business_terms.md.

### kb/evaluation/

- Contains documents about how the agent is scored and what the benchmark requires: DAB query format, pass@1 scoring method, submission requirements, the four DAB failure categories.
- Files: dab_overview.md, failure_taxonomy.md.

### kb/corrections/

- The file is `kb/corrections/log.md`. This is the self-learning loop.
- It is written by Drivers after every observed agent failure.
- It is the running structured log of agent failures.
- Entry format: `[query that failed] → [what was wrong] → [correct approach]`.
- The agent reads the last 10 entries at session start.
- Intelligence Officers prune outdated entries when newer ones supersede them — entries absorbed into kb/domain/ documents are removed from the log.
- Files: log.md.

## The Karpathy method — minimum content, maximum precision

The Karpathy discipline is **removal, not accumulation**. These rules are absolute:

1. Every document must be minimal and precise.
2. Every document must pass an injection test before committing. This is not optional.
3. A document that has not passed an injection test must not be loaded by the agent under any circumstances.
4. Standard documentation practice grows over time by adding more content. The Karpathy method does the opposite — it shrinks documents by removing what is not proven to work.
5. Remove everything the LLM already knows from pretraining. Only include content specific to DAB, these databases, and this agent. Nothing general.
6. A KB that grows without being tested becomes noise that degrades the agent rather than helping it.
7. The test for every sentence: if the agent read only this sentence with no other context, could it take the correct action? If no — rewrite it or cut it.
8. Documents without a passing injection test result are treated as non-existent. The enforcement is absolute: untested documents must not be loaded by the agent.

## Injection test protocol

```
Step 1: Copy the full text of the document.
Step 2: Open a completely fresh LLM session — no other context, no system prompt.
Step 3: Paste the document as the only content the LLM has seen.
Step 4: Ask the test question written at the bottom of the document.
Step 5: Grade: correct answer = PASS. Wrong or incomplete = FAIL.
Step 6: Write result to kb/architecture/injection_tests/[document_name]_test.md.
```

- The test cannot be run with other documents in the context window. The document must be the only thing the model sees.
- A document without a passing test result has not been validated. It must not be loaded by the agent.

## Why MEMORY.md has the smallest token budget

- MEMORY.md is capped at ~200 tokens because it is a pointer, not a topic document.
- Its only job: list what other documents exist and what each one contains in one sentence.
- It is loaded at every session start before the question arrives.
- Every token MEMORY.md consumes comes directly out of the mandatory pre-load budget — before any question-specific loading begins.
- If MEMORY.md grows beyond ~200 tokens it becomes a topic document masquerading as an index.
- Growing MEMORY.md wastes mandatory context budget before any question-specific loading has started.
- Any content that belongs in a topic file must be moved to that file, not added to MEMORY.md.

## Token budget summary

| Document                         | Budget                     | Load when                      |
| -------------------------------- | -------------------------- | ------------------------------ |
| MEMORY.md                        | ~200 tok                   | Always first — mandatory       |
| tool_scoping.md                  | ~300 tok                   | Always second — mandatory      |
| corrections/log.md               | ~400 tok (last 10 entries) | Always third — mandatory       |
| claude_code_memory.md            | ~380 tok                   | On demand                      |
| openai_agent_context.md          | ~360 tok                   | On demand                      |
| kb_v1_architecture.md            | ~300 tok                   | On demand                      |
| schemas.md (per dataset section) | ~400 tok                   | After question received        |
| business_terms.md                | ~300 tok                   | If ambiguous language detected |

**Mandatory pre-load total: ~900 tokens.** Breakdown: tool_scoping.md 300 + corrections/log.md 400 + MEMORY.md 200.

**Optional post-question maximum: ~700 tokens.** This covers all post-question loads combined — not each separately.

**Total maximum across a full session: ~1,600 tokens.**

## What this does NOT cover

Specific database tool assignments are in tool_scoping.md. Domain schemas and join keys are in kb/domain/. Agent failure corrections are in kb/corrections/.

---

Injection test: "What are the four KB subdirectories in the Oracle Forge project and what does each one contain?"
Expected answer: kb/architecture/ contains documents about how the agent works (memory system, tool scoping, context loading). kb/domain/ contains documents about the data (schemas, join keys, business terms). kb/evaluation/ contains documents about scoring and the benchmark. kb/corrections/ contains the running log of agent failures and their fixes, read at every session start.
Token count: ~360 tokens
Last verified: 2026-04-11
