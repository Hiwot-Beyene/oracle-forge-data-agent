# Shared Utility Library

## Purpose
Reusable modules for DAB agent development. All utilities are documented, tested, and designed to be used by any team member.

## Modules
### 1. Multi-Pass Retrieval Helper (`multi_pass_retrieval.py`)
Progressive context enrichment based on Claude Code's hierarchical memory pattern.

**Usage:**
```python
from utils.multi_pass_retrieval import iterative_query_refinement

answer, history = iterative_query_refinement(
    agent=my_agent,
    dataset='yelp',
    query_text='Average stars for businesses with >10 reviews'
)
```

### 2. Schema Introspector (`schema_introspector.py`)
Intelligent schema navigation to prevent context window bloat.

**Usage:**
```python
from utils.schema_introspector import get_relevant_tables, generate_schema_prompt

tables = get_relevant_tables('crmarenapro', 'customer revenue by ticket count')
prompt = generate_schema_prompt('crmarenapro', 'customer revenue by ticket count')
```

### 3. Join Key Resolver (`join_key_resolver.py`)
Cross-database join key format conversions.

**Usage:**
```python
from utils.join_key_resolver import normalize_key, detect_format_mismatch

# Convert "CUST-00123" (SQLite) to 123 (PostgreSQL)
customer_id = normalize_key("CUST-00123", "sqlite", "postgres", "customer_id")
```

### 4. Benchmark Harness Wrapper (`benchmark_harness_wrapper.py`)
Standardized DAB query execution with full tracing.

**Usage:**
```python
from utils.benchmark_wrapper import run_dab_query, compute_pass_at_1

traces = run_dab_query(agent=my_agent, dataset='yelp', query_id='1', trials=50)
score = compute_pass_at_1('yelp')
```

## Installation
```bash
# From oracle-forge root
pip install -e utils/
```

## Testing
```bash
cd utils
python -m pytest tests/
```

## Dependencies
- Python 3.12+
- pandas (for benchmark harness)
- pytest (for testing)

## Adding New Utilities
1. Create module in `utils/`
2. Add tests in `utils/tests/`
3. Update this README
4. Submit for mob session review

## Maintenance
**Owner:** Intelligence Officers
**Updates:** When new patterns discovered or DAB schema changes
**Approval:** Mob session required for modifications
