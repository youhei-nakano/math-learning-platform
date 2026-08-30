import argparse
import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path


def summarize(paths):
    rows = []
    for path in paths:
        records = [
            json.loads(line)
            for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not records:
            continue
        latencies = [item["latency_seconds"] for item in records]
        successes = sum(item["status"] == "success" for item in records)
        rows.append(
            {
                "experiment_id": records[0]["experiment_id"],
                "mode": records[0]["config"]["mode"],
                "retrieval": records[0]["config"]["retrieval"],
                "rerank": records[0]["config"]["rerank"],
                "dataset_version": records[0]["dataset_version"],
                "model": records[0]["config"]["model"],
                "runs": len(records),
                "successes": successes,
                "completion_rate": successes / len(records),
                "error_rate": 1 - successes / len(records),
                "answer_accuracy": sum(item["answer_correct"] for item in records)
                / len(records),
                "citation_precision": statistics.mean(
                    item["citation_precision"] for item in records
                ),
                "citation_recall": statistics.mean(
                    item["citation_recall"] for item in records
                ),
                "latency_mean": statistics.mean(latencies),
                "latency_median": statistics.median(latencies),
                "latency_stdev": statistics.pstdev(latencies),
                "latency_min": min(latencies),
                "latency_max": max(latencies),
                "tool_calls": sum(item["tool_calls"] for item in records),
                "input_tokens": sum(
                    item["usage"]["input_tokens"] or 0 for item in records
                ),
                "output_tokens": sum(
                    item["usage"]["output_tokens"] or 0 for item in records
                ),
                "cost_usd": sum(item["usage"]["cost_usd"] for item in records),
            }
        )
    return rows


def write(rows, csv_path, markdown_path):
    fields = (
        list(rows[0])
        if rows
        else [
            "experiment_id",
            "mode",
            "retrieval",
            "rerank",
            "runs",
            "successes",
            "answer_accuracy",
            "citation_precision",
            "citation_recall",
            "latency_mean",
            "latency_median",
            "latency_stdev",
            "tool_calls",
            "cost_usd",
        ]
    )
    with Path(csv_path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Measured offline results",
        "",
        "Only executed conditions appear below. API/OCR/VLM conditions are **Not run**.",
        "",
        "| " + " | ".join(fields) + " |",
        "|" + "|".join(["---"] * len(fields)) + "|",
    ]
    lines.extend(
        "| " + " | ".join(str(row[field]) for field in fields) + " |" for row in rows
    )
    lines.extend(
        [
            "",
            "## Not run",
            "",
            "- OpenAI model single/multi comparison",
            "- Neural embeddings and model reranking",
            "- OCR enabled",
            "- OCR + VLM",
        ]
    )
    Path(markdown_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def comparison_payload(rows):
    selected = [
        row
        for row in rows
        if row["retrieval"] == "hybrid"
        and row["rerank"]
        and row["mode"] in {"single", "multi"}
    ]
    selected.sort(key=lambda row: (row["mode"] != "single", row["mode"]))
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "datasetVersion": selected[0]["dataset_version"] if selected else "Not run",
        "model": selected[0]["model"] if selected else "Not run",
        "retrieval": "hybrid + deterministic rerank" if selected else "Not run",
        "rows": [
            {
                "experimentId": row["experiment_id"],
                "mode": row["mode"],
                "label": "単一エージェント"
                if row["mode"] == "single"
                else "複数役割エージェント",
                "qualityScore": row["answer_accuracy"],
                "citationPrecision": row["citation_precision"],
                "citationRecall": row["citation_recall"],
                "completionRate": row["completion_rate"],
                "medianSeconds": row["latency_median"],
                "meanSeconds": row["latency_mean"],
                "minSeconds": row["latency_min"],
                "maxSeconds": row["latency_max"],
                "stdevSeconds": row["latency_stdev"],
                "averageCostUsd": row["cost_usd"] / row["runs"],
                "inputTokens": row["input_tokens"],
                "outputTokens": row["output_tokens"],
                "runs": row["runs"],
                "successes": row["successes"],
            }
            for row in selected
        ],
        "limitations": [
            "4問の小規模CC0デモ評価",
            "決定論的な抽出回答と部分文字列採点",
            "外部モデル、OCR、VLMはNot run",
            "API費用のみを集計し端末計算費用は含まない",
        ],
    }


def managed_markdown(payload):
    lines = [
        "<!-- RESEARCH_RESULTS_START -->",
        "## Single／multi比較の実測結果",
        "",
        f"生成元: `evaluation` JSONL / 評価セット `{payload['datasetVersion']}` / モデル `{payload['model']}`",
        "",
        "| 方式 | 品質スコア | 引用精度 | 完了率 | 中央時間 | 平均API費用／問題 | 実行数 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['label']} | {row['qualityScore']:.0%} | {row['citationPrecision']:.0%} | {row['completionRate']:.0%} | {row['medianSeconds'] * 1000:.3f} ms | ${row['averageCostUsd']:.4f} | {row['runs']} |"
        )
    lines.extend(
        [
            "",
            "外部モデル呼び出しは0回です。品質は4問の抽出回答に対する決定論的採点であり、一般的な数学性能を示しません。OpenAIモデル、OCR、VLMは **Not run** です。",
            "<!-- RESEARCH_RESULTS_END -->",
        ]
    )
    return "\n".join(lines)


def update_readme(path, block):
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    start, end = "<!-- RESEARCH_RESULTS_START -->", "<!-- RESEARCH_RESULTS_END -->"
    if start in text and end in text:
        before = text.split(start, 1)[0].rstrip()
        after = text.split(end, 1)[1].lstrip()
        text = f"{before}\n\n{block}\n\n{after}" if after else f"{before}\n\n{block}\n"
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    target.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--app-json")
    parser.add_argument("--readme", action="append", default=[])
    args = parser.parse_args()
    rows = summarize(args.inputs)
    write(rows, args.csv, args.markdown)
    payload = comparison_payload(rows)
    if args.app_json:
        Path(args.app_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.app_json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    block = managed_markdown(payload)
    for readme in args.readme:
        update_readme(readme, block)


if __name__ == "__main__":
    main()
