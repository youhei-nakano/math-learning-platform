import os
import unittest
from unittest.mock import patch

from math_research_workflow import (
    WorkflowConfigurationError,
    cosine_similarity,
    create_client,
    differentiate_polynomial,
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


if __name__ == "__main__":
    unittest.main()
