"""
Rule-based resume / job-description parser.

Produces the same JSON shape as groq_parser.parse_resume() and
parse_job_description(). It's used when GROQ_API_KEY isn't set or the Groq
call fails, so the scorer keeps working offline and on free hosting. Groq is
more accurate on unusual layouts; this parser handles conventional resumes
(clear section headings, bullet points, dates on role lines) well.
"""

import re
from datetime import date
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Vocabularies
# --------------------------------------------------------------------------

SKILL_VOCAB = [
    # languages
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Golang", "Rust", "Kotlin", "Swift",
    "Ruby", "PHP", "Scala", "R", "MATLAB", "SQL", "Bash", "Shell", "Dart", "Perl", "HTML", "CSS", "Sass",
    # web / frameworks
    "React", "React Native", "Next.js", "Angular", "Vue", "Svelte", "Node.js", "Express", "Django", "Flask",
    "FastAPI", "Spring", "Spring Boot", "Rails", "Laravel", ".NET", "ASP.NET", "Tailwind", "Bootstrap",
    "Redux", "GraphQL", "REST", "REST APIs", "gRPC", "WebSockets", "Flutter", "Streamlit", "jQuery",
    # data / ML
    "Pandas", "NumPy", "SciPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras", "XGBoost", "LightGBM",
    "OpenCV", "NLTK", "spaCy", "Hugging Face", "Transformers", "LangChain", "LLM", "LLMs", "RAG",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Analysis", "Data Science",
    "Data Visualization", "Statistics", "A/B Testing", "Experimentation", "Regression", "Classification",
    "Time Series", "Forecasting", "Feature Engineering", "ETL", "Data Modeling", "Data Pipelines",
    "Data Cleaning", "Power BI", "Tableau", "Looker", "Excel", "Google Sheets", "Matplotlib", "Seaborn",
    "Plotly", "Jupyter", "Spark", "PySpark", "Hadoop", "Airflow", "dbt", "Kafka", "Snowflake", "BigQuery",
    "Redshift", "Databricks", "MLflow",
    # databases
    "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis", "Cassandra", "DynamoDB", "Firebase", "Supabase",
    "Elasticsearch", "Oracle", "SQL Server",
    # cloud / devops
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
    "GitHub Actions", "CI/CD", "Linux", "Git", "GitHub", "GitLab", "Nginx", "Vercel", "Netlify", "Heroku",
    "Lambda", "EC2", "S3", "Microservices", "Serverless",
    # practice
    "Agile", "Scrum", "Jira", "Unit Testing", "Testing", "TDD", "Pytest", "Jest", "Selenium", "Cypress",
    "System Design", "Data Structures", "Algorithms", "OOP", "Debugging", "Code Review",
    # design / product / business
    "Figma", "Adobe XD", "Photoshop", "Illustrator", "UI Design", "UX Design", "User Research",
    "Wireframing", "Prototyping", "Usability Testing", "Design Systems", "Accessibility",
    "Product Management", "Project Management", "Stakeholder Management", "Market Research", "SEO",
    "Google Analytics", "CRM", "Salesforce", "HubSpot", "Budgeting", "Financial Modeling", "KPIs",
    "Dashboards", "Reporting", "Process Improvement", "Negotiation",
    # soft skills
    "Communication", "Leadership", "Teamwork", "Problem Solving", "Collaboration", "Mentoring",
    "Public Speaking", "Time Management", "Critical Thinking",
]

ACTION_VERBS = {
    "accelerated", "achieved", "added", "analyzed", "analysed", "architected", "automated", "boosted",
    "built", "championed", "cleaned", "coached", "collaborated", "configured", "conducted", "consolidated",
    "contributed", "coordinated", "created", "cut", "debugged", "decreased", "delivered", "deployed",
    "designed", "developed", "devised", "directed", "drove", "enabled", "engineered", "enhanced",
    "established", "evaluated", "executed", "expanded", "facilitated", "forecast", "forecasted", "founded",
    "generated", "grew", "guided", "headed", "identified", "implemented", "improved", "increased",
    "initiated", "integrated", "introduced", "launched", "led", "maintained", "managed", "mentored",
    "migrated", "minimized", "modeled", "modelled", "monitored", "negotiated", "optimized", "optimised",
    "orchestrated", "organized", "overhauled", "owned", "partnered", "performed", "piloted", "planned",
    "presented", "prioritized", "produced", "programmed", "prototyped", "published", "raised", "rebuilt",
    "redesigned", "reduced", "refactored", "resolved", "restructured", "revamped", "saved", "scaled",
    "secured", "shipped", "simplified", "spearheaded", "streamlined", "strengthened", "supervised",
    "tested", "trained", "transformed", "tripled", "doubled", "upgraded", "won", "wrote", "researched",
    "visualized", "authored", "standardized", "validated", "containerized", "trimmed", "slashed",
}

SECTION_ALIASES = {
    "summary": ["summary", "professional summary", "profile", "about", "about me", "objective",
                "career objective", "professional profile", "overview"],
    "experience": ["experience", "work experience", "professional experience", "employment",
                   "employment history", "work history", "internships", "internship", "internship experience",
                   "relevant experience"],
    "education": ["education", "academic background", "academics", "education and training", "qualifications"],
    "skills": ["skills", "technical skills", "core skills", "key skills", "skills and tools", "tools",
               "technologies", "tech stack", "skills & tools", "competencies", "core competencies"],
    "projects": ["projects", "personal projects", "academic projects", "key projects", "selected projects",
                 "project experience"],
    "certifications": ["certifications", "certificates", "licenses", "courses", "certifications and courses",
                       "licenses & certifications"],
    "other": ["achievements", "awards", "honors", "activities", "extracurricular", "extra-curricular activities",
              "positions of responsibility", "languages", "interests", "hobbies", "publications", "volunteering",
              "leadership", "references"],
}

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

_BULLET = re.compile(r"^\s*(?:[•●▪◦■\-–—*·]|\d+[.)])\s+")
_DATE_TOKEN = r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*,?\s*\d{4}|\d{1,2}/\d{4}|\d{4})"
_RANGE = re.compile(
    rf"({_DATE_TOKEN})\s*(?:-|–|—|to|until)\s*({_DATE_TOKEN}|present|current|now|ongoing|today)",
    re.IGNORECASE,
)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?)\d{3,5}[\s-]?\d{3,5}")
_LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?", re.IGNORECASE)
_GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?", re.IGNORECASE)
_DEGREE = re.compile(
    r"\b(b\.?\s?tech|m\.?\s?tech|b\.?\s?e\b|m\.?\s?e\b|b\.?\s?sc|m\.?\s?sc|bachelor|master|ph\.?d|mba|bba|bca|mca|"
    r"b\.?\s?s\b|m\.?\s?s\b|diploma|associate|class\s+(?:x|xii|10|12)|high school|secondary|senior secondary|"
    r"b\.?\s?com|m\.?\s?com|b\.?\s?a\b|m\.?\s?a\b)",
    re.IGNORECASE,
)


def _skill_pattern(skill: str) -> re.Pattern:
    escaped = re.escape(skill)
    return re.compile(rf"(?<![\w+#.]){escaped}(?![\w+#])", re.IGNORECASE if len(skill) > 2 else 0)


_SKILL_PATTERNS = [(s, _skill_pattern(s)) for s in SKILL_VOCAB]


def find_vocab_skills(text: str) -> List[str]:
    found = []
    for skill, pattern in _SKILL_PATTERNS:
        if skill in ("C", "R", "Go"):
            # Single letters/short words are only trusted inside a skills-like list.
            if not re.search(rf"(?:^|[,|/•:;(]\s*){re.escape(skill)}(?:\s*[,|/•;)]|\s*$)", text, re.MULTILINE):
                continue
        if pattern.search(text):
            found.append(skill)
    return found


# --------------------------------------------------------------------------
# Sectioning
# --------------------------------------------------------------------------

def _heading_of(line: str) -> Optional[str]:
    clean = re.sub(r"[^a-z&\s-]", "", line.lower()).strip()
    clean = re.sub(r"\s+", " ", clean)
    if not clean or len(clean.split()) > 5:
        return None
    for section, aliases in SECTION_ALIASES.items():
        if clean in aliases:
            return section
    return None


def split_sections(text: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return (header lines before the first section, {section: lines})."""
    header: List[str] = []
    sections: Dict[str, List[str]] = {}
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        heading = _heading_of(line.rstrip(":"))
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        if current is None:
            header.append(line)
        else:
            sections[current].append(line)
    return header, sections


# --------------------------------------------------------------------------
# Field extraction
# --------------------------------------------------------------------------

def _parse_date(token: str, is_end: bool) -> Optional[date]:
    token = token.strip().lower()
    if token in ("present", "current", "now", "ongoing", "today"):
        return date.today()
    m = re.match(r"(\d{1,2})/(\d{4})", token)
    if m:
        return date(int(m.group(2)), max(1, min(12, int(m.group(1)))), 1)
    m = re.match(r"([a-z]{3})[a-z]*\.?\s*,?\s*(\d{4})", token)
    if m and m.group(1) in MONTHS:
        return date(int(m.group(2)), MONTHS[m.group(1)], 1)
    m = re.match(r"(\d{4})", token)
    if m:
        return date(int(m.group(1)), 12 if is_end else 1, 1)
    return None


def _months_between(start: Optional[date], end: Optional[date]) -> int:
    if not start or not end or end < start:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def _strip_bullet(line: str) -> str:
    return _BULLET.sub("", line).strip()


def _is_bullet(line: str) -> bool:
    return bool(_BULLET.match(line))


def _parse_experience(lines: List[str]) -> List[Dict]:
    entries: List[Dict] = []
    current: Optional[Dict] = None
    pending_title: Optional[str] = None
    for i, line in enumerate(lines):
        rng = _RANGE.search(line)
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if rng and not _is_bullet(line):
            start = _parse_date(rng.group(1), False)
            end = _parse_date(rng.group(2), True)
            head = (line[: rng.start()] + line[rng.end():]).strip(" |,-–—()")
            parts = [p.strip() for p in re.split(r"\s+[|–—-]\s+|\s+at\s+|,\s*", head) if p.strip()]
            title = parts[0] if parts else ""
            company = parts[1] if len(parts) > 1 else ""
            if pending_title:  # two-line layout: title above, "Company | dates" below
                title, company = pending_title, title or company
                pending_title = None
            current = {
                "job_title": title,
                "company": company,
                "start_date": rng.group(1),
                "end_date": rng.group(2),
                "duration_months": _months_between(start, end),
                "description": "",
            }
            entries.append(current)
        elif not _is_bullet(line) and len(line) < 80 and nxt and _RANGE.search(nxt) and not _is_bullet(nxt):
            pending_title = line
        elif current is None:
            current = {"job_title": _strip_bullet(line), "company": "", "start_date": "", "end_date": "",
                       "duration_months": 0, "description": ""}
            entries.append(current)
        else:
            current["description"] = (current["description"] + "\n" + _strip_bullet(line)).strip()
    return [e for e in entries if e["job_title"] or e["description"]]


def _parse_projects(lines: List[str]) -> List[Dict]:
    projects: List[Dict] = []
    current: Optional[Dict] = None
    for line in lines:
        if not _is_bullet(line) and (current is None or current["description"]) and len(line) < 120:
            title = re.split(r"\s+[|–—]\s+|:\s", line)[0].strip()
            current = {"title": title, "description": "", "technologies": []}
            rest = line[len(title):].strip(" |–—:-")
            if rest:
                current["description"] = rest
            projects.append(current)
        elif current is not None:
            current["description"] = (current["description"] + "\n" + _strip_bullet(line)).strip()
        else:
            current = {"title": _strip_bullet(line)[:60], "description": _strip_bullet(line), "technologies": []}
            projects.append(current)
    for p in projects:
        p["technologies"] = find_vocab_skills(p["title"] + "\n" + p["description"])
    return projects


def _parse_education(lines: List[str]) -> List[Dict]:
    out: List[Dict] = []
    for line in lines:
        text = _strip_bullet(line)
        year = re.findall(r"(?:19|20)\d{2}", text)
        if _DEGREE.search(text) or re.search(r"universit|institute|college|school|iit|nit|iiit", text, re.I):
            degree, institution = text, ""
            parts = [p.strip() for p in re.split(r"\s+[|–—-]\s+|,\s*", text) if p.strip()]
            for p in parts:
                if re.search(r"universit|institute|college|school|iit|nit|iiit", p, re.I):
                    institution = p
                    break
            for p in parts:
                if _DEGREE.search(p):
                    degree = p
                    break
            out.append({"degree": degree, "institution": institution, "year": year[-1] if year else ""})
    return out


def _skills_from_section(lines: List[str]) -> List[str]:
    skills: List[str] = []
    for line in lines:
        line = _strip_bullet(line)
        if ":" in line:
            line = line.split(":", 1)[1]
        for part in re.split(r"[,|•;/]|\s{2,}", line):
            part = part.strip(" .()")
            if 1 <= len(part) <= 40 and len(part.split()) <= 4:
                skills.append(part)
    return skills


def _dedupe(items: List[str]) -> List[str]:
    seen, out = set(), []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def parse_resume(raw_text: str) -> Dict:
    header, sections = split_sections(raw_text)
    full = raw_text

    email_match = _EMAIL.search(full)
    email = email_match.group(0) if email_match else None
    linkedin = _LINKEDIN.search(full)
    github = _GITHUB.search(full)
    phone = None
    for line in header + full.splitlines()[:12]:
        m = _PHONE.search(line)
        if m and len(re.sub(r"\D", "", m.group(0))) >= 10:
            phone = m.group(0).strip()
            break

    name = ""
    for line in header[:4]:
        if _EMAIL.search(line) or re.search(r"\d{4}", line):
            continue
        words = line.split()
        if 1 < len(words) <= 4 and all(re.match(r"^[A-Za-z.'-]+$", w) for w in words):
            name = line
            break

    summary_lines = sections.get("summary", [])
    if not summary_lines:
        # A paragraph in the header (after name/contact) often is the summary.
        prose = [l for l in header[1:] if len(l.split()) > 12 and not _EMAIL.search(l)]
        summary_lines = prose[:2]

    skills = _dedupe(_skills_from_section(sections.get("skills", [])) + find_vocab_skills(full))
    experience = _parse_experience(sections.get("experience", []))
    projects = _parse_projects(sections.get("projects", []))
    education = _parse_education(sections.get("education", []))
    certifications = [_strip_bullet(l) for l in sections.get("certifications", [])][:15]

    bullet_texts = [
        _strip_bullet(l)
        for key in ("experience", "projects")
        for l in sections.get(key, [])
        if _is_bullet(l)
    ]
    action_verbs = _dedupe([
        b.split()[0].lower().strip(",.:")
        for b in bullet_texts if b and b.split()[0].lower().strip(",.:") in ACTION_VERBS
    ])

    keywords = _dedupe(find_vocab_skills(full) + [s for s in skills if len(s) > 2])

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
        "professional_summary": " ".join(summary_lines).strip(),
        "skills": skills[:60],
        "experience": experience,
        "education": education,
        "certifications": certifications,
        "projects": projects,
        "action_verbs": action_verbs,
        "keywords": keywords[:80],
    }


def parse_job_description(raw_text: str) -> Dict:
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    title = ""
    m = re.search(r"(?:hiring|looking for|seeking)\s+(?:an?\s+)?([A-Z][\w/ -]{3,50}?)(?:\s+to\b|\s+who\b|[.,]|$)", raw_text)
    if m:
        title = m.group(1).strip()
    elif lines:
        title = lines[0][:60]

    lower = raw_text.lower()
    split_at = None
    for marker in ("nice to have", "preferred", "bonus", "good to have", "plus:"):
        idx = lower.find(marker)
        if idx != -1:
            split_at = idx if split_at is None else min(split_at, idx)
    required_text = raw_text if split_at is None else raw_text[:split_at]
    preferred_text = "" if split_at is None else raw_text[split_at:]

    required = find_vocab_skills(required_text)
    preferred = [s for s in find_vocab_skills(preferred_text) if s not in required]

    years = re.search(r"(\d+)\+?\s*(?:years|yrs)", raw_text, re.IGNORECASE)
    edu = _DEGREE.search(raw_text)
    responsibilities = [_strip_bullet(l) for l in lines if _is_bullet(l)][:12]

    return {
        "job_title": title,
        "required_skills": required,
        "preferred_skills": preferred,
        "experience_required": f"{years.group(1)}+ years" if years else "",
        "education_required": edu.group(0) if edu else "",
        "key_responsibilities": responsibilities,
        "keywords": _dedupe(required + preferred),
    }
