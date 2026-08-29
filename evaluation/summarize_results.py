import json
from pathlib import Path


BASELINE_PATH = Path("evaluation/baseline_results.json")
WORKFLOW_PATH = Path("evaluation/workflow_results.json")


def main():
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    retrieval = baseline["retrieval"]
    answerability = baseline["answerability"]

    print("Evaluation summary")
    print(
        f"- Retrieval {retrieval['metric']}: "
        f"{retrieval['hits']}/{retrieval['total']} "
        f"({retrieval['score']:.1%})"
    )
    print(
        "- Answerability separation: "
        f"in-domain min {answerability['answerable_min_similarity']:.4f}, "
        f"out-of-domain max {answerability['unanswerable_max_similarity']:.4f}, "
        f"threshold {answerability['threshold']:.2f}"
    )

    if not WORKFLOW_PATH.exists():
        print("- Tool selection: not run yet")
        return

    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    print(
        "- Tool selection accuracy: "
        f"{workflow['passed']}/{workflow['total']} "
        f"({workflow['score']:.1%})"
    )


if __name__ == "__main__":
    main()
