import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from evaluation.grading import grade_answer, normalize_text
from evaluation.live_runner import (
    LiveConfig,
    _case_view,
    calculate_cost,
    estimated_question_cost,
    run,
    run_live_case,
)
from evaluation.regrade_results import regrade
from evaluation.report_live import aggregate
from evaluation.run_research import load_dataset
from evaluation.validate_dataset import validate_dataset
from research_platform.ingestion import ingest_pdf
from research_platform.pipeline import (
    assess_revision,
    contains_secret,
    enforce_solver_citations,
    enforce_tutor,
    execute_retrieval,
    validate_retrieval_plan,
)

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evaluation/datasets/demo-v2/dataset.json"


class FakeResponses:
    def __init__(self, outputs=None, error=None):
        self.outputs = list(outputs or [])
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        role = (
            kwargs["text"]["format"]["name"]
            .removeprefix("math_")
            .removesuffix("_output")
        )
        defaults = {
            "single": {
                "answerable": True,
                "answer": "200",
                "explanation": "The excerpt gives the percentage rule.",
                "citation_chunk_ids": [],
                "issues": [],
            },
            "coordinator": {
                "problem_type": "percentage",
                "domain": "arithmetic",
                "difficulty_hypothesis": "easy",
                "subproblems": [{"id": "s1", "description": "apply discount"}],
                "required_evidence": ["percentage discount rule"],
                "required_operations": ["multiplication"],
                "answerability_hypothesis": "answerable",
                "retrieval_needed": True,
                "constraints": ["use supplied evidence"],
            },
            "retriever": {
                "queries": [
                    {
                        "query_id": "q1",
                        "text": "20 percent discount multiplier",
                        "intent": "find discount rule",
                        "subproblem_ids": ["s1"],
                        "filters": {"document_ids": [], "pages": []},
                    }
                ],
                "search_mode": "hybrid",
                "top_k": 5,
                "rerank": True,
                "rationale": "Retrieve the required rule.",
            },
            "solver": {
                "answerable": True,
                "answer": "200",
                "reasoning_summary": "Apply the discount multiplier.",
                "steps": ["250 times 0.8 equals 200"],
                "citation_ids": [],
                "uncertainties": [],
            },
            "verifier": {
                "verdict": "pass",
                "answer_correctness": "pass",
                "citation_validity": "pass",
                "citation_support": "pass",
                "answerability": "answerable",
                "issues": [],
                "permitted_citation_ids": [],
                "revision_instructions": [],
                "corrected_answer": None,
            },
            "tutor": {
                "answerable": True,
                "final_answer": "200",
                "citation_ids": [],
                "uncertainty": None,
            },
        }
        output = self.outputs.pop(0) if self.outputs else defaults[role]
        details = SimpleNamespace(cached_tokens=20)
        usage = SimpleNamespace(
            input_tokens=100,
            output_tokens=25,
            total_tokens=125,
            input_tokens_details=details,
        )
        return SimpleNamespace(
            id="resp-test", output_text=json.dumps(output), usage=usage
        )


class FakeClient:
    def __init__(self, outputs=None, error=None):
        self.responses = FakeResponses(outputs, error)


class DatasetTests(unittest.TestCase):
    def test_v2_dataset_is_large_valid_and_balanced(self):
        summary = validate_dataset(DATASET)
        self.assertTrue(summary["valid"], summary["errors"])
        self.assertGreaterEqual(summary["cases"], 20)
        self.assertGreaterEqual(summary["unanswerable"], 2)
        self.assertEqual(set(summary["difficulties"]), {"easy", "medium", "hard"})

    def test_dataset_ids_and_required_fields(self):
        raw = json.loads(DATASET.read_text())
        ids = [case["question_id"] for case in raw["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(case["grading_rubric"] for case in raw["cases"]))

    def test_runner_normalizes_v2_without_leaking_answers(self):
        case = load_dataset(DATASET)["cases"][0]
        view = _case_view(case)
        self.assertNotIn("answer", view)
        self.assertNotIn("grading_rubric", view)
        self.assertNotIn("required_reasoning", view)


class GradingTests(unittest.TestCase):
    def test_normalization_and_numeric_grading(self):
        self.assertEqual(normalize_text(" X − 2 "), "x-2")
        case = {"answerable": True, "expected_answer": "200.0"}
        self.assertTrue(grade_answer(case, "The result is 200.")["correct"])

    def test_unanswerable_requires_explicit_decline(self):
        case = {"answerable": False, "expected_answer": ""}
        self.assertTrue(
            grade_answer(case, "Cannot determine from the provided excerpts.")[
                "correct"
            ]
        )
        self.assertFalse(grade_answer(case, "42")["correct"])
        self.assertTrue(
            grade_answer(case, "Insufficient evidence in the supplied excerpts.")[
                "correct"
            ]
        )

    def test_regrading_preserves_raw_input_and_writes_versioned_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "raw.jsonl"
            output = Path(directory) / "regraded.jsonl"
            record = {
                "case_id": "unanswerable-prime-025",
                "answer": "Insufficient evidence in the supplied excerpts.",
                "citations": [],
                "answer_correct": False,
                "quality": {},
            }
            original = json.dumps(record) + "\n"
            source.write_text(original)
            result = regrade(source, output, DATASET)
            self.assertEqual(source.read_text(), original)
            self.assertTrue(result[0]["answer_correct"])
            self.assertEqual(
                result[0]["quality"]["grading_version"], "deterministic-v2"
            )


class LiveRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset(DATASET)
        cls.case = cls.dataset["cases"][0]
        cls.chunks = []
        for document in cls.dataset["documents"]:
            cls.chunks.extend(
                ingest_pdf(ROOT / document["path"], document["id"])["chunks"]
            )

    def test_pricing_uses_cached_input_separately(self):
        cost = calculate_cost(
            {
                "input_tokens": 1_000_000,
                "cached_input_tokens": 500_000,
                "output_tokens": 100_000,
            }
        )
        self.assertAlmostEqual(cost, 0.8625)

    def test_single_and_multi_have_separate_pipeline_versions(self):
        single_client = FakeClient()
        single = run_live_case(
            self.case,
            self.chunks,
            LiveConfig("live-single"),
            single_client,
            "e",
        )
        multi_client = FakeClient()
        multi = run_live_case(
            self.case,
            self.chunks,
            LiveConfig("live-multi"),
            multi_client,
            "e",
        )
        self.assertEqual(single["status"], "success")
        self.assertEqual(single["tool_calls"], 1)
        self.assertEqual(multi["tool_calls"], 5)
        self.assertEqual(multi["usage"]["input_tokens"], 500)
        self.assertEqual(multi["orchestration_version"], "multi-pipeline-v2")
        self.assertEqual(
            [item["role"] for item in multi["trace"]],
            ["coordinator", "retriever", "search", "solver", "verifier", "tutor"],
        )
        self.assertFalse(single_client.responses.calls[0]["store"])

    def test_role_output_changes_later_inputs_and_actual_search(self):
        client = FakeClient()
        result = run_live_case(
            self.case, self.chunks, LiveConfig("live-multi"), client, "experiment"
        )
        prompts = [json.loads(call["input"]) for call in client.responses.calls]
        self.assertEqual(
            prompts[1]["role_input"]["coordinator"]["problem_type"], "percentage"
        )
        search_step = next(item for item in result["trace"] if item["role"] == "search")
        self.assertEqual(
            search_step["output"]["query_runs"][0]["normalized_query"],
            "20 percent discount multiplier",
        )
        self.assertTrue(prompts[2]["role_input"]["evidence"])
        self.assertIn("solver", prompts[3]["role_input"])
        self.assertIn("verifier", prompts[4]["role_input"])
        prompt_text = json.dumps(prompts)
        self.assertNotIn("grading_rubric", prompt_text)
        self.assertNotIn("expected_answer", prompt_text)

    def test_verifier_revision_changes_tutor_result_and_is_measured(self):
        outputs = [
            {
                "problem_type": "percentage",
                "domain": "arithmetic",
                "difficulty_hypothesis": "easy",
                "subproblems": [{"id": "s1", "description": "calculate"}],
                "required_evidence": ["discount rule"],
                "required_operations": ["multiply"],
                "answerability_hypothesis": "answerable",
                "retrieval_needed": True,
                "constraints": [],
            },
            {
                "queries": [
                    {
                        "query_id": "q1",
                        "text": "20 percent discount",
                        "intent": "rule",
                        "subproblem_ids": ["s1"],
                        "filters": {"document_ids": [], "pages": []},
                    }
                ],
                "search_mode": "hybrid",
                "top_k": 5,
                "rerank": True,
                "rationale": "find rule",
            },
            {
                "answerable": True,
                "answer": "205",
                "reasoning_summary": "Incorrect multiplication.",
                "steps": ["250 times 0.8"],
                "citation_ids": [],
                "uncertainties": [],
            },
            {
                "verdict": "revise",
                "answer_correctness": "fail",
                "citation_validity": "pass",
                "citation_support": "uncertain",
                "answerability": "answerable",
                "issues": [
                    {
                        "type": "math",
                        "severity": "high",
                        "description": "250 times 0.8 is 200.",
                    }
                ],
                "permitted_citation_ids": [],
                "revision_instructions": ["Replace 205 with 200."],
                "corrected_answer": "200",
            },
            {
                "answerable": True,
                "final_answer": "200",
                "citation_ids": [],
                "uncertainty": None,
            },
        ]
        result = run_live_case(
            self.case,
            self.chunks,
            LiveConfig("live-multi"),
            FakeClient(outputs),
            "experiment",
        )
        self.assertEqual(result["answer"], "200")
        self.assertEqual(result["pipeline_metrics"]["classification"], "improved")
        self.assertTrue(result["pipeline_metrics"]["tutor_applied_revision"])
        self.assertEqual(result["pipeline_metrics"]["issue_types"], ["math"])

    def test_pipeline_guards_queries_citations_reject_and_secrets(self):
        plan = {
            "queries": [
                {
                    "query_id": "q",
                    "text": "  percentage   discount ",
                    "intent": "rule",
                    "subproblem_ids": ["s"],
                    "filters": {"document_ids": [], "pages": []},
                }
            ],
            "search_mode": "hybrid",
            "top_k": 2,
            "rerank": True,
            "rationale": "test",
        }
        validated = validate_retrieval_plan(plan, {"arithmetic-algebra"})
        result = execute_retrieval(validated, self.chunks)
        self.assertEqual(validated["queries"][0]["text"], "percentage discount")
        self.assertTrue(result["evidence"])
        with self.assertRaises(ValueError):
            validate_retrieval_plan(
                {**plan, "queries": [{**plan["queries"][0], "text": ""}]},
                {"arithmetic-algebra"},
            )
        with self.assertRaises(ValueError):
            enforce_solver_citations(
                {
                    "answerable": True,
                    "answer": "x",
                    "reasoning_summary": "x",
                    "steps": [],
                    "citation_ids": ["fabricated"],
                    "uncertainties": [],
                },
                set(),
            )
        with self.assertRaises(ValueError):
            enforce_tutor(
                {
                    "answerable": True,
                    "final_answer": "revived",
                    "citation_ids": [],
                    "uncertainty": None,
                },
                {"verdict": "reject", "permitted_citation_ids": []},
            )
        self.assertTrue(contains_secret({"authorization": "hidden"}))

    def test_revision_classifies_improvement_and_regression(self):
        solver = {"answer": "wrong", "citation_ids": ["old"]}
        tutor = {"final_answer": "right", "citation_ids": ["new"]}
        improved = assess_revision(solver, tutor, False, True)
        regressed = assess_revision(solver, tutor, True, False)
        self.assertEqual(improved["classification"], "improved")
        self.assertEqual(regressed["classification"], "regressed")

    def test_non_json_and_api_failure_are_bounded_failures(self):
        bad = FakeClient(outputs=["not-json"])
        result = run_live_case(
            self.case,
            self.chunks,
            LiveConfig("live-single", retries=0),
            bad,
            "e",
        )
        self.assertEqual(result["status"], "failed")
        self.assertIn("ValueError", result["error"])
        failing = FakeClient(error=TimeoutError("secret internal detail"))
        result = run_live_case(
            self.case,
            self.chunks,
            LiveConfig("live-single", retries=1),
            failing,
            "e",
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(failing.responses.calls), 2)
        self.assertNotIn("secret", result["error"])

    def test_resume_skips_success_and_retry_failed_repeats_only_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run.jsonl"
            config = LiveConfig("live-single")
            run(DATASET, output, config, FakeClient(), {self.case["id"]})
            first_lines = output.read_text().splitlines()
            client = FakeClient()
            run(DATASET, output, config, client, {self.case["id"]})
            self.assertEqual(output.read_text().splitlines(), first_lines)
            self.assertEqual(client.responses.calls, [])

    def test_live_report_keeps_not_run_distinct_from_zero(self):
        payload = aggregate([])
        self.assertEqual(payload["status"], "not_run")
        self.assertEqual(payload["experiments"], [])

    def test_safety_limits_reject_excessive_budget(self):
        with self.assertRaises(ValueError):
            LiveConfig("live-single", max_total_cost_usd=5.01).validate()
        with self.assertRaises(ValueError):
            LiveConfig("live-single", max_question_cost_usd=0.21).validate()
        self.assertGreater(estimated_question_cost(LiveConfig("live-multi")), 0)

    def test_problem_limit_runs_only_requested_count(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "limited.jsonl"
            run(DATASET, output, LiveConfig("live-single"), FakeClient(), limit=2)
            self.assertEqual(len(output.read_text().splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
