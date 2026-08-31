"""Deterministically generate the original CC0 demo-v2 corpus and dataset."""

import hashlib
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).parent
VERSION = "demo-v2"
DOCUMENTS = {
    "arithmetic-algebra": [
        (
            "Percent and proportions",
            [
                "A percent p percent means p/100 of a quantity. A 20 percent discount multiplies the original price by 0.80.",
                "A proportion a/b = c/d can be solved by cross multiplication: ad = bc, when the denominators are nonzero.",
            ],
        ),
        (
            "Equations",
            [
                "For a nonzero a, the linear equation ax + b = c has solution x = (c-b)/a.",
                "The quadratic formula solves ax^2 + bx + c = 0 as x = (-b plus or minus sqrt(b^2-4ac))/(2a), for nonzero a.",
            ],
        ),
    ],
    "functions-sequences": [
        (
            "Functions",
            [
                "The slope between (x1,y1) and (x2,y2) is (y2-y1)/(x2-x1) when x2 differs from x1.",
                "Function composition is (f composed with g)(x) = f(g(x)). The input must lie in the domain of g and g(x) in the domain of f.",
            ],
        ),
        (
            "Sequences",
            [
                "An arithmetic sequence with first term a1 and common difference d has nth term an = a1 + (n-1)d.",
                "A geometric sequence with first term a1 and ratio r has nth term an = a1*r^(n-1).",
            ],
        ),
    ],
    "calculus-foundations": [
        (
            "Derivatives",
            [
                "The power rule gives d(x^n)/dx = n*x^(n-1).",
                "The product rule gives (fg)' = f'g + fg'. The chain rule gives d f(g(x))/dx = f'(g(x))*g'(x).",
            ],
        ),
        (
            "Integrals",
            [
                "For n not equal to -1, an antiderivative of x^n is x^(n+1)/(n+1) plus a constant.",
                "The fundamental theorem says that if F'=f, then the integral of f from a to b is F(b)-F(a).",
            ],
        ),
    ],
    "linear-foundations": [
        (
            "Vector spaces and bases",
            [
                "A basis is a linearly independent spanning set. Every vector has a unique coordinate representation in a chosen basis.",
                "In R^2, the standard basis vectors are (1,0) and (0,1).",
            ],
        ),
        (
            "Linear maps",
            [
                "A linear map T satisfies T(u+v)=T(u)+T(v) and T(av)=aT(v).",
                "The rank-nullity theorem states dim(V) = rank(T) + nullity(T) for a linear map on a finite-dimensional domain V.",
            ],
        ),
    ],
    "probability-statistics": [
        (
            "Probability",
            [
                "Conditional probability is P(A given B) = P(A intersect B)/P(B) when P(B)>0.",
                "Events A and B are independent when P(A intersect B)=P(A)P(B).",
            ],
        ),
        (
            "Statistics",
            [
                "The arithmetic mean of n observations is their sum divided by n.",
                "Population variance is the mean of squared deviations from the population mean.",
            ],
        ),
    ],
    "geometry-word-problems": [
        (
            "Geometry",
            [
                "For a right triangle with legs a and b and hypotenuse c, a^2+b^2=c^2.",
                "A circle of radius r has area pi*r^2, and a triangle has area base*height/2.",
            ],
        ),
        (
            "Applied word problems",
            [
                "Distance equals rate times time. When two workers act together, their work rates add.",
                "A quantity increased by p percent is multiplied by 1+p/100; successive percentage changes multiply their factors.",
            ],
        ),
    ],
}


def case(
    question_id,
    question,
    domain,
    difficulty,
    answer_type,
    expected_answer,
    variants,
    rubric,
    reasoning,
    document_id,
    page,
    tags,
):
    return {
        "question_id": question_id,
        "question": question,
        "domain": domain,
        "difficulty": difficulty,
        "answer_type": answer_type,
        "answerable": True,
        "expected_answer": expected_answer,
        "acceptable_variants": variants,
        "grading_rubric": rubric,
        "required_reasoning": reasoning,
        "source_document_ids": [document_id],
        "source_pages": [{"document_id": document_id, "page_number": page}],
        "required_chunk_ids": [],
        "expected_citations": [{"document_id": document_id, "page_number": page}],
        "tags": tags,
        "dataset_version": VERSION,
        "auto_gradable": answer_type in {"numeric", "formula", "multiple_choice"},
    }


CASES = [
    case(
        "arith-percent-001",
        "A 20 percent discount is applied to 250. What is the discounted price?",
        "arithmetic",
        "easy",
        "numeric",
        "200",
        ["200.0"],
        "Compute 250*0.80.",
        ["convert percent to multiplier", "multiply"],
        "arithmetic-algebra",
        1,
        ["percent"],
    ),
    case(
        "arith-proportion-002",
        "Solve the proportion 3/5 = x/20.",
        "arithmetic",
        "medium",
        "numeric",
        "12",
        ["x=12"],
        "Use cross multiplication.",
        ["cross multiply", "solve"],
        "arithmetic-algebra",
        1,
        ["proportion"],
    ),
    case(
        "alg-linear-003",
        "Solve 3x + 5 = 20.",
        "algebra",
        "easy",
        "numeric",
        "5",
        ["x=5"],
        "Isolate x.",
        ["subtract 5", "divide by 3"],
        "arithmetic-algebra",
        2,
        ["linear-equation"],
    ),
    case(
        "alg-quadratic-004",
        "Which are the roots of x^2 - 5x + 6 = 0? A) 1,6 B) 2,3 C) -2,-3",
        "algebra",
        "hard",
        "multiple_choice",
        "B",
        ["B) 2,3", "2 and 3", "2,3"],
        "Choose the two roots whose sum is 5 and product is 6.",
        ["factor or quadratic formula", "select option"],
        "arithmetic-algebra",
        2,
        ["quadratic"],
    ),
    case(
        "func-slope-005",
        "Find the slope through (1,2) and (5,10).",
        "functions",
        "easy",
        "numeric",
        "2",
        ["2.0"],
        "Compute (10-2)/(5-1).",
        ["difference quotient"],
        "functions-sequences",
        1,
        ["slope"],
    ),
    case(
        "func-compose-006",
        "If f(x)=x+1 and g(x)=2x, compute (f composed with g)(3).",
        "functions",
        "medium",
        "numeric",
        "7",
        ["7.0"],
        "Evaluate g(3), then f of that value.",
        ["evaluate inner function", "evaluate outer function"],
        "functions-sequences",
        1,
        ["composition"],
    ),
    case(
        "seq-arithmetic-007",
        "An arithmetic sequence has a1=4 and d=3. Find a10.",
        "sequences",
        "easy",
        "numeric",
        "31",
        ["31.0"],
        "Use a1+(n-1)d.",
        ["substitute n=10"],
        "functions-sequences",
        2,
        ["arithmetic-sequence"],
    ),
    case(
        "seq-geometric-008",
        "A geometric sequence has a1=2 and r=3. Find a5.",
        "sequences",
        "hard",
        "numeric",
        "162",
        ["162.0"],
        "Use a1*r^(n-1).",
        ["substitute n=5", "evaluate power"],
        "functions-sequences",
        2,
        ["geometric-sequence"],
    ),
    case(
        "diff-power-009",
        "Differentiate x^5.",
        "differentiation",
        "easy",
        "formula",
        "5x^4",
        ["5*x^4", "5 x^4"],
        "Apply the power rule.",
        ["multiply by exponent", "decrease exponent"],
        "calculus-foundations",
        1,
        ["power-rule"],
    ),
    case(
        "diff-chain-010",
        "Differentiate (3x+1)^2.",
        "differentiation",
        "hard",
        "formula",
        "6(3x+1)",
        ["18x+6", "6*(3x+1)"],
        "Apply the chain rule.",
        ["differentiate outer square", "multiply by inner derivative"],
        "calculus-foundations",
        1,
        ["chain-rule"],
    ),
    case(
        "int-power-011",
        "Give an antiderivative of x^3.",
        "integration",
        "easy",
        "formula",
        "x^4/4 + C",
        ["(1/4)x^4+C", "x^4 / 4 + C"],
        "Apply the power antiderivative rule.",
        ["increase exponent", "divide by new exponent"],
        "calculus-foundations",
        2,
        ["power-integral"],
    ),
    case(
        "int-ftc-012",
        "If F'=f, express the integral of f from a to b.",
        "integration",
        "medium",
        "formula",
        "F(b)-F(a)",
        ["F(b) - F(a)"],
        "State the endpoint difference.",
        ["apply fundamental theorem"],
        "calculus-foundations",
        2,
        ["fundamental-theorem"],
    ),
    case(
        "lin-basis-013",
        "What two properties define a basis?",
        "linear_algebra",
        "easy",
        "short_text",
        "linearly independent and spanning",
        ["linearly independent spanning set"],
        "Mention both independence and spanning.",
        ["identify two defining properties"],
        "linear-foundations",
        1,
        ["basis"],
    ),
    case(
        "lin-coordinates-014",
        "Write (3,-2) using the standard basis e1=(1,0), e2=(0,1).",
        "linear_algebra",
        "medium",
        "formula",
        "3e1-2e2",
        ["3 e1 - 2 e2", "3(1,0)-2(0,1)"],
        "Give both coordinates in the standard basis.",
        ["read vector coordinates"],
        "linear-foundations",
        1,
        ["coordinates"],
    ),
    case(
        "lin-linearity-015",
        "State the two additivity and scalar properties required of a linear map T.",
        "linear_algebra",
        "medium",
        "short_text",
        "T(u+v)=T(u)+T(v) and T(av)=aT(v)",
        ["additivity and homogeneity"],
        "State both properties.",
        ["recall linearity conditions"],
        "linear-foundations",
        2,
        ["linear-map"],
    ),
    case(
        "lin-rank-016",
        "If dim(V)=7 and nullity(T)=2, find rank(T).",
        "linear_algebra",
        "hard",
        "numeric",
        "5",
        ["rank(T)=5"],
        "Use rank-nullity.",
        ["substitute dimensions", "subtract nullity"],
        "linear-foundations",
        2,
        ["rank-nullity"],
    ),
    case(
        "prob-conditional-017",
        "If P(A intersect B)=0.2 and P(B)=0.5, compute P(A given B).",
        "probability",
        "medium",
        "numeric",
        "0.4",
        ["2/5", "40%"],
        "Divide the intersection probability by P(B).",
        ["apply conditional formula"],
        "probability-statistics",
        1,
        ["conditional-probability"],
    ),
    case(
        "prob-independent-018",
        "P(A)=0.5, P(B)=0.4, and P(A intersect B)=0.2. Are A and B independent?",
        "probability",
        "hard",
        "short_text",
        "yes",
        ["Yes, because 0.5*0.4=0.2"],
        "Compare the intersection with the product.",
        ["multiply marginals", "compare"],
        "probability-statistics",
        1,
        ["independence"],
    ),
    case(
        "stat-mean-019",
        "Find the mean of 2, 4, 6, 8.",
        "statistics",
        "easy",
        "numeric",
        "5",
        ["5.0"],
        "Sum and divide by four.",
        ["sum observations", "divide by count"],
        "probability-statistics",
        2,
        ["mean"],
    ),
    case(
        "stat-variance-020",
        "For the population 1, 3, find the population variance.",
        "statistics",
        "hard",
        "numeric",
        "1",
        ["1.0"],
        "The mean is 2 and the average squared deviation is 1.",
        ["compute mean", "compute squared deviations", "average"],
        "probability-statistics",
        2,
        ["variance"],
    ),
    case(
        "geo-pythagorean-021",
        "A right triangle has legs 6 and 8. Find the hypotenuse.",
        "geometry",
        "easy",
        "numeric",
        "10",
        ["10.0"],
        "Use the Pythagorean theorem.",
        ["square legs", "add", "take square root"],
        "geometry-word-problems",
        1,
        ["pythagorean"],
    ),
    case(
        "geo-area-022",
        "A circle has radius 3. Express its area exactly.",
        "geometry",
        "medium",
        "formula",
        "9pi",
        ["9*pi", "9π"],
        "Use pi*r^2.",
        ["square radius", "multiply by pi"],
        "geometry-word-problems",
        1,
        ["circle-area"],
    ),
    case(
        "word-rate-023",
        "A cyclist travels at 15 km/h for 2 hours, then 10 km/h for 1 hour. Find total distance.",
        "word_problems",
        "medium",
        "multi_step",
        "40 km",
        ["40", "40km"],
        "Add 15*2 and 10*1.",
        ["compute each distance", "add distances"],
        "geometry-word-problems",
        2,
        ["distance-rate-time"],
    ),
    case(
        "word-percent-024",
        "A price of 100 increases by 10 percent and then decreases by 10 percent. Find the final price.",
        "word_problems",
        "hard",
        "multi_step",
        "99",
        ["99.0"],
        "Multiply by 1.10 and then 0.90.",
        ["apply first factor", "apply second factor"],
        "geometry-word-problems",
        2,
        ["successive-percent"],
    ),
]

for question_id, question, domain in [
    (
        "unanswerable-prime-025",
        "What is the largest known prime number?",
        "number_theory",
    ),
    (
        "unanswerable-topology-026",
        "State the classification theorem for compact connected surfaces.",
        "topology",
    ),
    (
        "unanswerable-ode-027",
        "Solve the differential equation y''+y=0 with y(0)=1 and y'(0)=0.",
        "differential_equations",
    ),
]:
    CASES.append(
        {
            "question_id": question_id,
            "question": question,
            "domain": domain,
            "difficulty": "hard",
            "answer_type": "unanswerable",
            "answerable": False,
            "expected_answer": "資料内では確認できません。",
            "acceptable_variants": [
                "not found in the provided material",
                "cannot be confirmed from the material",
            ],
            "grading_rubric": "Do not answer from outside knowledge; explicitly state that the supplied corpus is insufficient.",
            "required_reasoning": [
                "search corpus",
                "recognize missing evidence",
                "abstain",
            ],
            "source_document_ids": [],
            "source_pages": [],
            "required_chunk_ids": [],
            "expected_citations": [],
            "tags": ["unanswerable", "abstention"],
            "dataset_version": VERSION,
            "auto_gradable": True,
        }
    )


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    pdf_dir = ROOT / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    documents = []
    for document_id, pages in DOCUMENTS.items():
        path = pdf_dir / f"{document_id}.pdf"
        canvas = Canvas(str(path), pagesize=A4, invariant=1)
        for page_number, (heading, paragraphs) in enumerate(pages, start=1):
            canvas.setTitle(f"{document_id}.pdf")
            canvas.setAuthor("OpenAI Sandbox original CC0 fixture")
            canvas.setFont("Helvetica-Bold", 18)
            canvas.drawString(64, 780, heading)
            canvas.setFont("Helvetica", 10)
            canvas.drawString(
                64, 758, "Original CC0 evaluation fixture - generated locally"
            )
            text = canvas.beginText(64, 720)
            text.setFont("Helvetica", 12)
            text.setLeading(20)
            for paragraph in paragraphs:
                for start in range(0, len(paragraph), 88):
                    text.textLine(paragraph[start : start + 88])
                text.textLine("")
            canvas.drawText(text)
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(530, 36, f"Page {page_number}")
            canvas.showPage()
        canvas.save()
        digest = sha256(path)
        documents.append(
            {
                "id": document_id,
                "title": document_id.replace("-", " ").title(),
                "path": str(path.relative_to(ROOT.parents[2])),
                "sha256": digest,
                "license": "CC0-1.0",
                "pages": len(pages),
            }
        )
        for item in CASES:
            if item["source_document_ids"] == [document_id]:
                page = item["source_pages"][0]["page_number"]
                item["required_chunk_ids"] = [f"{document_id}:{digest[:8]}:{page}:0"]
    dataset = {
        "version": VERSION,
        "license": "CC0-1.0; original fixtures generated locally",
        "generation": {
            "script": "evaluation/datasets/demo-v2/generate_fixtures.py",
            "deterministic": True,
        },
        "documents": documents,
        "cases": CASES,
    }
    (ROOT / "dataset.json").write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
