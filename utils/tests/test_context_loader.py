from pathlib import Path

from agent.context_loader import (
    build_context_layers,
    build_router_planner_user_payload,
    extract_join_key_glossary_section_for_dataset,
    infer_dataset_hint_for_question,
)


def test_join_key_glossary_excerpt_for_dataset():
    root = Path(__file__).resolve().parents[2]
    ex = extract_join_key_glossary_section_for_dataset(root, "query_bookreview")
    assert "book_id" in ex and "purchase_id" in ex


def test_router_payload_includes_kb_focus_from_join_glossary():
    payload = build_router_planner_user_payload(
        "What is the average rating for books grouped by publication year?",
        {"toolbox_tools": []},
    )
    assert payload.get("dataset_hint_for_kb") == "query_bookreview"


def test_infer_routes_stockindex_up_days_question():
    hint = infer_dataset_hint_for_question(
        "Among North American stock indices, which indices had more up days than down days in 2018?"
    )
    assert hint == "query_stockindex"


def test_router_payload_stockindex_injects_domain_and_forge():
    payload = build_router_planner_user_payload(
        "If an investor had made regular monthly investments in all indices since 2000, "
        "which 5 indices would have produced the highest overall returns?",
        {"toolbox_tools": []},
    )
    assert payload.get("dataset_hint_for_kb") == "query_stockindex"
    dom = payload["kb_layers"]["domain"]
    assert "Oracle Forge" in dom or "session injection" in dom
    assert "index_trade" in dom.lower() or "Index" in dom


def test_router_payload_yelp_user_cohort_question():
    payload = build_router_planner_user_payload(
        "Which 5 business categories had the most total reviews from users who registered on Yelp in 2016, "
        "for reviews written since 2016-01-01?",
        {"toolbox_tools": []},
    )
    assert payload.get("dataset_hint_for_kb") == "query_yelp"


def test_router_payload_yelp_wifi_question_not_bookreview():
    payload = build_router_planner_user_payload(
        "Which U.S. state has the highest number of businesses that offer WiFi, "
        "and what is the average rating for those businesses?",
        {"toolbox_tools": []},
    )
    assert payload.get("dataset_hint_for_kb") == "query_yelp"
    assert "kb_focus" in payload
    jk = payload["kb_focus"]["join_key_glossary_dataset_section"]
    assert "business_id" in jk or "business_ref" in jk


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
        repo_root=Path(__file__).resolve().parents[2],
    )
    assert "KB v1" in context.layer_1_architecture or "kb/architecture" in context.layer_1_architecture
    assert "Oracle Forge" in context.layer_2_domain or "session injection" in context.layer_2_domain
    assert "Book Reviews" in context.layer_2_domain
    assert "book_id" in context.layer_2_domain.lower() or "purchase_id" in context.layer_2_domain.lower()
    assert context.system_prompt


def test_build_context_layers_handles_missing_corrections():
    context = build_context_layers(
        dataset="query_yelp",
        user_question="Top cities by rating?",
    )
    assert context.layer_3_corrections


def test_yelp_state_review_question_includes_forge_transport_hints():
    q = (
        "Which U.S. state has the highest number of reviews, and what is the average rating "
        "of businesses in that state?"
    )
    context = build_context_layers(
        dataset="query_yelp",
        user_question=q,
        repo_root=Path(__file__).resolve().parents[2],
    )
    assert "Oracle Forge" in context.layer_2_domain or "session injection" in context.layer_2_domain
    assert "var_tool_query_db" in context.layer_2_domain or "var_tool_" in context.layer_2_domain


def test_yelp_user_cohort_injects_hint():
    q = (
        "Which 5 business categories had the most total reviews from users who registered on Yelp in 2016?"
    )
    context = build_context_layers(
        dataset="query_yelp",
        user_question=q,
        repo_root=Path(__file__).resolve().parents[2],
    )
    assert "yelping_since" in context.layer_2_domain.lower() or "user.yelping_since" in context.layer_2_domain


def test_build_context_layers_stockindex_join_glossary():
    context = build_context_layers(
        dataset="query_stockindex",
        user_question="North American indices up days 2018",
        repo_root=Path(__file__).resolve().parents[2],
    )
    assert "Oracle Forge" in context.layer_2_domain or "session injection" in context.layer_2_domain
    assert "query_stockindex" in context.layer_2_domain or "index_trade" in context.layer_2_domain.lower()
