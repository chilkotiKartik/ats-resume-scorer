"""
A worked example of a backend AnalysisResponse, used by "See a sample report".

It lets someone see what the report contains before they sign in or upload
anything. The issue texts are the same ones backend/services/feedback_engine.py
produces, so the sample reads exactly like a real run.
"""

SAMPLE_FILENAME = "sample-resume-data-analyst.pdf"

SAMPLE_ANALYSIS = {
    "ATS_score": 72.0,
    "ats_score": 72.0,
    "interpretation": "Good! Your resume is ATS-friendly with room for minor improvements.",
    "component_scores": {
        "formatting": 17.0,
        "keywords": 19.0,
        "content": 14.0,
        "skill_validation": 9.0,
        "ats_compatibility": 13.0,
    },
    "strengths": [
        "Has a dedicated Experience section",
        "Includes a Projects section showcasing applied skills",
        "Clear Skills section with listed technologies",
        "Strong skill set — 14 skills detected",
        "8 skills are backed by project/experience evidence",
        "Well-formatted and ATS-friendly structure",
    ],
    "critical_issues": [],
    "issues_summary": [
        "Incomplete Contact Information",
        "No Quantifiable Achievements Found",
        "Most Skills Lack Supporting Evidence",
        "Missing Professional Summary",
    ],
    "detailed_feedback": [
        {
            "issue_title": "Incomplete Contact Information",
            "severity_level": "High",
            "ats_impact": "High",
            "explanation": (
                "Your resume is missing: phone number, LinkedIn URL. Recruiters need reliable ways "
                "to reach you. Missing contact details can cause your application to be skipped entirely."
            ),
            "where_it_appears": "Header / Contact section at the top of the resume",
            "how_to_fix": (
                "Add your full name, email, phone number, LinkedIn profile, and optionally a GitHub "
                "or portfolio link at the top of your resume."
            ),
            "action_items": [
                "Add your phone number to the header section",
                "Add your LinkedIn URL to the header section",
                "Format the contact line as: email | phone | linkedin | github",
            ],
            "example_improvement": (
                "Add at top:\nPriya Raman\npriya.raman@email.com | +91-98765 43210\n"
                "linkedin.com/in/priyaraman | github.com/priyaraman"
            ),
        },
        {
            "issue_title": "No Quantifiable Achievements Found",
            "severity_level": "Moderate",
            "ats_impact": "Medium",
            "explanation": (
                "Your experience section does not contain any measurable outcomes (numbers, percentages, "
                "or dollar amounts). Quantified achievements make your impact concrete and are strongly "
                "preferred by recruiters."
            ),
            "where_it_appears": "Experience section — bullet point content",
            "how_to_fix": (
                "Add numbers to at least 50% of your bullet points. Include metrics like: users served, "
                "response time improved, revenue generated, team size, etc."
            ),
            "action_items": [
                "Go through each bullet point and ask: 'How much?', 'How many?', 'By what %?'",
                "Add metrics: users served, requests/day, % improvement, team size, time saved",
                "Aim for numbers in at least 50% of your experience bullets",
            ],
            "example_improvement": (
                "Before:\n• Improved the weekly sales dashboard\n• Cleaned customer data for the marketing team\n\n"
                "After:\n• Rebuilt the weekly sales dashboard in Power BI, cutting refresh time from 40 to 6 minutes\n"
                "• Deduplicated 120K customer records, raising email deliverability by 18%"
            ),
        },
        {
            "issue_title": "Most Skills Lack Supporting Evidence",
            "severity_level": "Moderate",
            "ats_impact": "High",
            "explanation": (
                "43% of your listed skills (6 out of 14) are not backed by any mention in your projects "
                "or experience sections. Recruiters and ATS systems cross-reference skills against actual "
                "work to verify credibility."
            ),
            "where_it_appears": "These skills have no supporting context: Tableau, Airflow, Spark, A/B Testing, Docker, R",
            "how_to_fix": (
                "For each skill in your Skills section, ensure it appears at least once in a project "
                "description or experience bullet point. Describe how and where you used that technology."
            ),
            "action_items": [
                "Mention 'Tableau' in a project or experience bullet point",
                "Mention 'Airflow' in a project or experience bullet point",
                "Mention 'A/B Testing' in a project or experience bullet point",
                "Remove skills you cannot demonstrate with any project or experience",
            ],
            "example_improvement": (
                "Your skill 'Airflow' has no supporting evidence.\n\nFix: Add to a project or experience bullet:\n"
                "'Built a data pipeline using Airflow that processed 10K records daily, reducing manual effort by 60%.'"
            ),
        },
        {
            "issue_title": "Missing Professional Summary",
            "severity_level": "Low",
            "ats_impact": "Low",
            "explanation": (
                "Your resume does not include a Professional Summary or Objective section at the top. "
                "While not required, a 2-3 line summary helps recruiters quickly understand your profile "
                "and target role."
            ),
            "where_it_appears": "Top of resume — below contact info",
            "how_to_fix": (
                "Add a 2-3 sentence summary highlighting your experience level, key skills, and career "
                "focus. Tailor it to the job you're applying for."
            ),
            "action_items": [
                "Add a 'PROFESSIONAL SUMMARY' section at the top of your resume",
                "Keep it under 60 words — recruiters spend only 6 seconds on first scan",
            ],
            "example_improvement": (
                "Add:\nPROFESSIONAL SUMMARY\nData analyst with 1.5 years of experience turning sales and "
                "customer data into weekly decisions using SQL, Python and Power BI."
            ),
        },
    ],
    "skill_validation_details": {
        "validated": [
            {"skill": "Python", "similarity": 0.95, "projects": ["Churn prediction model", "Retail sales forecasting"]},
            {"skill": "SQL", "similarity": 0.91, "projects": ["Analytics intern, Kirana Labs"]},
            {"skill": "Power BI", "similarity": 0.86, "projects": ["Analytics intern, Kirana Labs"]},
            {"skill": "Pandas", "similarity": 0.83, "projects": ["Retail sales forecasting"]},
            {"skill": "Scikit-learn", "similarity": 0.8, "projects": ["Churn prediction model"]},
            {"skill": "Excel", "similarity": 0.74, "projects": ["Analytics intern, Kirana Labs"]},
            {"skill": "Statistics", "similarity": 0.72, "projects": ["Churn prediction model"]},
            {"skill": "Git", "similarity": 0.66, "projects": ["Retail sales forecasting"]},
        ],
        "unvalidated": ["Tableau", "Airflow", "Spark", "A/B Testing", "Docker", "R"],
        "total": 14,
        "validated_count": 8,
        "validation_pct": 57.1,
    },
    "jd_comparison": {
        "match_percentage": 64.0,
        "semantic_similarity": 0.71,
        "matched_keywords": [
            "SQL", "Python", "Power BI", "dashboards", "data cleaning", "stakeholders",
            "Excel", "forecasting", "statistics", "Pandas",
        ],
        "missing_keywords": ["dbt", "Snowflake", "Looker", "experimentation", "data modeling", "KPIs"],
        "skills_gap": ["dbt", "Snowflake", "Looker"],
    },
    "suggestions": [
        "Lead the Experience section with the forecasting project result — it is the strongest match for this role.",
        "If you have used any cloud warehouse, name it; the job post asks for Snowflake specifically.",
        "Rename 'Tools' to 'Skills' so parsers file it under the standard heading.",
    ],
    "skills": [
        "Python", "SQL", "Power BI", "Pandas", "Scikit-learn", "Excel", "Statistics", "Git",
        "Tableau", "Airflow", "Spark", "A/B Testing", "Docker", "R",
    ],
    "matched_keywords": [],
    "missing_keywords": [],
    "warnings": [],
}
SAMPLE_ANALYSIS["jd_match_analysis"] = SAMPLE_ANALYSIS["jd_comparison"]
