import os
import unittest
from unittest.mock import patch

from math_research_workflow import (
    API_TIMEOUT_SECONDS,
    WorkflowConfigurationError,
    WorkflowInputError,
    WorkflowServiceError,
    cosine_similarity,
    create_client,
    differentiate_polynomial,
    require_output_text,
    run_workflow,
)
from ui_app import render_page


class WorkflowTests(unittest.TestCase):
    def test_differentiate_polynomial(self):
        self.assertEqual(
            differentiate_polynomial("x^4 - 3*x^2 + 7"),
            "4*x**3 - 6*x",
        )

    def test_reject_non_polynomial(self):
        with self.assertRaises(ValueError):
            differentiate_polynomial("1/x")

    def test_reject_function(self):
        with self.assertRaises(ValueError):
            differentiate_polynomial("sin(x)")

    def test_cosine_dimension_mismatch(self):
        with self.assertRaises(ValueError):
            cosine_similarity([1.0], [1.0, 2.0])

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(WorkflowConfigurationError):
                create_client()

    def test_ui_escapes_question(self):
        page = render_page(question="<script>alert(1)</script>")
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_client_has_bounded_timeout_and_retry(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True):
            with patch("math_research_workflow.OpenAI") as client_class:
                create_client()
        client_class.assert_called_once_with(
            timeout=API_TIMEOUT_SECONDS,
            max_retries=1,
        )

    def test_empty_model_response_is_rejected(self):
        response = type("Response", (), {"output_text": "  "})()
        with self.assertRaises(WorkflowServiceError):
            require_output_text(response, "test")

    def test_long_input_is_rejected_before_api_call(self):
        with self.assertRaises(WorkflowInputError):
            run_workflow("x" * 2001, client=object())

    def test_ui_disables_duplicate_submission(self):
        page = render_page()
        self.assertIn("button.disabled=true", page)
        self.assertIn("aria-busy", page)


if __name__ == "__main__":
    unittest.main()
