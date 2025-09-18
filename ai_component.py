"""
Advanced Resume Analyzer – AI-Powered Company–Applicant Match + Comprehensive Feedback

Features:
- Advanced skill extraction with semantic matching
- Experience level detection and validation
- Education background analysis
- Resume quality scoring with detailed feedback
- ATS optimization suggestions
- Keyword density analysis
- Action verb optimization
- Contact information validation
- Professional summary analysis

Run locally:
  python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
  pip install -r requirements.txt
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
    # Programming Languages
    "python", "java", "c", "c++", "c#", ".net", "javascript", "typescript", "node", "node.js", "go", "golang", "rust", "php", "ruby", "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css", "sass", "scss",
    
    # Web Technologies
    "react", "angular", "vue", "svelte", "next.js", "nuxt.js", "gatsby", "express", "nest.js", "django", "flask", "fastapi", "spring", "spring boot", "laravel", "symfony", "rails", "asp.net", "dotnet",
    
    # Mobile Development
    "react native", "flutter", "xamarin", "ionic", "cordova", "progressive web apps", "pwa",
    
    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "neo4j", "sqlite", "oracle", "sql server", "mariadb", "couchdb", "influxdb", "firebase",
    
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "ansible", "chef", "puppet", "jenkins", "gitlab ci", "github actions", "circleci", "travis ci", "bamboo", "spinnaker",
    
    # Data Science & AI
    "machine learning", "ml", "deep learning", "dl", "artificial intelligence", "ai", "data science", "data analysis", "pandas", "numpy", "scipy", "tensorflow", "tf", "pytorch", "keras", "scikit-learn", "sklearn", "opencv", "nlp", "natural language processing", "computer vision", "neural networks", "statistics", "analytics", "tableau", "power bi", "looker", "qlik", "excel", "vba", "spark", "hadoop", "kafka", "airflow", "dbt", "etl",
    
    # Testing & Quality
    "unit testing", "integration testing", "test automation", "selenium", "cypress", "jest", "mocha", "chai", "pytest", "junit", "testng", "cucumber", "bdd", "tdd", "code review", "static analysis", "sonarqube", "eslint", "prettier",
    
    # Security
    "cybersecurity", "penetration testing", "vulnerability assessment", "security auditing", "owasp", "firewall", "ssl", "tls", "oauth", "oauth2", "jwt", "rbac", "encryption", "cryptography", "secure coding", "security compliance", "gdpr", "hipaa", "pci dss",
    
    # System Administration
    "linux", "windows", "unix", "bash", "powershell", "shell scripting", "system administration", "network administration", "monitoring", "logging", "prometheus", "grafana", "elk stack", "splunk", "new relic", "datadog", "zabbix", "nagios",
    
    # Architecture & Design
    "microservices", "rest api", "graphql", "websocket", "grpc", "soap", "api design", "system design", "distributed systems", "load balancing", "caching", "cdn", "message queues", "event streaming", "cqrs", "event sourcing", "domain driven design", "clean architecture", "hexagonal architecture",
    
    # Project Management & Soft Skills
    "agile", "scrum", "kanban", "waterfall", "project management", "leadership", "mentoring", "communication", "problem solving", "critical thinking", "teamwork", "time management", "adaptability", "creativity", "attention to detail", "customer service", "stakeholder management", "risk management", "change management",
    
    # Industry Specific
    "fintech", "healthcare", "e-commerce", "gaming", "edtech", "saas", "paas", "iaas", "blockchain", "cryptocurrency", "iot", "ar", "vr", "metaverse", "quantum computing", "edge computing", "serverless", "lambda", "api gateway", "service mesh", "istio", "linkerd",
    
    # Tools & Platforms
    "git", "jira", "confluence", "slack", "teams", "zoom", "figma", "sketch", "adobe", "photoshop", "illustrator", "invision", "zeplin", "notion", "trello", "asana", "monday.com", "clickup"
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
    "go": "golang",
    "k8s": "kubernetes",
    "ai": "artificial intelligence",
    "data eng": "data engineering",
    "big data": "data science",
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
        # Canonicalize custom skills once
        canonical_custom_skills = {canonicalize_skill(s) for s in custom_list}
        for t in toks:
            c = canonicalize_skill(t)
            if c in canonical_custom_skills:
                uni.add(c)
        # Check bigrams for custom skills
        for a, b in zip(toks, toks[1:]):
            bigram = canonicalize_skill(f"{a} {b}")
            if bigram in canonical_custom_skills:
                uni.add(bigram)

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
    "machine learning", "cyber security", "network engineering", "cloud computing",
    "business administration", "finance", "marketing", "design", "physics", "chemistry",
}

DEGREE_KEYWORDS = {"bsc", "b.tech", "btech", "be", "msc", "m.tech", "mtech", "ms", "phd",
                   "bachelor", "master", "doctorate", "associate", "diploma"}


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
    "managed", "mentored", "collaborated", "pioneered", "streamlined", "transformed",
    "generated", "identified", "resolved", "researched", "trained", "verified", "conceptualized",
]

GENERIC_PHRASES = [
    "responsible for", "worked on", "helped with", "involved in", "participated in",
    "hardworking", "team player", "result-oriented", "self-starter",
    "duties included", "tasked with", "a strong communicator", "goal-oriented", "flexible",
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


# ----------------------------
# Advanced Resume Analysis Functions
# ----------------------------

def analyze_contact_info(resume_text: str) -> dict:
    """Analyze contact information completeness and format."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    linkedin_pattern = r'linkedin\.com/in/[\w-]+'
    github_pattern = r'github\.com/[\w-]+'
    
    email = bool(re.search(email_pattern, resume_text))
    phone = bool(re.search(phone_pattern, resume_text))
    linkedin = bool(re.search(linkedin_pattern, resume_text, re.IGNORECASE))
    github = bool(re.search(github_pattern, resume_text, re.IGNORECASE))
    
    issues = []
    if not email:
        issues.append("Missing email address")
    if not phone:
        issues.append("Missing phone number")
    if not linkedin:
        issues.append("Consider adding LinkedIn profile")
    if not github and any(tech in resume_text.lower() for tech in ['developer', 'programmer', 'engineer', 'coding']):
        issues.append("Consider adding GitHub profile for technical roles")
    
    return {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "issues": issues,
        "completeness_score": (email + phone + linkedin + github) * 25
    }


def analyze_keyword_density(resume_text: str, target_keywords: list) -> dict:
    """Analyze keyword density and distribution."""
    text_lower = resume_text.lower()
    word_count = len(text_lower.split())
    
    keyword_counts = {}
    for keyword in target_keywords:
        count = text_lower.count(keyword.lower())
        density = (count / word_count * 100) if word_count > 0 else 0
        keyword_counts[keyword] = {
            "count": count,
            "density": round(density, 2)
        }
    
    # Calculate overall keyword density
    total_keyword_count = sum(kw["count"] for kw in keyword_counts.values())
    overall_density = (total_keyword_count / word_count * 100) if word_count > 0 else 0
    
    # Recommendations
    recommendations = []
    if overall_density < 1.0:
        recommendations.append("Increase keyword density - aim for 1-2%")
    elif overall_density > 3.0:
        recommendations.append("Reduce keyword density - avoid keyword stuffing")
    
    for keyword, data in keyword_counts.items():
        if data["count"] == 0:
            recommendations.append(f"Consider adding '{keyword}' if relevant")
        elif data["density"] > 2.0:
            recommendations.append(f"Reduce overuse of '{keyword}'")
    
    return {
        "keyword_counts": keyword_counts,
        "overall_density": round(overall_density, 2),
        "recommendations": recommendations
    }


def analyze_professional_summary(resume_text: str) -> dict:
    """Analyze professional summary/objective section."""
    # Look for common summary section patterns
    summary_patterns = [
        r'(?:summary|profile|objective|about me)[:\s]*(.+?)(?:\n\n|\n[A-Z]|$)',
        r'^(?!.*(?:experience|education|skills)).{50,200}(?=\n\n|\n[A-Z])',
    ]
    
    summary_found = False
    summary_text = ""
    for i, pattern in enumerate(summary_patterns):
        match = re.search(pattern, resume_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            # For the second pattern, use group(0) since it doesn't have capture groups
            if i == 1:
                summary_text = match.group(0).strip()
            else:
                summary_text = match.group(1).strip()
            summary_found = True
            break
    
    issues = []
    suggestions = []
    
    if not summary_found:
        issues.append("Missing professional summary section")
        suggestions.append("Add a compelling 2-3 line professional summary")
    else:
        summary_length = len(summary_text.split())
        if summary_length < 20:
            issues.append("Professional summary too short")
            suggestions.append("Expand summary to 20-50 words")
        elif summary_length > 100:
            issues.append("Professional summary too long")
            suggestions.append("Keep summary concise (20-50 words)")
        
        # Check for action verbs
        action_verbs_found = any(verb in summary_text.lower() for verb in ACTION_VERBS)
        if not action_verbs_found:
            suggestions.append("Use strong action verbs in summary")
        
        # Check for quantifiable achievements
        has_numbers = bool(re.search(r'\b\d+%|\b\d+\s*(?:years?|months?|people|projects?|dollars?|%)', summary_text))
        if not has_numbers:
            suggestions.append("Include quantifiable achievements in summary")
    
    return {
        "found": summary_found,
        "text": summary_text,
        "word_count": len(summary_text.split()) if summary_text else 0,
        "issues": issues,
        "suggestions": suggestions
    }


def analyze_ats_optimization(resume_text: str) -> dict:
    """Analyze ATS (Applicant Tracking System) optimization."""
    issues = []
    suggestions = []
    
    # Check for common ATS issues
    if re.search(r'[^\x00-\x7F]', resume_text):
        issues.append("Contains non-ASCII characters that may cause ATS issues")
        suggestions.append("Use standard ASCII characters only")
    
    if re.search(r'[^\w\s\-\.\,\:\;\(\)\[\]\/]', resume_text):
        issues.append("Contains special characters that may confuse ATS")
        suggestions.append("Avoid excessive special characters")
    
    # Check for tables or complex formatting
    if re.search(r'\|.*\|', resume_text):
        issues.append("Contains tables which may not parse well in ATS")
        suggestions.append("Convert tables to bullet points or simple text")
    
    # Check for headers
    if not re.search(r'^(experience|work history|employment)', resume_text, re.MULTILINE | re.IGNORECASE):
        issues.append("Missing clear 'Experience' section header")
        suggestions.append("Use standard section headers: Experience, Education, Skills")
    
    if not re.search(r'^(education|academic)', resume_text, re.MULTILINE | re.IGNORECASE):
        issues.append("Missing clear 'Education' section header")
    
    if not re.search(r'^(skills|technical skills|technologies)', resume_text, re.MULTILINE | re.IGNORECASE):
        issues.append("Missing clear 'Skills' section header")
    
    # Check for consistent date formatting
    date_patterns = re.findall(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\s*[-–]\s*\d{4}\b', resume_text, re.IGNORECASE)
    if len(set(date_patterns)) > 3:
        issues.append("Inconsistent date formatting")
        suggestions.append("Use consistent date format (e.g., MM/YYYY)")
    
    return {
        "issues": issues,
        "suggestions": suggestions,
        "ats_score": max(0, 100 - len(issues) * 15)
    }


def comprehensive_resume_analysis(resume_text: str, target_skills: list = None) -> dict:
    """Perform comprehensive resume analysis with all advanced features."""
    if target_skills is None:
        target_skills = []
    
    # Basic analysis
    quality = resume_quality(resume_text)
    contact = analyze_contact_info(resume_text)
    summary = analyze_professional_summary(resume_text)
    ats = analyze_ats_optimization(resume_text)
    
    # Keyword analysis if target skills provided
    keyword_analysis = {}
    if target_skills:
        keyword_analysis = analyze_keyword_density(resume_text, target_skills)
    
    # Calculate overall score
    scores = [
        quality.get('readability', {}).get('flesch_reading_ease', 0) / 10,  # 0-10
        contact['completeness_score'],  # 0-100
        ats['ats_score'],  # 0-100
        80 if summary['found'] else 0,  # 0-80
    ]
    
    if keyword_analysis:
        scores.append(min(100, keyword_analysis['overall_density'] * 50))  # 0-100
    
    overall_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "overall_score": round(overall_score, 1),
        "quality_analysis": quality,
        "contact_analysis": contact,
        "summary_analysis": summary,
        "ats_analysis": ats,
        "keyword_analysis": keyword_analysis,
        "recommendations": {
            "priority": [
                "Focus on quantifiable achievements",
                "Use strong action verbs",
                "Optimize for ATS compatibility",
                "Include relevant keywords naturally"
            ],
            "quick_wins": [
                "Add missing contact information",
                "Include professional summary",
                "Use consistent formatting",
                "Proofread for grammar errors"
            ]
        }
    }
