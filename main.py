import argparse

from app import build_agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify an incident severity (P1-P4) using PydanticAI + Bedrock."
    )
    parser.add_argument("text", help="Customer-reported problem text")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    agent = build_agent()
    result = agent.run_sync(args.text)
    print(result.output.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
