from agent.context_loader import build_context_layers, build_router_planner_user_payload


def test_build_router_planner_user_payload_merges_dab_and_kb():
    payload = build_router_planner_user_payload(
        "Maximum adjusted close for RealReal in 2020",
        {"dab_key": "stub"},
    )
    assert payload["question"].startswith("Maximum")
    assert payload["dab_candidates"] == {"dab_key": "stub"}
    assert "architecture" in payload["kb_layers"]
    assert "domain" in payload["kb_layers"]
    assert "corrections" in payload["kb_layers"]


def test_build_context_layers_for_known_dataset():
    context = build_context_layers(
        dataset="query_bookreview",
        user_question="What is the average rating for english books?",
    )
    assert "MEMORY.md" in context.layer_1_architecture
    assert "Book Reviews" in context.layer_2_domain or "query_bookreview" in context.layer_2_domain
    assert context.system_prompt


def test_build_context_layers_handles_missing_corrections():
    context = build_context_layers(
        dataset="query_yelp",
        user_question="Top cities by rating?",
    )
    assert context.layer_3_corrections
