# Adversarial Probe Library

## Purpose
This directory contains structured queries designed to expose specific failure modes in the DAB data agent. Each probe targets one of DAB's four hard requirement categories.

## Structure
```
probes/
├── README.md                           # This file
├── probes.md                           # Complete probe library (all probes)
├── category_1_multi_db_routing.md      # Category 1 probes only
├── category_2_ill_formatted_keys.md    # Category 2 probes only
├── category_3_unstructured_text.md     # Category 3 probes only
├── category_4_domain_knowledge.md      # Category 4 probes only
└── results/
    ├── baseline_scores.json            # Initial run scores
    ├── fixed_scores.json               # Post-fix scores
    └── improvement_log.md              # Sprint-by-sprint progress
```

## Using the Probe Library

### 1. Run Baseline
```bash
python probes/run_probes.py --update-docs
```

### 2. Analyze Failures
Review `results/baseline_scores.json` to identify failure patterns.

### 3. Apply Fixes
Update KB documents or agent code based on failure categories.

### 4. Verify Fixes
```bash
python probes/run_probes.py --update-docs --mode fixed
```

### 5. Document Improvement
Update `results/fixed_scores.json` and `improvement_log.md`.

## Probe Format
Each probe follows this structure:
- **Category:** One of the four DAB requirements
- **Dataset:** Which DAB dataset to use
- **Query:** Natural language query
- **Expected Failure:** What should go wrong
- **Observed Failure:** What actually went wrong (filled after run)
- **Fix Applied:** What changed (filled after fix)
- **Score Before/After:** Quantitative improvement

## Maintenance
**Owner:** Intelligence Officers
**Updates:** When new failure patterns discovered
**Review:** Weekly mob session
