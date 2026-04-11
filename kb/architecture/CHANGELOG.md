# Changelog - Architecture KB

All notable architectural changes and document migrations will be documented in this file.

## [1.2.0] - 2026-04-11
### Added
- **Automated Verification**: Integrated `run_injection_tests.py` for rubric-based document grading.
- **Rubric Test Specs**: Replaced manual templates with structured "Required Concept" rubrics in `injection_tests/`.
- **DAB Failure Scenarios**: Added specific Join Key (PG/Mongo) and Business Term (Active Customer) examples.
- **Codebase Precision**: Added specific `src/` paths and line counts (e.g., `QueryEngine.ts`) from reference architecture leaks.

### Changed
- Unified modular documents in Agent 1 with the technical depth of Agent 2's master files.
- Upgraded `README.md` to enforce the Karpathy Method (minimum content, maximum precision).
- Synchronized token budgets across system overview and index documents.

### Removed
- Redundant manual test template `test_combined.md`.
