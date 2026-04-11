# Claude Code three-layer memory architecture

## What this is

This document describes the memory system extracted from the Claude Code source snapshot (March 2026 leak, ~512,000 lines of TypeScript). This architecture is the direct model for how the Oracle Forge agent manages its own context across sessions.

## The three memory layers

### Layer 1 — MEMORY.md index (~200 tokens, always loaded)

- MEMORY.md is a small index file. It is not a knowledge document.
- It lists every other KB document by name with a one-sentence description of what that document contains.
- The agent reads MEMORY.md first at session start, before the question arrives.
- MEMORY.md is used to decide which topic files to load next, based on the question.
- MEMORY.md is approximately 200 tokens. This limit is deliberate.
- Growing MEMORY.md beyond 200 tokens defeats its purpose as an index. It becomes a topic document masquerading as an index and wastes mandatory context budget before any question-specific loading begins.
- Source: `src/memdir/`

### Layer 2 — Topic files (~300-400 tokens each, loaded on demand)

- Topic files contain the actual knowledge for a specific subject — tool scoping, schema details, business terms, join key glossaries.
- Topic files are loaded only when the MEMORY.md index indicates they are relevant to the current question.
- Never load all topic files upfront. Loading is selective and on-demand.
- Source: `src/services/extractMemories/` (auto-extracts memories and writes to topic files), `src/services/teamMemorySync/` (synchronizes across team members).

### Layer 3 — Session transcripts (searched, never pre-loaded)

- Session transcripts are logs of past agent runs.
- They record which queries were asked, what tools were called, what results came back, and what the final answer was.
- Session transcripts are stored in `.claude/sessions/`.
- Session transcripts are never pre-loaded into context. Pre-loading is expensive. Most sessions do not need them.
- The agent searches transcripts only when a new question closely resembles a past one. Searching is cheap; pre-loading is expensive.
- The never-pre-load discipline is enforced by context window budget management in `src/QueryEngine.ts` (~46K lines). This is the specific file responsible for enforcing it.

## The autoDream consolidation pattern

- Source: `src/tasks/DreamTask/` and `src/services/autoDream/`. These are the two specific directories that implement autoDream.
- autoDream is a background process. It runs after sessions end — not during sessions. Never during sessions.
- It reviews what was learned during the session: corrections made, successful query patterns, new business term definitions discovered.
- It consolidates learnings back into the relevant topic files.
- It removes old, superseded information from topic files.
- After consolidation, the topic file is smaller and more precise than before the session.
- This prevents the KB from growing into noise.

**Consolidation trigger thresholds from the source code:**

- User corrects the same pattern 3+ times → write to MEMORY.md
- Agent successfully uses a pattern 5+ times → promote to a topic file
- Topic file grows beyond 500 words → split into subtopics

**Oracle Forge equivalent of autoDream:**

- After agent runs, review `kb/corrections/log.md`
- Absorb verified fixes into the relevant `kb/domain/` documents
- Remove absorbed entries from the corrections log
- This is the manual Oracle Forge equivalent of the autoDream loop

## Tool scoping philosophy (40+ tools, tight domain boundaries)

- Source: `src/tools/` (~40 tool implementations), `src/Tool.ts` (~29K lines).
- Rule: each tool has a single tight responsibility. One tool, one responsibility, one domain boundary.
- A tool that does one thing precisely is more reliable than a tool doing multiple things loosely.
- When a tool fails, the agent knows exactly which tool failed and why.
- Tight domain boundaries make failures diagnosable and recoverable.
- This is why the Oracle Forge agent uses separate tools per database type — not a single "query database" tool that switches internally.

## Worktree sub-agent spawn modes

- Source: `src/tools/EnterWorktreeTool.ts`, `src/tools/ExitWorktreeTool.ts`, `src/coordinator/`.
- Claude Code spawns sub-agents into isolated git worktrees for parallel experiments.
- The Coordinator (`src/coordinator/coordinatorMode.ts`) orchestrates sub-agents and merges outputs.
- For Oracle Forge: multiple trial runs of the same query run in isolation and results are aggregated by the harness.

## What this does NOT cover

The OpenAI six-layer context design is in openai_agent_context.md. The Oracle Forge KB structure rules are in kb_v1_architecture.md. Database tool routing specifics are in tool_scoping.md.

---

Injection test: "What is the purpose of MEMORY.md in Claude Code's memory system, and how does autoDream relate to it?"
Expected answer: MEMORY.md is a small index file (~200 tokens) that lists all topic files and their one-sentence descriptions. The agent reads it first at session start to know what knowledge exists, then loads only the relevant topic files on demand. autoDream is a background process that runs after sessions end — it consolidates learnings from the session back into topic files, removes outdated information, and keeps topic files minimal and precise. For Oracle Forge, autoDream means absorbing verified corrections from kb/corrections/log.md into kb/domain/ documents after each agent run, then removing those entries from the log.
Token count: ~430 tokens
Last verified: 2026-04-11
