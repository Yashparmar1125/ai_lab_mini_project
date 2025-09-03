"""
Resume Analyzer – Company–Applicant Match + Grammarly-style Feedback

Run locally:
  python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
  pip install -r requirements.txt  # OR: pip install flask scikit-learn nltk textstat language_tool_python
  python app.py

Notes:
- Grammar checks via language_tool_python are optional and will auto-disable if Java or the package isn't available.
- This is an in-memory MVP. Swap the simple dict stores with a DB for production.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Optional deps: gracefully degrade if unavailable
try:
    import textstat  # readability metrics
except Exception:  # pragma: no cover
    textstat = None

try:
    import language_tool_python  # grammar/style
except Exception:  # pragma: no cover
    language_tool_python = None


# ----------------------------
# Simple in-memory data stores
# ----------------------------
@dataclass
class Company:
    company_id: int
    name: str
    requirements: dict  # {skills: [..], experience: int, education: [..]}


@dataclass
class Candidate:
    candidate_id: int
    name: str
    resume_text: str


companies: Dict[int, Company] = {}
candidates: Dict[int, Candidate] = {}


# ----------------------------
# Utility: text normalization
# ----------------------------
def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9+.#/\- ]+", " ", s)  # allow tech tokens like c++, .net, node.js
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(s: str) -> List[str]:
    return normalize(s).split()


# ----------------------------
# Skill lexicon (expand as needed)
# ----------------------------
DEFAULT_SKILLS = {
    "python", "java", "c", "c++", "c#", ".net", "javascript", "typescript", "node", "node.js",
    "react", "angular", "vue", "django", "flask", "spring", "fastapi",
    "sql", "mysql", "postgres", "mongodb", "redis", "elasticsearch",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "linux",
    "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch", "nlp", "llm",
    "machine learning", "deep learning", "data science", "etl", "airflow",
}

# Map common synonyms/aliases → canonical
SKILL_SYNONYMS = {
    "js": "javascript",
    "ts": "typescript",
    "tf": "tensorflow",
    "scikit learn": "scikit-learn",
    "ml": "machine learning",
    "dl": "deep learning",
    "postgresql": "postgres",
}


def canonicalize_skill(tok: str) -> str:
    t = tok.strip().lower()
    t = SKILL_SYNONYMS.get(t, t)
    return t


def extract_skills(text: str, custom_list: Optional[List[str]] = None) -> List[str]:
    """Very light keyword-based skill extraction.
    For production, replace with an NER/section-aware extractor.
    """
    toks = tokenize(text)
    uni = set()

    # Unigrams
    for t in toks:
        c = canonicalize_skill(t)
        if c in DEFAULT_SKILLS:
            uni.add(c)

    # Bigrams for phrases like 'machine learning', 'data science'
    for a, b in zip(toks, toks[1:]):
        bigram = canonicalize_skill(f"{a} {b}")
        if bigram in DEFAULT_SKILLS:
            uni.add(bigram)

    # Add any custom skills provided by the company
    if custom_list:
        for s in custom_list:
            s_norm = canonicalize_skill(s)
            if s_norm in normalize(text):
                uni.add(s_norm)

    return sorted(uni)


# ----------------------------
# Experience & Education checks
# ----------------------------
YEAR_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.I)


def extract_years_of_experience(text: str) -> Optional[float]:
    matches = [float(m.group(1)) for m in YEAR_PATTERN.finditer(text)]
    return max(matches) if matches else None


EDU_KEYWORDS = {
    "computer science", "information technology", "data science", "software engineering",
    "electronics", "electrical", "mathematics", "statistics", "ai", "artificial intelligence",
}

DEGREE_KEYWORDS = {"bsc", "b.tech", "btech", "be", "msc", "m.tech", "mtech", "ms", "phd"}


def education_match_score(requirements: dict, resume_text: str) -> int:
    req_edus = [normalize(x) for x in requirements.get("education", [])]
    r = normalize(resume_text)

    has_degree = any(d in r for d in DEGREE_KEYWORDS)
    edu_field_match = any(e in r for e in EDU_KEYWORDS) or any(e in r for e in req_edus)

    if req_edus and edu_field_match and has_degree:
        return 100
    if edu_field_match or has_degree:
        return 70
    return 40


# ----------------------------
# Similarity scoring (TF‑IDF)
# ----------------------------
def tfidf_cosine(a: str, b: str) -> float:
    vec = TfidfVectorizer()
    m = vec.fit_transform([a, b])
    return float(cosine_similarity(m[0:1], m[1:2])[0][0])


# ----------------------------
# Fit analysis (weighted)
# ----------------------------
def compute_fit(requirements: dict, resume_text: str) -> Tuple[float, dict]:
    # Requirements flattening for semantic similarity
    req_text = " ".join(requirements.get("skills", [])) + " " + " ".join(requirements.get("education", []))
    if "experience" in requirements:
        req_text += f" {requirements['experience']} years experience"

    sim = tfidf_cosine(req_text, resume_text)  # 0..1

    # Skills score via Jaccard overlap
    req_skills = [canonicalize_skill(s) for s in requirements.get("skills", [])]
    cand_skills = extract_skills(resume_text, custom_list=req_skills)
    set_req, set_cand = set(req_skills), set(cand_skills)
    jacc = len(set_req & set_cand) / len(set_req) if set_req else 1.0
    skills_score = int(round(jacc * 100))

    # Experience score
    req_years = requirements.get("experience")
    cand_years = extract_years_of_experience(resume_text) or 0
    if req_years is None or req_years == 0:
        exp_score = 100
    else:
        # Full score if cand_years >= req_years, else scale linearly down to 40
        if cand_years >= req_years:
            exp_score = 100
        else:
            ratio = max(0.0, cand_years / float(req_years))
            exp_score = int(40 + 60 * ratio)  # min 40 if mentioned but below

    # Education score
    edu_score = education_match_score(requirements, resume_text)

    # Weighted overall
    weights = {"skills": 0.6, "experience": 0.25, "education": 0.15}
    overall = (
            skills_score * weights["skills"]
            + exp_score * weights["experience"]
            + edu_score * weights["education"]
    )

    # Blend with semantic similarity to avoid keyword gaming (10% weight)
    overall = 0.9 * overall + 0.1 * (sim * 100)

    breakdown = {
        "skills": skills_score,
        "experience": exp_score,
        "education": edu_score,
        "semantic": int(round(sim * 100)),
        "matched_skills": sorted(list(set_req & set_cand)),
        "missing_skills": sorted(list(set_req - set_cand)),
    }

    return round(overall, 2), breakdown


# ----------------------------
# Grammarly-style resume feedback
# ----------------------------
ACTION_VERBS = [
    "built", "developed", "designed", "led", "optimized", "implemented", "launched",
    "automated", "reduced", "increased", "improved", "delivered", "owned", "created",
    "engineered", "constructed", "initiated", "executed", "analyzed", "produced",
]

GENERIC_PHRASES = [
    "responsible for", "worked on", "helped with", "involved in", "participated in",
    "hardworking", "team player", "result-oriented", "self-starter",
]

PASSIVE_HINT = re.compile(r"\b(?:was|were|is|are|been|being|be)\b\s+\w+ed\b.*?(?:\bby\b)?", re.I)

SECTIONS = [
    "education", "experience", "projects", "skills", "certifications",
    "summary", "achievements", "objective", "internships", "work"
]


def resume_quality(resume_text: str) -> Dict[str, object]:
    tips: List[str] = []
    text_norm = normalize(resume_text)

    # Section presence
    missing_sections = [s for s in SECTIONS if s not in text_norm]
    if missing_sections:
        tips.append(f"Consider adding sections: {', '.join(missing_sections[:3])}.")

    # Action verbs
    if not any(av in text_norm for av in ACTION_VERBS):
        tips.append("Use strong action verbs (e.g., built, optimized, implemented) at bullet starts.")

    # Generic phrasing
    for gp in GENERIC_PHRASES:
        if gp in text_norm:
            tips.append(f"Replace generic phrase '{gp}' with specific, impact-focused wording.")
            break

    # Passive voice hint
    if PASSIVE_HINT.search(resume_text):
        tips.append("Reduce passive voice; prefer active constructions (e.g., 'Designed X' vs 'X was designed').")

    # Quantification
    if re.search(r"\b\d+%\b", resume_text) is None and re.search(r"\b\d+\b", resume_text) is None:
        tips.append("Quantify impact with numbers (e.g., 'reduced latency by 35%').")

    # Readability
    readability = {}
    if textstat is not None:
        try:
            readability = {
                "flesch_reading_ease": textstat.flesch_reading_ease(resume_text),
                "smog_index": textstat.smog_index(resume_text),
                "avg_sentence_length": textstat.avg_sentence_length(resume_text),
            }
            tips.append("Aim for concise bullets (typically 10–20 words). Avoid long sentences.")
        except Exception:
            pass

    # Grammar via LanguageTool (optional)
    grammar_issues = []
    if language_tool_python is not None:
        try:
            tool = language_tool_python.LanguageTool("en-US")
            matches = tool.check(resume_text)
            # Deduplicate messages and keep top 10
            seen = set()
            for m in matches:
                msg = m.message.strip()
                if msg and msg not in seen:
                    grammar_issues.append(msg)
                    seen.add(msg)
                if len(grammar_issues) >= 10:
                    break
        except Exception:
            # If Java unavailable or tool fails, skip silently
            pass

    return {
        "readability": readability,
        "grammar_issues": grammar_issues,
        "suggestions": tips,
    }
