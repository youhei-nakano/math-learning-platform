"""Generate original CC0 evaluation PDFs. No external source text is used."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).parent
DOCUMENTS = {
    "linear-foundations.pdf": [
        (
            "Vector spaces and bases",
            [
                "A vector space is a set with vector addition and scalar multiplication satisfying the vector space axioms.",
                "A basis is a linearly independent spanning set. Every vector has a unique coordinate representation in a chosen basis.",
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
    "calculus-foundations.pdf": [
        (
            "Derivatives",
            [
                "The derivative measures instantaneous rate of change.",
                "For the power function f(x)=x^n, the power rule gives f'(x)=n x^(n-1).",
            ],
        ),
        (
            "Integrals",
            [
                "The definite integral represents signed area and accumulation.",
                "The fundamental theorem of calculus connects differentiation and integration: if F'=f, then the integral of f from a to b is F(b)-F(a).",
            ],
        ),
    ],
}


def build():
    pdf_dir = ROOT / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    for filename, pages in DOCUMENTS.items():
        canvas = Canvas(str(pdf_dir / filename), pagesize=A4)
        for page_number, (heading, paragraphs) in enumerate(pages, start=1):
            canvas.setTitle(filename)
            canvas.setAuthor("OpenAI Sandbox evaluation fixture")
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
                for line in [
                    paragraph[index : index + 88]
                    for index in range(0, len(paragraph), 88)
                ]:
                    text.textLine(line)
                text.textLine("")
            canvas.drawText(text)
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(530, 36, f"Page {page_number}")
            canvas.showPage()
        canvas.save()


if __name__ == "__main__":
    build()
