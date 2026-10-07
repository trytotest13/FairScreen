from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

# Skills lexicon: canonical name -> aliases (lowercase, word-boundary matched).
# This is data on purpose: recruiters can extend it without touching scoring code.
SKILL_LEXICON: dict[str, list[str]] = {
    "SQL": ["sql"],
    "Python": ["python", "pandas", "numpy"],
    "Excel": ["excel", "vlookup", "pivot tables"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi", "dax"],
    "R": ["r language", " rstudio", " ggplot"],
    "Statistics": ["statistics", "statistical", "hypothesis testing", "regression"],
    "A/B Testing": ["a/b testing", "ab testing", "experimentation"],
    "Data Visualization": ["data visualization", "dashboards", "charting"],
    "ETL": ["etl", "data pipelines", "airflow", "dbt"],
    "Data Warehousing": ["data warehouse", "snowflake", "redshift", "bigquery"],
    "Machine Learning": ["machine learning", "scikit-learn", "sklearn"],
    "Deep Learning": ["deep learning", "pytorch", "tensorflow", "neural network"],
    "NLP": ["nlp", "natural language processing", "llm", "transformers"],
    "Computer Vision": ["computer vision", "opencv", "image classification"],
    "Spark": ["spark", "pyspark", "hadoop"],
    "AWS": ["aws", "s3", "lambda", "ec2"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker", "containeriz"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git", "github", "gitlab"],
    "PostgreSQL": ["postgres", "postgresql"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "API Development": ["rest api", "fastapi", "flask", "django", "api development"],
    "Google Analytics": ["google analytics", "ga4"],
    "Looker": ["looker", "lookml"],
    "Project Management": ["project management", "agile", "scrum", "stakeholder"],
}

_WORD = re.compile(r"[a-z0-9][a-z0-9+\-/. ]*")


@dataclass
class MatchResult:
    filename: str
    score: float
    text_similarity: float
    skill_coverage: float
    jd_skills: list[str]
    gaps: list[str] = field(default_factory=list)


def _contains(text: str, needle: str) -> bool:
    needle = needle.strip()
    if " " in needle:
        return needle in text
    # short aliases need boundaries: "dax" must not match "guidance"
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text) is not None


def extract_skills(text: str) -> list[str]:
    lowered = " " + re.sub(r"\s+", " ", text.lower()) + " "
    found = []
    for skill, aliases in SKILL_LEXICON.items():
        if any(_contains(lowered, alias) for alias in aliases):
            found.append(skill)
    return found


@lru_cache(maxsize=1)
def _semantic_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def semantic_similarity(text_a: str, texts_b: list[str]) -> list[float]:
    model = _semantic_model()
    embeddings_a = model.encode([text_a], normalize_embeddings=True)
    embeddings_b = model.encode(texts_b, normalize_embeddings=True)
    return (embeddings_a @ embeddings_b.T)[0].tolist()


def tfidf_similarity(query: str, documents: list[str]) -> list[float]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform([query] + documents)
    return cosine_similarity(matrix[0:1], matrix[1:]).flatten().tolist()


def rank(
    jd_text: str,
    resumes: list[tuple[str, str]],
    use_semantic: bool = False,
) -> tuple[list[MatchResult], str]:
    """Returns (ranked results, engine_used). Resumes are (filename, text) pairs."""
    if not resumes:
        return [], "none"
    engine = "tfidf"
    try:
        if use_semantic:
            similarities = semantic_similarity(jd_text, [text for _, text in resumes])
            engine = "semantic"
        else:
            raise RuntimeError("semantic disabled")
    except Exception:
        similarities = tfidf_similarity(jd_text, [text for _, text in resumes])
        engine = "tfidf"

    jd_skills = extract_skills(jd_text)
    results: list[MatchResult] = []
    for (filename, text), similarity in zip(resumes, similarities):
        candidate_skills = extract_skills(text)
        matched = [s for s in jd_skills if s in candidate_skills]
        coverage = len(matched) / len(jd_skills) if jd_skills else 0.0
        score = 0.6 * float(similarity) + 0.4 * coverage
        results.append(
            MatchResult(
                filename=filename,
                score=round(score, 4),
                text_similarity=round(float(similarity), 4),
                skill_coverage=round(coverage, 4),
                jd_skills=jd_skills,
                gaps=[s for s in jd_skills if s not in candidate_skills],
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return results, engine
