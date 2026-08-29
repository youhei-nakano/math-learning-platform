import argparse
import json
import sys
import time
from pathlib import Path

from openai import OpenAIError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from math_research_workflow import (
    WorkflowError,
    choose_tool,
    create_client,
    get_tool_call,
)


CASES_PATH = Path("evaluation/workflow_cases.json")
RESULTS_PATH = Path("evaluation/workflow_results.json")


def evaluate(cases_path=CASES_PATH, results_path=RESULTS_PATH):
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    client = create_client()
    results = []

    for case in cases:
        started_at = time.perf_counter()
        try:
            response = choose_tool(client, case["question"])
            actual_tool = get_tool_call(response).name
            error = None
        except (OpenAIError, ValueError, TypeError) as exc:
            actual_tool = None
            error = str(exc)

        passed = actual_tool == case["expected_tool"]
        results.append(
            {
                **case,
                "actual_tool": actual_tool,
                "passed": passed,
                "error": error,
                "latency_seconds": round(
                    time.perf_counter() - started_at,
                    3,
                ),
            }
        )
        print(f"{case['id']}: {'PASS' if passed else 'FAIL'}")

    passed_count = sum(item["passed"] for item in results)
    report = {
        "metric": "tool_selection_accuracy",
        "passed": passed_count,
        "total": len(results),
        "score": passed_count / len(results),
        "total_latency_seconds": round(
            sum(item["latency_seconds"] for item in results),
            3,
        ),
        "cases": results,
    }
    results_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Accuracy: {passed_count}/{len(results)} ({report['score']:.1%})")
    print(f"Saved: {results_path}")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--output", type=Path, default=RESULTS_PATH)
    args = parser.parse_args()
    try:
        evaluate(args.cases, args.output)
    except WorkflowError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
