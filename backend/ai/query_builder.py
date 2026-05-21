import re
from collections import Counter

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "you", "your", "will", "can", "all", "not", "but", "they",
    "their", "our", "about", "into", "over", "under", "using", "used", "use",
    "work", "worked", "experience", "years", "year", "responsible", "looking",
    "resume", "candidate", "skills", "skill", "knowledge", "ability", "able"
}

ROLE_KEYWORDS = [
    "developer",
    "engineer",
    "analyst",
    "data analyst",
    "software developer",
    "python developer",
    "machine learning engineer",
    "business analyst",
    "frontend developer",
    "backend developer",
    "full stack developer",
]

TECH_SKILLS = [
    "python",
    "sql",
    "postgresql",
    "mysql",
    "excel",
    "power bi",
    "tableau",
    "data analysis",
    "machine learning",
    "pandas",
    "numpy",
    "fastapi",
    "flask",
    "django",
    "javascript",
    "typescript",
    "react",
    "node",
    "docker",
    "aws",
    "azure",
    "git",
    "api",
    "rest api",
]


def normalize_text(text: str) -> str:
    return (text or "").lower().replace("/", " ")


def extract_skills(resume_text: str) -> list[str]:
    text = normalize_text(resume_text)
    found = []

    for skill in TECH_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found.append(skill)

    return found


def extract_role(resume_text: str) -> str:
    text = normalize_text(resume_text)

    for role in ROLE_KEYWORDS:
        if role in text:
            return role

    if "python" in text:
        return "python developer"

    if "data" in text or "sql" in text or "excel" in text or "power bi" in text:
        return "data analyst"

    if "javascript" in text or "react" in text:
        return "frontend developer"

    return "software developer"


def build_query(resume_text: str) -> str:
    """
    Main query for logging/UI.
    Keep it broad, not too restrictive.
    """
    role = extract_role(resume_text)
    skills = extract_skills(resume_text)

    if not skills:
        return role

    # Only 1-2 strongest skills in the main query.
    # Long query kills Adzuna results.
    return " ".join([role] + skills[:2])


def build_search_queries(resume_text: str) -> list[str]:
    """
    Query expansion for Adzuna.
    Instead of sending one long query, send multiple broad queries,
    then merge vacancies and rank locally.
    """
    role = extract_role(resume_text)
    skills = extract_skills(resume_text)

    queries = []

    # 1. broad role query
    queries.append(role)

    # 2. role + each skill
    for skill in skills:
        if skill in {"python", "javascript", "typescript", "java"}:
            queries.append(f"{skill} developer")
        elif skill in {"sql", "excel", "power bi", "tableau", "data analysis"}:
            queries.append(f"{skill} analyst")
        elif skill in {"machine learning", "pandas", "numpy"}:
            queries.append("machine learning data")
        elif skill in {"fastapi", "flask", "django"}:
            queries.append(f"python {skill}")
        elif skill in {"docker", "aws", "azure"}:
            queries.append(f"{role} {skill}")
        else:
            queries.append(skill)

    # 3. fallback if resume is very short
    if not queries:
        queries = ["software developer", "python developer", "data analyst"]

    # remove duplicates, keep order
    unique = []
    for q in queries:
        q = q.strip()
        if q and q not in unique:
            unique.append(q)

    return unique[:8]


def choose_alpha(resume_text: str) -> float:
    words = re.findall(r"\w+", resume_text or "")

    if len(words) < 30:
        return 0.35

    if len(words) < 120:
        return 0.50

    return 0.65