from __future__ import annotations

import argparse
from dataclasses import dataclass

from agent.context_loader import ContextLayers, build_context_layers


@dataclass
class AgentRequest:
    dataset: str
    question: str


def prepare_context(request: AgentRequest) -> ContextLayers:
    return build_context_layers(
        dataset=request.dataset,
        user_question=request.question,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Oracle Forge agent context bootstrap.")
    parser.add_argument("--dataset", required=True, help="Target dataset name (e.g. query_yelp)")
    parser.add_argument("--question", required=True, help="User analytics question")
    parser.add_argument(
        "--print-layers",
        action="store_true",
        help="Print each context layer for debugging",
    )
    args = parser.parse_args()

    request = AgentRequest(dataset=args.dataset, question=args.question)
    context = prepare_context(request)

    print("Context assembled successfully.")
    print(f"Warnings: {len(context.warnings)}")
    if context.warnings:
        for warning in context.warnings:
            print(f"- {warning}")

    if args.print_layers:
        print("\n=== LAYER 1: ARCHITECTURE ===")
        print(context.layer_1_architecture[:1800])
        print("\n=== LAYER 2: DOMAIN ===")
        print(context.layer_2_domain[:1800])
        print("\n=== LAYER 3: CORRECTIONS ===")
        print(context.layer_3_corrections[:1800])

    print("\n=== SYSTEM PROMPT PREVIEW ===")
    print(context.system_prompt[:2000])


if __name__ == "__main__":
    main()
