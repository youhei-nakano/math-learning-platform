import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.grading import citation_scores, grade_answer
from evaluation.run_research import load_dataset

GRADING_VERSION = "deterministic-v2"


def regrade(input_path, output_path, dataset_path):
    source = Path(input_path)
    destination = Path(output_path)
    if source.resolve() == destination.resolve():
        raise ValueError("output must differ from the immutable raw input")
    cases = {case["id"]: case for case in load_dataset(dataset_path)["cases"]}
    records = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        case = cases.get(record["case_id"])
        if case is None:
            raise ValueError(f"unknown case_id: {record['case_id']}")
        grading = grade_answer(case, record.get("answer", ""))
        citation = citation_scores(record.get("citations", []), case["evidence"])
        updated = dict(record)
        updated["answer_correct"] = grading["correct"]
        updated["citation_precision"] = citation["precision"]
        updated["citation_recall"] = citation["recall"]
        updated["quality"] = {
            **updated.get("quality", {}),
            "grading_kind": grading["kind"],
            "grading_version": GRADING_VERSION,
        }
        records.append(updated)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )
    return records


def main():
    parser = argparse.ArgumentParser(
        description="Regrade live JSONL without calling an external API."
    )
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument(
        "--dataset", default=ROOT / "evaluation/datasets/demo-v2/dataset.json"
    )
    args = parser.parse_args()
    print(len(regrade(args.input, args.output, args.dataset)))


if __name__ == "__main__":
    main()
