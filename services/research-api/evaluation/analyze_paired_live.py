import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openai_config import GENERATION_MODEL

GRADING_VERSION = "paired-analysis-v1"


def percentile(values, p):
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    lo, hi = math.floor(index), math.ceil(index)
    return (
        ordered[lo]
        if lo == hi
        else ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)
    )


def mean_ci(values):
    if not values:
        return [None, None]
    if len(values) == 1:
        return [values[0], values[0]]
    mean = statistics.mean(values)
    margin = 1.96 * statistics.stdev(values) / math.sqrt(len(values))
    return [mean - margin, mean + margin]


def proportion_ci(values):
    low, high = mean_ci(values)
    return [max(0, low), min(1, high)]


def stats(records):
    successes = [r for r in records if r["status"] == "success"]
    costs = [r.get("usage", {}).get("cost_usd") or 0 for r in records]
    latencies = [r["latency_seconds"] for r in successes]

    def rate(field, rows=records):
        return statistics.mean(bool(r.get(field)) for r in rows) if rows else None

    multi_metrics = [
        r.get("pipeline_metrics") for r in records if r.get("pipeline_metrics")
    ]
    answer_values = [float(bool(r.get("answer_correct"))) for r in records]
    answerability_values = [
        float(r.get("answerable") == r.get("answerable_expected")) for r in records
    ]
    return {
        "runs": len(records),
        "successes": len(successes),
        "failure_rate": 1 - len(successes) / len(records) if records else None,
        "answer_accuracy": rate("answer_correct"),
        "answer_accuracy_ci95": proportion_ci(answer_values),
        "citation_precision": statistics.mean(
            r.get("citation_precision", 0) for r in records
        )
        if records
        else None,
        "citation_recall": statistics.mean(r.get("citation_recall", 0) for r in records)
        if records
        else None,
        "answerability_accuracy": statistics.mean(
            r.get("answerable") == r.get("answerable_expected") for r in records
        )
        if records
        else None,
        "answerability_accuracy_ci95": proportion_ci(answerability_values),
        "cost_usd": sum(costs),
        "cost_mean": statistics.mean(costs) if costs else None,
        "cost_median": statistics.median(costs) if costs else None,
        "cost_stdev": statistics.stdev(costs) if len(costs) > 1 else 0,
        "cost_mean_ci95": mean_ci(costs),
        "cost_per_success_usd": sum(costs) / len(successes) if successes else None,
        "latency_mean": statistics.mean(latencies) if latencies else None,
        "latency_p50": percentile(latencies, 0.50),
        "latency_p90": percentile(latencies, 0.90),
        "latency_p95": percentile(latencies, 0.95),
        "input_tokens": sum(
            r.get("usage", {}).get("input_tokens") or 0 for r in records
        ),
        "cached_input_tokens": sum(
            r.get("usage", {}).get("cached_input_tokens") or 0 for r in records
        ),
        "output_tokens": sum(
            r.get("usage", {}).get("output_tokens") or 0 for r in records
        ),
        "total_tokens": sum(
            r.get("usage", {}).get("total_tokens") or 0 for r in records
        ),
        "verifier_issue_rate": statistics.mean(
            bool(m.get("verifier_detected_issue")) for m in multi_metrics
        )
        if multi_metrics
        else None,
        "verifier_revision_rate": statistics.mean(
            bool(m.get("revision_requested")) for m in multi_metrics
        )
        if multi_metrics
        else None,
        "verifier_effective_revision_rate": statistics.mean(
            m.get("classification") == "improved" for m in multi_metrics
        )
        if multi_metrics
        else None,
        "downstream_regression_rate": statistics.mean(
            m.get("classification") == "regressed" for m in multi_metrics
        )
        if multi_metrics
        else None,
    }


def failure_class(record):
    if record["status"] == "success":
        if not record.get("answer_correct"):
            return "mathematical_error_or_grader_mismatch"
        if (
            record.get("citation_precision", 0) < 1
            or record.get("citation_recall", 0) < 1
        ):
            return "citation_defect"
        return "none"
    text = (record.get("error") or "").lower()
    role = next(
        (
            s.get("role")
            for s in reversed(record.get("trace", []))
            if s.get("status") == "failed"
        ),
        None,
    )
    if "tutor revived" in text:
        kind, role = "guard_failure", "tutor"
    elif "pass verdict cannot contain" in text:
        kind, role = "guard_failure", "verifier"
    elif "rate" in text:
        kind = "rate_limit"
    elif "timeout" in text:
        kind = "timeout"
    elif any(x in text for x in ("json", "schema", "format", "valueerror")):
        kind = "structured_output"
    else:
        kind = "api_failure"
    return (
        f"multi_role_{role}:{kind}"
        if role and record["config"]["mode"] == "live-multi"
        else kind
    )


def classify(single, multi):
    labels = []
    s, m = bool(single.get("answer_correct")), bool(multi.get("answer_correct"))
    labels.append(
        "multi_only_correct"
        if m and not s
        else "single_only_correct"
        if s and not m
        else "both_correct"
        if s
        else "both_incorrect"
    )
    for metric in ("citation_precision", "citation_recall"):
        delta = (multi.get(metric) or 0) - (single.get(metric) or 0)
        if delta:
            labels.append(f"multi_{metric}_{'improved' if delta > 0 else 'worsened'}")
    if not single.get("answerable_expected", True):
        sd = single.get("answerable") is False
        md = multi.get("answerable") is False
        if md != sd:
            labels.append(
                "multi_unanswerable_improved" if md else "multi_unanswerable_worsened"
            )
    pm = multi.get("pipeline_metrics") or {}
    if pm.get("classification") == "improved":
        labels.append("verifier_revision_success")
    if pm.get("verifier_detected_issue") and pm.get("classification") not in {
        "improved"
    }:
        labels.append("verifier_detected_but_not_fixed")
    if pm.get("classification") == "regressed":
        labels.append("downstream_regression")
    quality_equal = all(
        (single.get(k) or 0) == (multi.get(k) or 0)
        for k in ("answer_correct", "citation_precision", "citation_recall")
    )
    if quality_equal and (
        (multi.get("usage", {}).get("cost_usd") or 0)
        > (single.get("usage", {}).get("cost_usd") or 0)
        or multi["latency_seconds"] > single["latency_seconds"]
    ):
        labels.append("equal_quality_cost_or_latency_increase")
    if single["status"] != "success" or multi["status"] != "success":
        labels.append("system_failure")
    return labels


def paired_bootstrap(differences, seed=20260831, samples=10000):
    if not differences:
        return {"mean_difference": None, "ci95": [None, None], "effect_size_dz": None}
    rng = random.Random(seed)
    means = [
        statistics.mean(rng.choices(differences, k=len(differences)))
        for _ in range(samples)
    ]
    sd = statistics.stdev(differences) if len(differences) > 1 else 0
    return {
        "mean_difference": statistics.mean(differences),
        "ci95": [percentile(means, 0.025), percentile(means, 0.975)],
        "effect_size_dz": statistics.mean(differences) / sd if sd else 0,
    }


def analyze(path):
    raw = [
        json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()
    ]
    paired_raw = [r for r in raw if r.get("evaluation_kind") == "live-llm-paired"]
    if paired_raw:
        experiment_counts = Counter(r["experiment_id"] for r in paired_raw)
        selected_experiment = experiment_counts.most_common(1)[0][0]
        raw = [r for r in paired_raw if r["experiment_id"] == selected_experiment]
    all_attempt_cost_usd = sum(r.get("usage", {}).get("cost_usd") or 0 for r in raw)
    wrong_models = [
        r
        for r in raw
        if r.get("config", {}).get("model") != GENERATION_MODEL
        or any(
            step.get("model") not in {None, GENERATION_MODEL}
            for step in r.get("trace", [])
        )
    ]
    if wrong_models:
        raise ValueError("mixed or unexpected generation model in raw results")
    latest = {}
    for r in raw:
        latest[(r["experiment_id"], r["case_id"], r["trial"], r["config"]["mode"])] = r
    records = list(latest.values())
    pairs = defaultdict(dict)
    for r in records:
        pairs[(r["case_id"], r["trial"])][r["config"]["mode"]] = r
    complete = [
        (key, p["live-single"], p["live-multi"])
        for key, p in pairs.items()
        if len(p) == 2
    ]
    comparisons, counts = [], Counter()
    for (case_id, trial), single, multi in complete:
        labels = classify(single, multi)
        counts.update(labels)
        winner = (
            "multi"
            if multi.get("answer_correct") and not single.get("answer_correct")
            else "single"
            if single.get("answer_correct") and not multi.get("answer_correct")
            else "tie"
        )
        comparisons.append(
            {
                "case_id": case_id,
                "trial": trial,
                "winner": winner,
                "labels": labels,
                "single_correct": single.get("answer_correct"),
                "multi_correct": multi.get("answer_correct"),
                "single_citation_precision": single.get("citation_precision"),
                "multi_citation_precision": multi.get("citation_precision"),
                "single_citation_recall": single.get("citation_recall"),
                "multi_citation_recall": multi.get("citation_recall"),
                "single_cost_usd": single.get("usage", {}).get("cost_usd"),
                "multi_cost_usd": multi.get("usage", {}).get("cost_usd"),
                "single_latency_seconds": single.get("latency_seconds"),
                "multi_latency_seconds": multi.get("latency_seconds"),
                "failure_classes": [failure_class(single), failure_class(multi)],
            }
        )
    modes = {
        m: [r for r in records if r["config"]["mode"] == m]
        for m in ("live-single", "live-multi")
    }
    metrics = {}
    paired_fields = {
        "answer_correct": lambda r: float(bool(r.get("answer_correct"))),
        "citation_precision": lambda r: r.get("citation_precision") or 0,
        "citation_recall": lambda r: r.get("citation_recall") or 0,
        "answerability_correct": lambda r: float(
            r.get("answerable") == r.get("answerable_expected")
        ),
        "cost_usd": lambda r: r.get("usage", {}).get("cost_usd") or 0,
        "latency_seconds": lambda r: r.get("latency_seconds") or 0,
    }
    for metric, value in paired_fields.items():
        diffs = [value(m) - value(s) for _, s, m in complete]
        metrics[metric] = paired_bootstrap(diffs)
    breakdown = {}
    for field in ("domain", "difficulty", "answerable_expected"):
        breakdown[field] = {}
        for value in sorted({str(r.get(field)) for r in records}):
            breakdown[field][value] = {
                mode: stats([r for r in rows if str(r.get(field)) == value])
                for mode, rows in modes.items()
            }
    question_variance = {
        mode: statistics.pvariance(
            [
                statistics.mean(bool(x.get("answer_correct")) for x in rows)
                for rows in defaultdict(list).values()
            ]
        )
        if False
        else None
        for mode in modes
    }
    for mode, rows in modes.items():
        grouped = defaultdict(list)
        for r in rows:
            grouped[r["case_id"]].append(r)
        vals = [
            statistics.mean(bool(x.get("answer_correct")) for x in rs)
            for rs in grouped.values()
        ]
        question_variance[mode] = statistics.pvariance(vals) if len(vals) > 1 else 0
    trial_variance = {}
    for mode, rows in modes.items():
        grouped = defaultdict(list)
        for r in rows:
            grouped[r["trial"]].append(r)
        vals = [
            statistics.mean(bool(x.get("answer_correct")) for x in rs)
            for rs in grouped.values()
        ]
        trial_variance[mode] = statistics.pvariance(vals) if len(vals) > 1 else 0
    auth_blocked = bool(records) and all(
        r.get("status") == "failed" and r.get("error") == "AuthenticationError"
        for r in records
    )
    return {
        "schemaVersion": 2,
        "gradingVersion": GRADING_VERSION,
        "status": (
            "blocked_authentication"
            if auth_blocked
            else "measured"
            if len(complete) == 135
            else "incomplete"
            if records
            else "not_run"
        ),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "reason": (
            "Live execution stopped after authentication failed; no API usage was billed."
            if auth_blocked
            else None
        ),
        "experiment_id": records[0]["experiment_id"] if records else None,
        "records": len(records),
        "complete_pairs": len(complete),
        "attempt_records": len(raw),
        "experiment_cost_usd": all_attempt_cost_usd,
        "retry_overhead_cost_usd": all_attempt_cost_usd
        - sum(r.get("usage", {}).get("cost_usd") or 0 for r in records),
        "conditions": {m: stats(v) for m, v in modes.items()},
        "paired": metrics,
        "outcomes": dict(counts),
        "comparisons": comparisons,
        "breakdown": breakdown,
        "variance": {
            "between_question_accuracy": question_variance,
            "between_trial_accuracy": trial_variance,
        },
        "failure_classes": dict(Counter(failure_class(r) for r in records)),
        "attempt_failure_classes": dict(Counter(failure_class(r) for r in raw)),
        "cost_breakdown": {
            "by_mode_trial": {
                mode: {
                    str(trial): sum(
                        r.get("usage", {}).get("cost_usd") or 0
                        for r in rows
                        if r["trial"] == trial
                    )
                    for trial in sorted({r["trial"] for r in rows})
                }
                for mode, rows in modes.items()
            },
            "by_mode_case": {
                mode: {
                    case_id: sum(
                        r.get("usage", {}).get("cost_usd") or 0
                        for r in rows
                        if r["case_id"] == case_id
                    )
                    for case_id in sorted({r["case_id"] for r in rows})
                }
                for mode, rows in modes.items()
            },
        },
        "limitations": [
            "The 27 cases are locally authored fixtures, not a representative population.",
            "Five repetitions quantify run variability but do not make the sample statistically sufficient.",
            "Deterministic grading can misclassify semantically correct or incorrect explanations; blind human review remains pending.",
        ],
    }


def write_outputs(payload, output_dir, raw_path):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "paired-results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )
    single = payload["conditions"]["live-single"]
    multi = payload["conditions"]["live-multi"]
    outcome = payload["outcomes"]

    def number(value):
        return 0 if value is None else value

    summary = (
        "# Live LLM evaluation\n\n"
        + (
            "**Not run.** No paired live-LLM records are available.\n"
            if payload["status"] == "not_run"
            else f"Experiment `{payload['experiment_id']}`; {payload['complete_pairs']} complete pairs.\n"
        )
        + "\n"
        "| Condition | Runs | Accuracy | Citation P/R | Failure rate | Cost USD | p50 latency |\n"
        "|---|---:|---:|---:|---:|---:|---:|\n"
        f"| single | {single['runs']} | {number(single['answer_accuracy']):.3f} | {number(single['citation_precision']):.3f}/{number(single['citation_recall']):.3f} | {number(single['failure_rate']):.3f} | {single['cost_usd']:.6f} | {single['latency_p50'] or 0:.3f} |\n"
        f"| multi | {multi['runs']} | {number(multi['answer_accuracy']):.3f} | {number(multi['citation_precision']):.3f}/{number(multi['citation_recall']):.3f} | {number(multi['failure_rate']):.3f} | {multi['cost_usd']:.6f} | {multi['latency_p50'] or 0:.3f} |\n\n"
        f"Multi wins/ties/losses: {outcome.get('multi_only_correct', 0)}/"
        f"{outcome.get('both_correct', 0) + outcome.get('both_incorrect', 0)}/"
        f"{outcome.get('single_only_correct', 0)}. Human audit remains pending.\n\n"
        + "\n".join(f"- {item}" for item in payload["limitations"])
        + "\n"
    )
    (out.parent / "LIVE_RESULTS.md").write_text(summary, encoding="utf-8")
    readme = Path(__file__).resolve().parents[3] / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        start, end = "<!-- LIVE_RESULTS_START -->", "<!-- LIVE_RESULTS_END -->"
        if payload["status"] == "not_run":
            generated = f"{start}\n実LLM評価: **Not run**（対応raw JSONLなし）。\n{end}"
        else:
            generated = (
                f"{start}\n実LLM評価: `{payload['experiment_id']}`、対応比較"
                f"{payload['complete_pairs']}組、multi勝/同点/負="
                f"{outcome.get('multi_only_correct', 0)}/"
                f"{outcome.get('both_correct', 0) + outcome.get('both_incorrect', 0)}/"
                f"{outcome.get('single_only_correct', 0)}、総費用 $"
                f"{single['cost_usd'] + multi['cost_usd']:.6f}。人手監査は未完了。\n{end}"
            )
        if start in text and end in text:
            before = text.split(start, 1)[0]
            after = text.split(end, 1)[1]
            readme.write_text(before + generated + after, encoding="utf-8")
    comparisons = payload["comparisons"]
    fields = list(comparisons[0]) if comparisons else ["case_id"]
    for name, rows in (
        ("all-paired-cases.csv", comparisons),
        (
            "multi-losses.csv",
            [
                r
                for r in comparisons
                if r["winner"] == "single"
                or "multi_citation_precision_worsened" in r["labels"]
                or "multi_citation_recall_worsened" in r["labels"]
                or "downstream_regression" in r["labels"]
            ],
        ),
    ):
        with (out / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fields)
            w.writeheader()
            for row in rows:
                w.writerow(
                    {
                        **row,
                        "labels": ";".join(row["labels"]),
                        "failure_classes": ";".join(row["failure_classes"]),
                    }
                )
    losses = [
        r
        for r in comparisons
        if r["winner"] == "single"
        or any("worsened" in x or "regression" in x for x in r["labels"])
    ]
    md = [
        "# All multi-agent losses",
        "",
        "No favorable-case selection is applied.",
        "",
        "| Case | Trial | Labels |",
        "|---|---:|---|",
    ] + [
        f"| {r['case_id']} | {r['trial']} | {', '.join(r['labels'])} |" for r in losses
    ]
    (out / "MULTI_LOSSES.md").write_text("\n".join(md) + "\n")
    raw = [json.loads(x) for x in Path(raw_path).read_text().splitlines() if x.strip()]
    by_key = {(r["case_id"], r["trial"], r["config"]["mode"]): r for r in raw}
    dataset_path = Path(__file__).parent / "datasets" / "demo-v2" / "dataset.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = {c["question_id"]: c for c in dataset["cases"]}
    audit_rows = []
    audit_key_rows = []
    for comp in comparisons:
        if (
            comp["winner"] != "tie"
            or "both_incorrect" in comp["labels"]
            or any("citation" in x or "regression" in x for x in comp["labels"])
        ):
            pair_id = hashlib.sha256(
                f"{payload['experiment_id']}:{comp['case_id']}:{comp['trial']}".encode()
            ).hexdigest()[:12]
            modes = ["live-single", "live-multi"]
            random.Random(pair_id).shuffle(modes)
            for label, mode in zip(("A", "B"), modes):
                r = by_key[(comp["case_id"], comp["trial"], mode)]
                case = cases.get(comp["case_id"], {})
                audit_rows.append(
                    {
                        "pair_id": pair_id,
                        "case_id": comp["case_id"],
                        "trial": comp["trial"],
                        "blind_label": label,
                        "question": case.get("question", ""),
                        "expected_answer": r.get("expected_answer"),
                        "expected_evidence_json": json.dumps(
                            r.get("expected_evidence"), ensure_ascii=False
                        ),
                        "source_document_ids_json": json.dumps(
                            case.get("source_document_ids", []), ensure_ascii=False
                        ),
                        "source_pages_json": json.dumps(
                            case.get("source_pages", []), ensure_ascii=False
                        ),
                        "answer": r.get("answer"),
                        "explanation": r.get("explanation"),
                        "citations_json": json.dumps(
                            r.get("citations"), ensure_ascii=False
                        ),
                        "math_correct_human": "",
                        "explanation_complete_human": "",
                        "citations_support_claims_human": "",
                        "notes": "",
                    }
                )
                audit_key_rows.append(
                    {"pair_id": pair_id, "blind_label": label, "mode": mode}
                )
    fields = list(audit_rows[0]) if audit_rows else ["pair_id"]
    with (out / "blind-audit.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(audit_rows)
    # The key is separate so the review sheet itself stays blind.
    with (out / "blind-audit-key.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["pair_id", "blind_label", "mode"])
        w.writeheader()
        w.writerows(audit_key_rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("raw")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--app-json")
    a = p.parse_args()
    payload = analyze(a.raw)
    write_outputs(payload, a.output_dir, a.raw)
    if a.app_json:
        Path(a.app_json).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        )


if __name__ == "__main__":
    main()
