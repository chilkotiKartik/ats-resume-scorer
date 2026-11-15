"""Resources page: guides, interview prep, templates and learning links, with search."""

import streamlit as st

from frontend import navigation
from frontend.components.ui import bullet_list, chips, esc, footer, html, page_head
from frontend.services import templates_docx

# What each check looks at — summarised from backend/services/ats_scorer.py.
CHECKS = [
    ("Formatting", 20, [
        "Experience, Education, Skills, Summary and Projects sections",
        "How many lines are real bullet points",
        "How many of the standard sections are filled in",
    ]),
    ("Keywords & skills", 25, [
        "Number of distinct keywords and skills found",
        "Share of the job post's keywords you cover, allowing close spellings",
    ]),
    ("Content quality", 25, [
        "Bullets that open with action verbs",
        "Measurable results: %, ₹/$, users, hours saved",
        "Spelling and grammar",
    ]),
    ("Skill evidence", 15, [
        "Each listed skill is searched for in your projects and roles",
        "Matching is by meaning, so “built models” can back “machine learning”",
    ]),
    ("ATS safety", 15, [
        "Starts at full marks and deducts for problems",
        "Home address or PIN code on the page",
        "Box-drawing characters from table layouts",
        "Sections with almost no text",
    ]),
]

HEADINGS = ["Summary", "Experience", "Projects", "Education", "Skills", "Certifications"]

DO = [
    "One column, top to bottom, in the order above",
    "Standard fonts such as Calibri, Arial or Georgia at 10 to 12 pt",
    "A number in at least half of your bullets",
    "The job post's own wording for the skills you really have",
    "Each skill mentioned again in the project or role where you used it",
    "Save as PDF with selectable text, or as DOCX",
]
AVOID = [
    "Tables, text boxes and two-column templates",
    "Contact details placed in the page header or footer",
    "Skill bars, icons and photos, which parsers skip",
    "Your full street address; city and country are enough",
    "Abbreviations without the full term the first time",
    "Repeating keywords you can't back up",
]

REWRITES = [
    ("Responsible for building the backend",
     "Built a FastAPI backend serving 5,000 requests a day for the campus events app"),
    ("Worked on improving dashboard performance",
     "Cut dashboard load time from 9 s to 2 s by moving aggregation into SQL views"),
    ("Helped the team with data cleaning",
     "Cleaned and deduplicated 120,000 customer records, raising email deliverability by 18%"),
]

KEYWORDS = {
    "Software": ["Python", "Java", "JavaScript", "TypeScript", "React", "Node.js", "Django", "FastAPI",
                 "REST APIs", "SQL", "Git", "Docker", "Kubernetes", "AWS", "CI/CD", "Unit testing", "Agile"],
    "Data": ["SQL", "Python", "Pandas", "NumPy", "Scikit-learn", "Power BI", "Tableau", "Excel",
             "Statistics", "A/B testing", "ETL", "Airflow", "dbt", "Snowflake", "Data modeling", "KPIs"],
    "Business": ["Stakeholder management", "Project management", "Budgeting", "Forecasting",
                 "Process improvement", "Market research", "CRM", "Negotiation", "Strategic planning", "Team leadership"],
    "Design": ["Figma", "User research", "Wireframing", "Prototyping", "Usability testing", "Design systems",
               "Information architecture", "Interaction design", "Accessibility", "Adobe Creative Suite"],
}


INTERVIEW_QUESTIONS = [
    ("Tell me about yourself.", "Present, past, future in 60–90 seconds: what you do now, the one or two "
     "experiences that prove it, and why this role is the next step."),
    ("Walk me through a project you’re proud of.", "Pick one with a measurable result. Cover the problem, "
     "your choices and trade-offs, and what you'd do differently."),
    ("Tell me about a time you disagreed with a teammate.", "Use STAR. Show that you listened, used data "
     "to decide, and kept the relationship intact."),
    ("Describe a failure and what you learned.", "Choose a real one with a small blast radius; spend most "
     "of the answer on what you changed afterwards."),
    ("Why do you want to work here?", "Name something specific about the product, team or problem, and "
     "connect it to work you've already done."),
    ("What are your strengths and weaknesses?", "Back each strength with a resume bullet. For the weakness, "
     "pick a real one and show the system you use to manage it."),
    ("Where do you see yourself in a few years?", "Talk about skills and scope you want to grow into "
     "rather than titles."),
    ("Do you have any questions for us?", "Always yes. Ask how success is measured in the first 90 days, "
     "or what the team is working on next."),
]

STAR = [
    ("Situation", "One or two sentences of context: where, when, what was at stake."),
    ("Task", "What you were responsible for."),
    ("Action", "What you did, in the first person. This is most of the answer."),
    ("Result", "What changed, with a number if you have one, and what you learned."),
]

CAREER = [
    ("Ship projects people can use", "A deployed project with real users beats five tutorials. Put the link on your resume."),
    ("Write about your work", "Short posts on LinkedIn or a blog explaining what you built make you findable and show communication skills."),
    ("Contribute to open source", "Start with docs or small bugs in tools you already use; merged pull requests are verifiable proof."),
    ("Ask for referrals the right way", "Message people with a specific role ID, your one-line fit, and your resume. Keep it under 80 words."),
    ("Track applications", "Log company, role, date, contact and status. Follow up once after 7–10 days."),
    ("Re-score after every edit", "Small changes add up. Use History here to see which edits actually moved your score."),
]

LEARNING = [
    ("freeCodeCamp", "https://www.freecodecamp.org", "Free certifications in web development, Python and data analysis."),
    ("Harvard CS50", "https://cs50.harvard.edu/x/", "The classic introduction to computer science, free online."),
    ("Kaggle Learn", "https://www.kaggle.com/learn", "Short, hands-on courses in Python, pandas, SQL and machine learning."),
    ("roadmap.sh", "https://roadmap.sh", "Step-by-step learning paths for frontend, backend, DevOps, data and more."),
    ("NPTEL", "https://nptel.ac.in", "IIT and IISc courses with optional proctored certificates."),
    ("MIT OpenCourseWare", "https://ocw.mit.edu", "Lecture notes, videos and problem sets from MIT courses."),
]

CARDS = [
    ("tips", "Resume Tips", "Proven tips to make your resume stand out.",
     "bullets action verbs numbers rewrite do avoid keywords"),
    ("guide", "ATS Guide", "Complete guide to ATS-friendly resumes.",
     "ats score formatting headings sections parser points"),
    ("interview", "Interview Prep", "Top interview questions and how to answer them.",
     "interview questions star behavioral tell me about yourself"),
    ("career", "Career Growth", "Practical ways to grow opportunities in tech.",
     "career referrals linkedin open source projects networking"),
    ("templates", "Resume Templates", "ATS-friendly Word templates for every stage.",
     "templates word docx download fresher student classic"),
    ("learning", "Learning Resources", "Free courses to sharpen your skills.",
     "courses learning free certification kaggle cs50 nptel"),
]


def _tips() -> None:
    html('<div class="rs-cols">'
         f'<div><div class="rs-h3">Do</div>{bullet_list(DO, "good")}</div>'
         f'<div><div class="rs-h3">Avoid</div>{bullet_list(AVOID, "bad")}</div></div>')
    html('<div class="rs-h3" style="margin-top:1.5rem">Rewrite weak bullets</div>')
    for before, after in REWRITES:
        html('<div class="rs-ba" style="margin-bottom:.6rem">'
             f'<div class="rs-ba__col rs-ba__col--before"><div class="rs-ba__label">Before</div><p class="rs-ba__text">{esc(before)}</p></div>'
             f'<div class="rs-ba__col rs-ba__col--after"><div class="rs-ba__label">After</div><p class="rs-ba__text">{esc(after)}</p></div></div>')
    html('<div class="rs-h3" style="margin-top:1.5rem">Keywords recruiters search for</div>'
         '<p class="rs-body">Starting points by field. Always prefer the exact terms in the job post.</p>')
    tabs = st.tabs(list(KEYWORDS))
    for tab, words in zip(tabs, KEYWORDS.values()):
        with tab:
            html(chips(words))


def _guide() -> None:
    html('<p class="rs-body">Your score is the sum of five checks. Here’s what each one looks at.</p>')
    cols = "".join(
        f'<div><div class="rs-split__pts">{pts}<small>pts</small></div>'
        f'<div class="rs-split__name">{esc(name)}</div>'
        "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul></div>"
        for name, pts, items in CHECKS
    )
    html(f'<div class="rs-guide-grid">{cols}</div>')
    html('<div class="rs-h3" style="margin-top:1.5rem">Use the headings parsers expect, in this order</div>'
         '<div class="rs-headings">' + "".join(f"<span>{h}</span>" for h in HEADINGS) + "</div>")


def _interview() -> None:
    html('<div class="rs-h3">Answer behavioural questions with STAR</div>'
         '<div class="rs-tiles" style="margin:.6rem 0 1.4rem">' + "".join(
             f'<div class="rs-tile"><div class="v" style="font-size:1.2rem">{esc(k)}</div><div class="l">{esc(v)}</div></div>'
             for k, v in STAR) + "</div>")
    html('<div class="rs-h3">Common questions</div>')
    for q, a in INTERVIEW_QUESTIONS:
        with st.expander(q):
            html(f'<p class="rs-body">{esc(a)}</p>')


def _career() -> None:
    html('<ul class="rs-checks2">' + "".join(
        f'<li><i class="ok">✓</i><span><b>{esc(t)}.</b> {esc(d)}</span></li>' for t, d in CAREER) + "</ul>")


def _templates() -> None:
    html('<p class="rs-body">Single-column Word files with standard headings, so every ATS can read them. '
         "Replace the bracketed text, then score the result here.</p>")
    c1, c2 = st.columns(2)
    with c1:
        html('<div class="rs-h3">Classic</div><p class="rs-small">Summary, Experience, Projects, Education, Skills.</p>')
        st.download_button("Download Classic (.docx)", data=templates_docx.classic, file_name="resume-template-classic.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           icon=":material/download:", key="tpl_classic", type="primary", on_click="ignore")
    with c2:
        html('<div class="rs-h3">Student / fresher</div><p class="rs-small">Education and Projects first, then Experience.</p>')
        st.download_button("Download Student (.docx)", data=templates_docx.student, file_name="resume-template-student.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           icon=":material/download:", key="tpl_student", on_click="ignore")


def _learning() -> None:
    html('<ul class="rs-checks2">' + "".join(
        f'<li><i class="ok">↗</i><span><a href="{url}" target="_blank" rel="noopener"><b>{esc(n)}</b></a> {esc(d)}</span></li>'
        for n, url, d in LEARNING) + "</ul>")


_CONTENT = {"tips": _tips, "guide": _guide, "interview": _interview, "career": _career,
            "templates": _templates, "learning": _learning}


_ICONS = {"tips": "💡", "guide": "📄", "interview": "🤝", "career": "🚀", "templates": "📝", "learning": "🎓"}


_DIALOGS = {k: st.dialog(t, width="large", icon=_ICONS[k])(_CONTENT[k]) for k, t, _, _ in CARDS}


def _open(key: str) -> None:
    _DIALOGS[key]()


def render() -> None:
    with st.container(horizontal=True, vertical_alignment="center"):
        page_head("📘 Resources", "Useful resources to improve your resume and ace your interviews.")
        st.space("stretch")
        query = st.text_input("Search resources", placeholder="Search resources…", key="rsearch",
                              label_visibility="collapsed", icon=":material/search:", width=280)

    q = (query or "").strip().lower()
    cards = [c for c in CARDS if not q or q in (c[1] + " " + c[2] + " " + c[3]).lower()]
    if not cards:
        html(f'<div class="rs-empty"><h2 class="rs-h2">Nothing matches “{esc(query)}”</h2>'
             '<p class="rs-body">Try a broader word like interview, template or keywords.</p></div>')
    for row_start in range(0, len(cards), 3):
        cols = st.columns(3, gap="medium")
        for col, (key, title, desc, _) in zip(cols, cards[row_start:row_start + 3]):
            with col:
                with st.container(key=f"res_{key}"):
                    html(f'<div class="rs-rescard"><img src="app/static/art/icon-{key}.svg" alt="">'
                         f"<b>{esc(title)}</b><p>{esc(desc)}</p></div>")
                    if st.button("Open", type="tertiary", icon=":material/arrow_forward:", icon_position="right",
                                 key=f"rsopen_{key}"):
                        _open(key)

    st.space("large")
    with st.container(key="callout"):
        c1, c2 = st.columns([1.6, 1], vertical_alignment="center")
        with c1:
            html('<h2 class="rs-h2">Put it into practice</h2>'
                 '<p class="rs-body">Apply a few tips, then score your resume to see how much they moved the number.</p>')
        with c2:
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button("Score my resume", key="res_score"):
                    navigation.go("analyze")
    footer()
