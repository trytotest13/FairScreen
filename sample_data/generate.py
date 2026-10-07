from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MALE_NAMES = [
    "James Carter", "Rahul Verma", "Daniel Kim", "Omar Haddad", "Peter Novak",
    "Luis Garcia", "Tom Becker", "Arjun Patel", "Marcus Reed", "Ibrahim Osman",
    "Kevin Zhao", "David Miller",
]
FEMALE_NAMES = [
    "Maria Lopez", "Sarah Chen", "Aisha Khan", "Emily Watson", "Nina Petrova",
    "Fatima Noor", "Hannah Lee", "Priya Sharma", "Grace Okafor", "Elena Rossi",
    "Mei Lin", "Dana Sullivan",
]
TIER1 = ["MIT", "Stanford University", "UC Berkeley", "Carnegie Mellon University"]
TIER2 = ["State College", "City University", "Riverdale Institute", "Lakeside College"]
CITIES = ["Austin", "Denver", "Chicago", "Seattle", "Atlanta", "Boston"]

CORE_SKILLS = ["SQL", "Excel", "Tableau", "Data Visualization"]
BONUS_SKILLS = ["Python", "Statistics", "A/B Testing", "Power BI", "Data Warehousing", "Google Analytics", "Machine Learning"]

SAMPLE_JD = (
    "Data Analyst, Growth Team\n\n"
    "We are looking for a data analyst to own reporting and experiments for the growth team.\n\n"
    "Responsibilities:\n"
    "- Build and maintain dashboards in Tableau for marketing and product stakeholders\n"
    "- Write SQL against the warehouse and Python scripts for weekly analysis\n"
    "- Design and evaluate A/B tests with clear statistical rigor\n\n"
    "Requirements:\n"
    "- SQL and Excel fluency\n"
    "- Python (pandas) for analysis\n"
    "- Dashboard experience (Tableau or Power BI)\n"
    "- Statistics and A/B testing fundamentals\n"
    "- Familiarity with data warehousing (Snowflake or BigQuery)\n"
    "- Google Analytics for funnel analysis\n"
)


def build_resume(
    rng: random.Random,
    name: str,
    bonus_count: int,
    experience_years: int,
    tier1: bool,
) -> tuple[str, dict]:
    pronoun = "He" if name in MALE_NAMES else "She"
    possessive = "his" if pronoun == "He" else "her"
    university = rng.choice(TIER1 if tier1 else TIER2)
    grad_year = 2026 - experience_years - rng.randint(0, 2)
    city = rng.choice(CITIES)
    bonus = rng.sample(BONUS_SKILLS, bonus_count)
    skills = sorted(set(CORE_SKILLS + bonus))
    slug = name.lower().replace(" ", ".").replace("..", ".")

    extra_bullets = []
    if "Python" in skills:
        extra_bullets.append(f"- Automated weekly reporting with Python and pandas, cutting manual work by {rng.randint(2, 8)} hours per week")
    if "A/B Testing" in skills:
        extra_bullets.append(f"- Designed {rng.randint(4, 15)} A/B tests with proper power analysis; two won and shipped")
    if "Power BI" in skills:
        extra_bullets.append("- Migrated legacy Excel reports into Power BI models")
    if "Data Warehousing" in skills:
        extra_bullets.append("- Modeled warehouse tables in Snowflake for self-serve analytics")
    if "Machine Learning" in skills:
        extra_bullets.append("- Built a churn-scoring model with scikit-learn used by retention")

    text = (
        f"{name}\n"
        f"{city}, USA\n"
        f"Email: {slug}@example.com | Phone: 555-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}\n\n"
        f"Summary: Data analyst with {experience_years} years of experience turning messy data into "
        f"decisions. {pronoun} enjoys partnering with stakeholders and shipping dashboards people actually use.\n\n"
        f"Education: B.Sc. in Statistics, {university} ({grad_year})\n\n"
        f"Skills: {', '.join(skills)}\n\n"
        "Experience:\n"
        f"- Built Tableau dashboards adopted by {rng.randint(3, 9)} teams\n"
        f"- Wrote advanced SQL and Excel models for weekly and monthly reporting\n"
        + ("\n".join(extra_bullets) + "\n" if extra_bullets else "")
        + f"- {pronoun.replace('He', 'Led').replace('She', 'Led')} weekly metric reviews; {possessive} documentation became the team reference\n"
    )
    meta = {
        "filename": f"{slug}.txt",
        "name": name,
        "group": "male" if name in MALE_NAMES else "female",
        "tier": "tier1" if tier1 else "tier2",
        "experience_years": experience_years,
        "skills": len(skills),
    }
    return text, meta


def build_fixture(out_dir: Path, seed: int = 42) -> "list[dict]":
    """24 synthetic resumes: 12 male-named, 12 female-named.

    The fixture deliberately gives female-named candidates fewer bonus skills
    on average so the 4/5ths audit has a disparity to detect. This is a
    generated demo fixture, labeled synthetic everywhere it appears.
    """
    rng = random.Random(seed)
    rows: list[dict] = []
    resumes_dir = out_dir / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)

    for index, name in enumerate(MALE_NAMES + FEMALE_NAMES):
        is_male = index < len(MALE_NAMES)
        experience = rng.randint(2, 9)
        # group skill gap: male candidates average ~4 bonus skills, female ~2
        bonus_count = rng.randint(3, 5) if is_male else rng.randint(1, 3)
        tier1 = rng.random() < 0.4
        text, meta = build_resume(rng, name, bonus_count, experience, tier1)
        (resumes_dir / meta["filename"]).write_text(text, encoding="utf-8")
        rows.append(meta)

    import csv

    with (out_dir / "metadata.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["filename", "name", "group", "tier", "experience_years", "skills"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the synthetic candidate fixture")
    parser.add_argument("--out", default=str(ROOT / "sample_data" / "out"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rows = build_fixture(Path(args.out), seed=args.seed)
    print(f"Generated {len(rows)} resumes + metadata.csv under {args.out}")
    print("The fixture is synthetic: names, universities and skill sets are generated, not real people.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
