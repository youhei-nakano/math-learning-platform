import json
from pathlib import Path


SINGLE_PATH = Path("evaluation/workflow_results.json")
MULTI_PATH = Path("evaluation/multi_agent_results.json")


def load(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    single = load(SINGLE_PATH)
    multi = load(MULTI_PATH)

    if single is None or multi is None:
        print("Run both evaluators before comparing orchestration.")
        print(f"- single router: {'ready' if single else 'missing'}")
        print(f"- multi agent: {'ready' if multi else 'missing'}")
        return

    print("Orchestration comparison")
    print(
        f"- Single router: {single['score']:.1%} accuracy, "
        f"{single['total_latency_seconds']:.3f}s total"
    )
    print(
        f"- Multi agent: {multi['score']:.1%} accuracy, "
        f"{multi['total_latency_seconds']:.3f}s total"
    )
    print(
        "Keep the single router unless multi-agent accuracy improves enough "
        "to justify additional latency, API calls, dependencies, and tracing."
    )


if __name__ == "__main__":
    main()
