import argparse
import asyncio
import json
import os
import time
from pathlib import Path

from agents import Agent, Runner


CASES_PATH = Path("evaluation/workflow_cases.json")
OUTPUT_PATH = Path("evaluation/multi_agent_results.json")
MODEL = "gpt-4.1-mini"


literature_agent = Agent(
    name="Literature specialist",
    handoff_description="Handles literature, definition, theorem, and proof questions.",
    instructions="Classify this as a literature-search request. Reply only: search_math_pdf",
    model=MODEL,
)

differentiation_agent = Agent(
    name="Differentiation specialist",
    handoff_description="Handles any request to differentiate an expression in x.",
    instructions=(
        "Classify this as a differentiation request, including unsupported "
        "expressions. Reply only: differentiate_polynomial"
    ),
    model=MODEL,
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Hand off every request to exactly one matching specialist.",
    handoffs=[literature_agent, differentiation_agent],
    model=MODEL,
)


async def evaluate():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        started_at = time.perf_counter()
        run = await Runner.run(triage_agent, case["question"])
        actual_tool = str(run.final_output).strip()
        passed = actual_tool == case["expected_tool"]
        results.append(
            {
                **case,
                "actual_tool": actual_tool,
                "last_agent": run.last_agent.name,
                "passed": passed,
                "latency_seconds": round(
                    time.perf_counter() - started_at,
                    3,
                ),
            }
        )
        print(f"{case['id']}: {'PASS' if passed else 'FAIL'}")

    passed_count = sum(item["passed"] for item in results)
    report = {
        "pattern": "agents_sdk_handoffs",
        "passed": passed_count,
        "total": len(results),
        "score": passed_count / len(results),
        "total_latency_seconds": round(
            sum(item["latency_seconds"] for item in results),
            3,
        ),
        "cases": results,
        "comparison_note": (
            "Compare this routing score and API latency with the single-router "
            "Function Calling baseline. Multi-agent is not used in production."
        ),
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Accuracy: {passed_count}/{len(results)} ({report['score']:.1%})")


def main():
    parser = argparse.ArgumentParser(
        description="Limited Agents SDK routing comparison (uses API calls)."
    )
    parser.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEYが設定されていません。")
    asyncio.run(evaluate())


if __name__ == "__main__":
    main()
