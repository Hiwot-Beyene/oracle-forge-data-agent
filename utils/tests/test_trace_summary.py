from utils.trace_summary import tool_failures_in_messages, tool_steps_from_messages


def test_tool_steps_from_messages_extracts_query_db():
    messages = [
        {"role": "assistant", "tool_calls": [{"id": "1", "function": {"name": "query_db", "arguments": "{}"}}]},
    ]
    steps = tool_steps_from_messages(messages)
    assert len(steps) == 1
    assert steps[0]["tool"] == "query_db"


def test_tool_failures_in_messages_detects_failed_tool_content():
    messages = [
        {"role": "tool", "content": "The tool query_db execution failed.\nError: oops"},
    ]
    assert tool_failures_in_messages(messages) is True
