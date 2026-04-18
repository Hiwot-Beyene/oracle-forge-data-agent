# Shared utilities (Oracle Forge)

Small, testable modules used by `app.py`, `eval/`, and scripts. The challenge checklist expects a `utils/` library with documented entrypoints.

## Modules

| Module | Purpose |
|--------|---------|
| `dab_paths.py` | Resolve `DAB_ROOT`, DAB `.env`, and default Yelp DuckDB path via environment overrides. |
| `toolbox_config.py` | Merge MCP toolbox YAML files (`MCP_TOOLBOX_CONFIGS` or default `tools_dab_generated.yaml`), list SQL tool names, read tool `kind`. |
| `trace_summary.py` | Build tool-step summaries and failure heuristics from DataAgent `messages` (used by `eval/challenge_contract.py`). |

## Examples

```python
from pathlib import Path
from utils.dab_paths import dab_root
from utils.toolbox_config import merged_toolbox_tools, resolved_toolbox_config_paths
from utils.trace_summary import tool_steps_from_messages

print(dab_root())
print(resolved_toolbox_config_paths(Path(".")))
tools = merged_toolbox_tools()
print(len(tools), "toolbox tools merged")
```

## Tests

```bash
cd /path/to/oracle-forge-data-agent
python3 -m pytest utils/tests/ -q
```
