import argparse
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.grading import citation_scores, grade_answer
from research_platform.config import ExperimentConfig
from research_platform.ingestion import ingest_pdf
from research_platform.orchestration import run_case


def git_version():
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    version = result.stdout.strip() or "uncommitted"
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return f"{version}-dirty" if dirty.stdout.strip() else version


def load_dataset(path):
    dataset = json.loads(Path(path).read_text(encoding="utf-8"))
    normalized = []
    for original in dataset["cases"]:
        case = dict(original)
        if "question_id" in case:
            case.update(
                {
                    "id": case["question_id"],
                    "answer": case["expected_answer"],
                    "evidence": case["expected_citations"],
                }
            )
        required = {"id", "question", "answer", "evidence"}
        missing = required - set(case)
        if missing:
            raise ValueError(f"case {case.get('id')} missing {sorted(missing)}")
        normalized.append(case)
    dataset["cases"] = normalized
    return dataset


def run(
    dataset_path, config, output_path, resume=True, case_ids=None, retry_failed=False
):
    dataset = load_dataset(dataset_path)
    chunks = []
    for document in dataset["documents"]:
        ingested = ingest_pdf(ROOT / document["path"], document["id"])
        if ingested["document_version"] != document["sha256"]:
            raise ValueError(f"document version mismatch: {document['id']}")
        chunks.extend(ingested["chunks"])
    code = git_version()
    experiment_id = config.experiment_id(dataset["version"], code)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not resume and destination.exists():
        destination.write_text("", encoding="utf-8")
    completed = set()
    if resume and destination.exists():
        prior = [
            json.loads(line)
            for line in destination.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        completed = {
            item["case_id"]
            for item in prior
            if not retry_failed or item["status"] == "success"
        }
    with destination.open("a", encoding="utf-8") as stream:
        for case in dataset["cases"]:
            if case_ids and case["id"] not in case_ids:
                continue
            if case["id"] in completed:
                continue
            result = run_case(case, chunks, config, experiment_id).to_dict()
            result.update(
                {
                    "config": asdict(config),
                    "dataset_version": dataset["version"],
                    "code_version": code,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "environment": {
                        "python": platform.python_version(),
                        "platform": platform.platform(),
                    },
                    "pricing": {
                        "currency": "USD",
                        "version": None,
                        "checked_at": None,
                        "scope": "No external model calls; API cost is measured as 0.",
                    },
                    "expected_answer": case["answer"],
                    "expected_evidence": case["evidence"],
                }
            )
            grading = grade_answer(case, result["answer"])
            result["answer_correct"] = grading["correct"]
            citation = citation_scores(result["citations"], case["evidence"])
            result["citation_precision"] = citation["precision"]
            result["citation_recall"] = citation["recall"]
            result["quality"] = {
                "final_answer_accuracy": result["answer_correct"],
                "explanation_accuracy": None,
                "intermediate_steps_complete": None,
                "citation_existence_rate": 1.0 if result["citations"] else 0.0,
                "citation_support_rate": result["citation_precision"],
                "citation_coverage": result["citation_recall"],
                "unsupported_claims": 0 if result["status"] == "success" else None,
                "grading_kind": grading["kind"] + " + evidence page match",
            }
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            stream.flush()
    return experiment_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", default=ROOT / "evaluation/datasets/demo-v2/dataset.json"
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    config = ExperimentConfig(
        **json.loads(Path(args.config).read_text(encoding="utf-8"))
    )
    print(
        run(
            args.dataset,
            config,
            args.output,
            not args.no_resume,
            set(args.case_ids or []),
            args.retry_failed,
        )
    )


if __name__ == "__main__":
    main()
