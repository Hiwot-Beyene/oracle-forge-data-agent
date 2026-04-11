# Claude Code — autoDream Memory Consolidation

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: Claude Code npm leak, March 31 2026_

### The Consolidation Pattern

**autoDream** is a background process that runs **after** sessions end — never during a live session. It reviews what was learned (corrections, query patterns, business terms) and consolidates them back into the relevant topic files.

### Engineering Details

- **Source Code**: `src/tasks/DreamTask/` and `src/services/autoDream/`.
- **Mechanism**: It removes old, superseded information. The topic file after consolidation is **smaller and more precise** than before the session.
- **DAB Application**: Review the `kb/corrections/log.md` after agent runs, absorb verified fixes into domain documents (like `kb/domain/schemas.md`), and remove those entries from the corrections log once absorbed.

### Key Logic

If a correction exists in the log, autoDream verifies it in the next "dream" cycle. If the correction makes a topic file more accurate, it is merged. This prevents the KB from growing into noise. This is the mechanism that prevents the knowledge base from expanding indefinitely and becoming overwhelming.

### Key Insight

**Knowledge is a garden, not a dumpster.** If you do not prune the corrections log into the main schema documents, the agent will eventually become confused by too many conflicting "don't do X" rules. Pruning outdated or inaccurate information is as important as adding new facts.

---
### ⚙️ Injection Test Verification
- **Test Question:** "What is autoDream and when does it run?"
- **Expected Outcome:** Correct identification as a background consolidation process that runs after sessions.
- **Last Status:** 
- **Verified On:** 2026-04-11
- **Test Specification:** claude_autodream_test.md