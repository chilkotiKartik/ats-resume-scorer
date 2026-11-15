"""Downloadable, ATS-friendly resume templates built with python-docx."""

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor


def _base() -> Document:
    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Pt(42)
        section.left_margin = section.right_margin = Pt(50)
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    return doc


def _heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)


def _bullets(doc: Document, items) -> None:
    for item in items:
        p = doc.add_paragraph(item, style="List Bullet")
        p.paragraph_format.space_after = Pt(1)


def _role(doc: Document, title: str, where: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(title)
    r.bold = True
    p.add_run(f"  |  {where}")


def _header(doc: Document, name: str, line: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(name)
    r.bold = True
    r.font.size = Pt(20)
    doc.add_paragraph(line)


def classic() -> bytes:
    """One column, standard headings: works for most experienced candidates."""
    doc = _base()
    _header(doc, "Your Name", "City, Country | you@email.com | +91 00000 00000 | linkedin.com/in/you | github.com/you")
    _heading(doc, "Professional Summary")
    doc.add_paragraph("Role title with N years of experience in [domain]. Known for [two strengths], "
                      "using [3 to 4 core tools]. Looking to [the kind of role you want].")
    _heading(doc, "Experience")
    _role(doc, "Job Title, Company", "Mon YYYY – Present")
    _bullets(doc, [
        "Built [what] with [tools] for [who], [result with a number].",
        "Reduced [metric] by [X%] by [action you took].",
        "Led [team / project] to [outcome], [scale: users, revenue, time saved].",
    ])
    _role(doc, "Job Title, Company", "Mon YYYY – Mon YYYY")
    _bullets(doc, ["Start every bullet with an action verb and end with the result.",
                   "Put a number in at least half of your bullets."])
    _heading(doc, "Projects")
    _role(doc, "Project Name", "Tech: Python, SQL, …")
    _bullets(doc, ["What it does, how you built it, and what changed because of it."])
    _heading(doc, "Education")
    doc.add_paragraph("Degree, Institution, YYYY")
    _heading(doc, "Skills")
    doc.add_paragraph("Languages: …   Tools: …   Frameworks: …   Cloud: …")
    _heading(doc, "Certifications")
    doc.add_paragraph("Certification name, Issuer, YYYY")
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def student() -> bytes:
    """Education and projects first: for students and freshers."""
    doc = _base()
    _header(doc, "Your Name", "City, Country | you@email.com | +91 00000 00000 | linkedin.com/in/you | github.com/you")
    _heading(doc, "Summary")
    doc.add_paragraph("Final-year [degree] student focused on [area]. Built [N] projects with [tools]; "
                      "looking for a [role] internship or graduate role.")
    _heading(doc, "Education")
    _role(doc, "Degree, Institution", "YYYY – YYYY")
    doc.add_paragraph("CGPA: x.xx / 10   Relevant coursework: …")
    _heading(doc, "Projects")
    _role(doc, "Project Name", "Tech: …")
    _bullets(doc, ["Built [what] using [tools] that [result, with a number].",
                   "Deployed it at [link]; [N] users / stars / downloads."])
    _role(doc, "Project Name", "Tech: …")
    _bullets(doc, ["Describe the problem, your approach and the measurable outcome."])
    _heading(doc, "Experience")
    _role(doc, "Intern, Company", "Mon YYYY – Mon YYYY")
    _bullets(doc, ["Automated [task] with [tool], saving [hours] per week."])
    _heading(doc, "Skills")
    doc.add_paragraph("Languages: …   Tools: …   Libraries: …")
    _heading(doc, "Achievements")
    _bullets(doc, ["Hackathon / competition result, with rank and scale (e.g. top 5 of 300 teams)."])
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()
