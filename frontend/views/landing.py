import streamlit as st

from frontend import navigation
from frontend.components.ui import footer, html, section_head
from frontend.services import store, theme
from frontend.services.sample_report import SAMPLE_ANALYSIS, SAMPLE_FILENAME
from frontend.services.session import open_report


HERO_SHEET = """
<div class="rs-desk" aria-label="Example of a resume marked up by the scorer">
  <div class="rs-page">
    <div class="rs-scan" aria-hidden="true"></div>
    <div class="rs-grade" aria-label="Score 72 out of 100">72<small>/100</small></div>
    <p class="rs-page__name">Priya Raman</p>
    <p class="rs-page__role">Data analyst, Bengaluru</p>

    <div class="rs-page__label">Experience</div>
    <ul>
      <li>Built weekly <span class="rs-hl">SQL</span> and <span class="rs-hl d2">Power BI</span>
          reports for 6 regional sales teams</li>
      <li><span class="rs-strike">Responsible for</span> cleaning customer data for the marketing team</li>
      <li>Forecast store demand with <span class="rs-hl d3">Python</span> and
          <span class="rs-hl d4">Pandas</span>, cutting stock-outs by 14%</li>
    </ul>

    <div class="rs-page__label">Skills</div>
    <p class="rs-page__skills"><span class="rs-hl d5">Python</span>, <span class="rs-hl d6">SQL</span>,
       Power BI, Pandas, Tableau, Airflow</p>
  </div>

  {mascot}
  <p class="rs-note rs-note--green n1" style="top: 6.4rem">Matches the job post</p>
  <p class="rs-note rs-note--red n2" style="top: 10.6rem">Weak opener, and no number</p>
  <p class="rs-note rs-note--red n3" style="top: 16.8rem">Tableau and Airflow are listed but never used</p>
</div>
"""

POINTS = [
    ("Formatting", 20, "Standard sections, consistent bullets, a structure parsers can follow."),
    ("Keywords", 25, "The skills and terms a recruiter searches for, and how many the job post shares."),
    ("Content", 25, "Action verbs, measurable results, and clean grammar."),
    ("Skill evidence", 15, "Whether each listed skill shows up in a real project or role."),
    ("ATS safety", 15, "No box-drawing characters, thin sections or home address details."),
]

STEPS = [
    ("Upload your resume", "PDF, DOC or DOCX. The text is extracted exactly as screening software would see it."),
    ("Add the job post", "Optional. Paste it in to see which of its keywords you already cover and which are missing."),
    ("Fix in order", "Issues come ranked by impact, each with the reason, where it appears and a rewrite example."),
]


def _open_sample() -> None:
    open_report(SAMPLE_ANALYSIS, SAMPLE_FILENAME, source="sample", with_jd=True)
    navigation.go("report")


def render() -> None:
    if theme.uses_sidebar():
        from frontend.views import home_dashboard
        home_dashboard.render()
        return
    left, right = st.columns([1, 1.08], gap="large", vertical_alignment="center")

    with left:
        html(
            '<h1 class="rs-display">Know what the ATS sees before a recruiter does.</h1>'
            '<p class="rs-lede">Upload your resume, paste the job post, and get a score out of 100 '
            "with the exact fixes that raise it: missing keywords, skills with no evidence, "
            "bullets without numbers.</p>"
        )
        st.space("small")
        with st.container(horizontal=True, gap="small"):
            if st.button("Score my resume", type="primary", key="hero_score"):
                navigation.go("analyze")
            if st.button("See a sample report", key="hero_sample"):
                _open_sample()
        access = ("Sign-in needed to run a check." if store.engine_mode() == "remote"
                  else "No account needed to try it.")
        html(f'<p class="rs-small" style="margin-top:.6rem">PDF, DOC or DOCX up to 5 MB. {access}</p>')

    with right:
        mascot = ""
        if theme.show_mascot():
            mascot = f'<img class="rs-hero-mascot rs-pop" src="{theme.art("scout-highlight")}" alt="Scout, the mascot">'
        if theme.current() == "toon":
            mascot += (
                f'<img class="rs-doodle rs-float" src="{theme.art("doodle-star")}" alt="" style="width:56px;top:-1.5rem;left:42%">'
                f'<img class="rs-doodle rs-float f2" src="{theme.art("doodle-plane")}" alt="" style="width:72px;top:1rem;right:-1rem">'
                f'<img class="rs-doodle rs-float f3" src="{theme.art("doodle-star")}" alt="" style="width:34px;top:45%;left:-1.2rem">'
            )
        html(HERO_SHEET.replace("{mascot}", mascot))

    # ---- Where the points come from -------------------------------------
    section_head(
        "Where the 100 points come from",
        "Five checks, weighted by how much they affect whether a resume gets through "
        "automated screening. The report shows your points in each.",
    )
    segs = "".join(
        f'<div class="rs-split__seg"><div class="rs-split__pts">{pts}<small>pts</small></div>'
        f'<div class="rs-split__name">{name}</div><div class="rs-split__what">{what}</div></div>'
        for name, pts, what in POINTS
    )
    html(f'<div class="rs-split">{segs}</div>')

    # ---- How a check works ---------------------------------------------
    section_head("How a check works")
    steps = "".join(
        f'<div class="rs-step"><div class="rs-step__n">{i}</div>'
        f'<div class="rs-h3">{title}</div><p class="rs-body">{body}</p></div>'
        for i, (title, body) in enumerate(STEPS, start=1)
    )
    html(f'<div class="rs-steps">{steps}</div>')

    # ---- More than a score -------------------------------------------------
    section_head("More than a score")
    html(
        '<div class="rs-honest">'
        '<div><div class="rs-h3">Bullet Lab</div><p class="rs-body">Paste your bullets and get an instant score '
        "and the one change that fixes each, before you touch the full resume.</p></div>"
        '<div><div class="rs-h3">Compare versions</div><p class="rs-body">History shows your score over time and '
        "exactly which issues each edit fixed or introduced.</p></div>"
        '<div><div class="rs-h3">Three looks</div><p class="rs-body">Switch between Toon, Paper and Midnight '
        "from the Theme menu at the top.</p></div>"
        "</div>"
    )

    # ---- What happens to the file ---------------------------------------
    section_head("What happens to your resume")
    html(
        '<div class="rs-honest">'
        '<div><div class="rs-h3">Read on the server</div><p class="rs-body">The file is parsed and scored '
        "with spaCy and sentence embeddings. It isn't shared with employers.</p></div>"
        '<div><div class="rs-h3">Groq, only if configured</div><p class="rs-body">When the site has a Groq key, '
        "the resume text is sent to Groq's Llama 3 API for more accurate parsing. Otherwise nothing leaves the server.</p></div>"
        '<div><div class="rs-h3">Yours to keep or delete</div><p class="rs-body">Signed in, results are saved to '
        "your account. As a guest, they disappear when you close the tab.</p></div>"
        "</div>"
    )

    # ---- Sample callout ----------------------------------------------------
    with st.container(key="callout"):
        c1, c2 = st.columns([1.6, 1], vertical_alignment="center")
        with c1:
            html(
                '<h2 class="rs-h2">Not ready to upload yet?</h2>'
                '<p class="rs-body">Open a finished report for a sample data-analyst resume '
                "and see every section before you sign in.</p>"
            )
        with c2:
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button("Open the sample report", key="callout_sample"):
                    _open_sample()

    footer()
