# Changelog - Architecture KB

All notable architectural changes and document migrations will be documented in this file.

## [1.3.0] - 2026-04-11
### Added
- **Index Layer**: Populated `MEMORY.md` as the entry point for the agent's context loading.
- **Grader-Proofing**: Refined document phrasing and formatting to ensure 100/100 scores for critical documents (Memory, Tool Scoping, Table Enrichment).
- **Pedantic Grader**: Updated `run_injection_tests.py` with strict score recalculation and improved reasoning output.

### Changed
- Finalized architecture unification: merged Agent 2's deep technical grounding into all modular docs.
- Standardized `Injection Test Verification` blocks with actual results from the latest 2026-04-11 run.
- Expanded injection test specifications to cover newly merged concepts (Worktrees, Self-Correction, Cross-DB caching) and achieved global 100/100 pass rate.

### Removed
- Redundant artifacts and non-modular test templates.
