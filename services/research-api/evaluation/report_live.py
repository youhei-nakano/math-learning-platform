import argparse
import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path


def _stats(records):
    successful = [item for item in records if item["status"] == "success"]
    latencies = [item["latency_seconds"] for item in successful]
    costs = [item.get("usage", {}).get("cost_usd") or 0 for item in records]
    return {
        "runs": len(records),
        "successes": len(successful),
        "completion_rate": len(successful) / len(records) if records else None,
        "answer_accuracy": statistics.mean(
            bool(item.get("answer_correct")) for item in records
        )
        if records
        else None,
        "citation_precision": statistics.mean(
            item.get("citation_precision", 0) for item in records
        )
        if records
        else None,
        "citation_recall": statistics.mean(
            item.get("citation_recall", 0) for item in records
        )
        if records
        else None,
        "latency_mean": statistics.mean(latencies) if latencies else None,
        "latency_median": statistics.median(latencies) if latencies else None,
        "latency_stdev": statistics.pstdev(latencies) if latencies else None,
        "latency_min": min(latencies) if latencies else None,
        "latency_max": max(latencies) if latencies else None,
        "input_tokens": sum(
            item.get("usage", {}).get("input_tokens") or 0 for item in records
        ),
        "output_tokens": sum(
            item.get("usage", {}).get("output_tokens") or 0 for item in records
        ),
        "cost_usd": sum(costs),
        "cost_per_success_usd": sum(costs) / len(successful) if successful else None,
    }


def aggregate(paths):
    records = []
    for path in paths:
        records.extend(
            json.loads(line)
            for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    if not records:
        return {
            "schemaVersion": 1,
            "status": "not_run",
            "reason": "実LLM JSONLがないため未実行です (No live-LLM records).",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "experiments": [],
        }
    experiments = []
    for experiment_id in sorted({item["experiment_id"] for item in records}):
        selected = [item for item in records if item["experiment_id"] == experiment_id]
        first = selected[0]
        breakdown = {}
        for field in ("domain", "difficulty"):
            breakdown[field] = {
                value: _stats([item for item in selected if item.get(field) == value])
                for value in sorted({item.get(field, "unknown") for item in selected})
            }
        experiments.append(
            {
                "experiment_id": experiment_id,
                "mode": first["config"]["mode"],
                "model": first["config"]["model"],
                "dataset_version": first["dataset_version"],
                "pricing": first.get("pricing"),
                "overall": _stats(selected),
                "breakdown": breakdown,
            }
        )
    return {
        "schemaVersion": 1,
        "status": "measured",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "experiments": experiments,
    }


def write_reports(payload, json_path, csv_path, markdown_path):
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(json_path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    rows = []
    for experiment in payload["experiments"]:
        rows.append(
            {
                "experiment_id": experiment["experiment_id"],
                "mode": experiment["mode"],
                "model": experiment["model"],
                **experiment["overall"],
            }
        )
    fields = list(rows[0]) if rows else ["status", "reason"]
    with Path(csv_path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
        else:
            writer.writerow({"status": "not_run", "reason": payload["reason"]})
    lines = ["# Live LLM evaluation", ""]
    if payload["status"] == "not_run":
        lines.extend(["**Not run.**", "", payload["reason"]])
    else:
        lines.extend(
            [
                "Only measured live runs are listed; deterministic runs are excluded.",
                "",
                "| Mode | Model | Runs | Accuracy | Citation precision | Median seconds | Cost USD |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for experiment in payload["experiments"]:
            stats = experiment["overall"]
            lines.append(
                f"| {experiment['mode']} | {experiment['model']} | {stats['runs']} | "
                f"{stats['answer_accuracy']:.3f} | {stats['citation_precision']:.3f} | "
                f"{stats['latency_median'] or 0:.3f} | {stats['cost_usd']:.6f} |"
            )
    Path(markdown_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="*")
    parser.add_argument("--json", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--app-json")
    args = parser.parse_args()
    payload = aggregate(args.inputs)
    write_reports(payload, args.json, args.csv, args.markdown)
    if args.app_json:
        Path(args.app_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.app_json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
