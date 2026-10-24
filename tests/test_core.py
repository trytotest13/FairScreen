import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fairscreen.bias import four_fifths_audit, proxy_flags, redact
from fairscreen.matching import extract_skills, rank
from fairscreen.parsing import extract_text
from sample_data.generate import SAMPLE_JD, build_fixture


def test_redact_removes_all_pii():
    text = (
        "CURRICULUM VITAE\n"
        "Jane Doe\n"
        "jane.doe@example.com | 555-123-4567\n"
        "github.com/janedoe\n"
        "Experienced analyst with SQL and Python."
    )
    result = redact(text)
    assert "jane.doe@example.com" not in result.text
    assert "555-123-4567" not in result.text
    assert "github.com" not in result.text
    assert "Jane Doe" not in result.text
    assert "CURRICULUM VITAE" in result.text  # all-caps headings are kept, not treated as names
    assert set(result.removed) == {"email", "phone", "link", "name line"}
    assert "SQL and Python" in result.text


def test_proxy_flags_detect_years_and_pronouns():
    text = "Graduated in 2019 from State College. She led the analytics team. 42 Wall Street."
    flags = {flag["category"]: flag["fragment"] for flag in proxy_flags(text)}
    assert "graduation years" in flags and "2019" in flags["graduation years"]
    assert "gendered pronouns" in flags and "she" in flags["gendered pronouns"]
    assert "street address" in flags


def test_four_fifths_audit_flags_disparity():
    ranked = (
        [{"filename": f"m{i}", "group": "A"} for i in range(10)]
        + [{"filename": f"f{i}", "group": "B"} for i in range(10)]
    )
    # cutoff 8 selects 8 of group A and 0 of group B
    audit = four_fifths_audit(ranked, cutoff=8)
    assert audit is not None and audit.flagged is True
    assert audit.ratio == 0.0
    assert audit.groups["A"]["selected"] == 8
    assert audit.groups["B"]["selected"] == 0


def test_four_fifths_audit_passes_balanced_selection():
    ranked = [{"filename": f"a{i}", "group": "A"} for i in range(10)] + [
        {"filename": f"b{i}", "group": "B"} for i in range(10)
    ]
    # interleave so both groups get 4 of the top 8
    balanced = [row for pair in zip(ranked[:10], ranked[10:]) for row in pair]
    audit = four_fifths_audit(balanced, cutoff=8)
    assert audit is not None and audit.flagged is False
    assert audit.ratio == 1.0


def test_four_fifths_audit_returns_none_without_groups():
    ranked = [{"filename": "x"}, {"filename": "y"}]
    assert four_fifths_audit(ranked, cutoff=1) is None


def test_skill_extraction_boundaries():
    text = "Built dashboards with DAX in Power BI and wrote SQL queries. Read a guidance document."
    skills = extract_skills(text)
    assert "SQL" in skills
    assert "Power BI" in skills
    assert "R" not in skills  # 'r' alone must not match inside words


def test_rank_components_and_gaps():
    jd = SAMPLE_JD
    strong = (
        "Analyst with SQL, Excel, Tableau, Python pandas, A/B testing and Google Analytics experience. "
        "Statistics background, built Snowflake dashboards."
    )
    weak = "Marketing assistant, made flyers and social posts."
    results, engine = rank(jd, [("strong.txt", strong), ("weak.txt", weak)], use_semantic=False)
    assert engine == "tfidf"
    strong_result, weak_result = results  # sorted by score
    assert strong_result.filename == "strong.txt"
    assert strong_result.skill_coverage > weak_result.skill_coverage
    # every gap must be a JD skill, and the strong candidate misses fewer
    assert set(strong_result.gaps).issubset(set(strong_result.jd_skills))
    assert len(strong_result.gaps) < len(weak_result.gaps)
    assert weak_result.skill_coverage == 0.0


def test_fixture_generates_deterministically(tmp_path):
    rows_a = build_fixture(tmp_path / "a", seed=42)
    rows_b = build_fixture(tmp_path / "b", seed=42)
    assert rows_a == rows_b
    groups = {row["group"] for row in rows_a}
    assert groups == {"male", "female"}
    assert len(rows_a) == 24
    # text files parse cleanly
    first = next((tmp_path / "a" / "resumes").glob("*.txt"))
    assert "Skills:" in extract_text(first)
