"""
Instant checks for single resume bullets (used by the Bullet Lab page).

Pure Python, no models: the same signals the full scorer rewards in its
Content quality check — an action verb up front, a number, a visible result —
plus the habits that cost points (first person, filler, length).
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple

from backend.services.local_parser import ACTION_VERBS

WEAK_OPENERS = {
    "responsible": "Led, Owned or Managed",
    "worked": "Built, Developed or Delivered",
    "helped": "Contributed to, Co-built or Supported",
    "assisted": "Supported, Partnered on or Contributed to",
    "involved": "Drove, Delivered or Contributed to",
    "participated": "Contributed to or Co-led",
    "tasked": "Owned or Delivered",
    "handled": "Managed, Resolved or Processed",
    "did": "Built, Ran or Delivered",
    "made": "Built, Designed or Created",
    "duties": "Start with what you did, not your duties",
}
FILLER = ["various", "etc", "several", "a lot of", "many different", "things", "stuff", "some ",
          "responsible for", "worked on", "helped with", "duties included", "in charge of"]
PRONOUNS = re.compile(r"\b(i|me|my|we|our|us)\b", re.IGNORECASE)
METRIC = re.compile(r"(\d|%|₹|\$|€|£|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|dozen|hundred|thousand|million)\b|\bx\d|\d+x\b)",
                    re.IGNORECASE)
RESULT = re.compile(
    r"\b(by|resulting|result|cutting|cut|reducing|reduced|increasing|increased|saving|saved|improving|improved|"
    r"raising|raised|boosting|boosted|growing|grew|lowering|lowered|from\s.+\sto|leading to|enabling|so that|"
    r"which|achieving|reaching)\b",
    re.IGNORECASE,
)


@dataclass
class BulletReport:
    text: str
    score: int
    checks: List[Tuple[str, bool]] = field(default_factory=list)
    tip: str = ""


def _first_word(text: str) -> str:
    match = re.match(r"\s*([A-Za-z][A-Za-z'-]*)", text)
    return match.group(1).lower() if match else ""


def check(text: str) -> BulletReport:
    text = re.sub(r"^\s*(?:[•●▪◦■\-–—*·]|\d+[.)])\s*", "", text).strip()
    words = text.split()
    first = _first_word(text)

    weak = first in WEAK_OPENERS
    strong_verb = not weak and (first in ACTION_VERBS or (first.endswith("ed") and len(first) > 4))
    has_metric = bool(METRIC.search(text))
    has_result = bool(RESULT.search(text))
    good_length = 8 <= len(words) <= 32
    no_pronoun = not PRONOUNS.search(text)
    lowered = f" {text.lower()} "
    no_filler = not any(f in lowered for f in FILLER)

    score = (30 * strong_verb + 30 * has_metric + 15 * has_result + 10 * good_length
             + 5 * no_pronoun + 10 * no_filler)

    checks = [
        ("Starts with an action verb", strong_verb),
        ("Has a number", has_metric),
        ("Shows a result", has_result),
        ("8 to 32 words", good_length),
        ("No “I” or “we”", no_pronoun),
        ("No filler", no_filler),
    ]

    if weak:
        tip = f"Swap “{words[0]}” for a verb that shows ownership: {WEAK_OPENERS[first]}."
    elif not strong_verb:
        tip = "Open with a past-tense action verb, e.g. Built, Led, Reduced, Launched."
    elif not has_metric:
        tip = "Add a number: how many users, how much faster, what %, how much money or time."
    elif not has_result:
        tip = "Say what changed because of it: “…, cutting load time by 40%”."
    elif not good_length:
        tip = ("Too short to show impact; add the tool and the outcome." if len(words) < 8
               else "Long bullets get skimmed; split it or cut the context.")
    elif not no_pronoun:
        tip = "Drop “I/we”; resumes are written without pronouns."
    elif not no_filler:
        tip = "Replace vague words (various, several, etc.) with the specific thing."
    else:
        tip = "Strong bullet. Keep this shape for the rest."

    return BulletReport(text=text, score=int(score), checks=checks, tip=tip)


def split_bullets(blob: str) -> List[str]:
    lines = [l.strip() for l in blob.splitlines()]
    return [l for l in lines if len(l.split()) >= 2][:25]
