from pathlib import Path

from utils.toolbox_config import merged_toolbox_tools, resolved_toolbox_config_paths


def test_resolved_paths_include_generated_yaml_when_present():
    root = Path(__file__).resolve().parents[2]
    paths = resolved_toolbox_config_paths(root)
    assert paths, "expected at least one toolbox yaml path"
    assert all(p.suffix in (".yaml", ".yml") for p in paths)


def test_merged_tools_non_empty_in_repo():
    root = Path(__file__).resolve().parents[2]
    tools = merged_toolbox_tools(root)
    assert len(tools) >= 1