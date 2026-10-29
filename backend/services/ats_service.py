import sys
import re
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlmodel import Session
from src.exception import CustomException
from backend.models.database import engine
from backend.models.schemas import ResumeAnalysis
from backend.output_parsers import ResumeSchema, JDSchema

logger = logging.getLogger(__name__)

# Weights must sum to 1.0
WEIGHTS: Dict[str, float] = {
    "keyword_match": 0.40,
    "skills_coverage": 0.20,
    "title_match": 0.15,
    "section_completeness": 0.15,
    "date_consistency": 0.10,
}

# Title match constants
_TITLE_IN_HEADLINE = 100.0
_TITLE_IN_SUMMARY = 75.0
_TITLE_OVERLAP_MAX = 50.0
_TITLE_STOPWORDS = frozenset(
    {"a", "an", "and", "the", "of", "for", "in", "to", "at", "&", "or"}
)

# Date style patterns
_YEAR = r"(?:19|20)\d{2}"
_MONTH = (
    r"(?i:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?"
    r"|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_DATE_PATTERN = re.compile(
    rf"(?P<iso>\b{_YEAR}[-/]\d{{1,2}}\b)"
    rf"|(?P<numeric>\b\d{{1,2}}[/.-]{_YEAR}\b)"
    rf"|(?P<name_year>\b{_MONTH}\.?,?\s+{_YEAR}\b)"
    rf"|(?P<name_short_year>\b{_MONTH}\.?\s+'\d{{2}}\b)"
    rf"|(?P<year>\b{_YEAR}\b)"
)
_MIN_DATES_FOR_CONSISTENCY = 2


def keyword_in_text(keyword: str, text: str) -> bool:
    """Checks whether a keyword appears as a whole word/phrase in text."""
    try:
        if not keyword or not text:
            return False
        pattern = r"(?<!\w)" + re.escape(keyword.strip()) + r"(?!\w)"
        return bool(re.search(pattern, text, re.IGNORECASE))
    except Exception as e:
        raise CustomException(e, sys)


def _normalize_to_dict(obj: Any) -> Any:
    """Recursively converts Pydantic models and nested structures to plain Python dictionaries."""
    if hasattr(obj, "model_dump"):
        return _normalize_to_dict(obj.model_dump())
    if isinstance(obj, dict):
        return {k: _normalize_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_to_dict(item) for item in obj]
    return obj


def _extract_all_text(data: Any) -> str:
    """Flattens all strings from nested resume dictionaries/lists into a single text block."""
    parts: List[str] = []

    def _walk(obj: Any) -> None:
        if isinstance(obj, str):
            parts.append(obj)
        elif hasattr(obj, "model_dump"):
            _walk(obj.model_dump())
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)

    _walk(data)
    return " ".join(parts)


def _title_tokens(text: str) -> set[str]:
    """Extracts lowercased title tokens, ignoring stopwords."""
    return {
        token
        for token in re.findall(r"[^\W_]+", text.lower())
        if token not in _TITLE_STOPWORDS
    }


def compute_title_match(
    resume: Union[Dict[str, Any], ResumeSchema],
    jd: Union[Dict[str, Any], JDSchema],
) -> Optional[float]:
    """
    Scores how literally the JD's role title appears in the resume:
    - 100: Exact title in headline
    - 75: Exact title in summary
    - Up to 50: Partial word overlap with headline
    """
    try:
        resume_dict = _normalize_to_dict(resume)
        jd_dict = _normalize_to_dict(jd)

        role = jd_dict.get("role")
        if not isinstance(role, str) or not role.strip():
            return None

        personal_info = resume_dict.get("personalInfo") or {}
        headline = str(personal_info.get("title") or "")
        summary = str(resume_dict.get("summary") or "")

        if headline and keyword_in_text(role, headline):
            return _TITLE_IN_HEADLINE
        if summary and keyword_in_text(role, summary):
            return _TITLE_IN_SUMMARY

        role_tokens = _title_tokens(role)
        if not role_tokens or not headline:
            return 0.0

        overlap = len(role_tokens & _title_tokens(headline)) / len(role_tokens)
        return round(overlap * _TITLE_OVERLAP_MAX, 1)
    except Exception as e:
        raise CustomException(e, sys)


def compute_skills_coverage(
    resume: Union[Dict[str, Any], ResumeSchema],
    jd: Union[Dict[str, Any], JDSchema],
) -> Tuple[float, List[str], List[str]]:
    """
    Checks overlap between required/preferred JD skills and the resume.
    Returns (score, matched_skills, missing_skills).
    """
    try:
        resume_dict = _normalize_to_dict(resume)
        jd_dict = _normalize_to_dict(jd)

        target_skills: List[str] = []
        target_skills.extend(jd_dict.get("required_skills") or [])
        target_skills.extend(jd_dict.get("preferred_skills") or [])

        # Remove duplicate skills case-insensitively while preserving order
        seen = set()
        deduped_target: List[str] = []
        for s in target_skills:
            if isinstance(s, str) and s.strip().lower() not in seen:
                seen.add(s.strip().lower())
                deduped_target.append(s.strip())

        if not deduped_target:
            return 100.0, [], []

        # Gather resume skills
        resume_skills_set = {
            s.strip().lower() for s in (resume_dict.get("skills") or []) if isinstance(s, str)
        }

        # Also collect skills mentioned in project technologies
        for proj in resume_dict.get("projects") or []:
            if isinstance(proj, dict):
                for tech in proj.get("project_technologies") or []:
                    if isinstance(tech, str):
                        resume_skills_set.add(tech.strip().lower())

        # Also collect certification names and issuers
        for cert in resume_dict.get("certifications") or []:
            if isinstance(cert, dict):
                c_name = cert.get("certification_name")
                if isinstance(c_name, str) and c_name.strip():
                    resume_skills_set.add(c_name.strip().lower())
                issuer = cert.get("issuer")
                if isinstance(issuer, str) and issuer.strip():
                    resume_skills_set.add(issuer.strip().lower())

        resume_full_text = _extract_all_text(resume_dict)

        matched: List[str] = []
        missing: List[str] = []

        for skill in deduped_target:
            skill_lower = skill.lower()
            if skill_lower in resume_skills_set or keyword_in_text(skill, resume_full_text):
                matched.append(skill)
            else:
                missing.append(skill)

        score = min(100.0, round((len(matched) / len(deduped_target)) * 100, 1))
        return score, matched, missing
    except Exception as e:
        raise CustomException(e, sys)


def compute_keyword_match(
    resume: Union[Dict[str, Any], ResumeSchema],
    jd: Union[Dict[str, Any], JDSchema],
) -> Tuple[float, List[str], List[str]]:
    """
    Evaluates general keyword coverage from JD across all resume text.
    Returns (score, matched_keywords, missing_keywords).
    """
    try:
        resume_dict = _normalize_to_dict(resume)
        jd_dict = _normalize_to_dict(jd)

        all_keywords: List[str] = []
        all_keywords.extend(jd_dict.get("required_skills") or [])
        all_keywords.extend(jd_dict.get("preferred_skills") or [])
        all_keywords.extend(jd_dict.get("keywords") or [])

        seen = set()
        deduped_keywords: List[str] = []
        for kw in all_keywords:
            if isinstance(kw, str) and kw.strip().lower() not in seen:
                seen.add(kw.strip().lower())
                deduped_keywords.append(kw.strip())

        if not deduped_keywords:
            return 100.0, [], []

        resume_text = _extract_all_text(resume_dict)
        matched: List[str] = []
        missing: List[str] = []

        for kw in deduped_keywords:
            if keyword_in_text(kw, resume_text):
                matched.append(kw)
            else:
                missing.append(kw)

        score = min(100.0, round((len(matched) / len(deduped_keywords)) * 100, 1))
        return score, matched, missing
    except Exception as e:
        raise CustomException(e, sys)


def compute_section_completeness(resume: Union[Dict[str, Any], ResumeSchema]) -> float:
    """
    Scores (0-100) whether contact info (email/phone) and essential sections exist:
    - Summary
    - Work Experience, Projects, or Academic Positions
    - Education
    - Skills
    """
    try:
        resume_dict = _normalize_to_dict(resume)
        personal_info = resume_dict.get("personalInfo") or {}
        has_contact = bool(personal_info.get("email") or personal_info.get("phone"))

        # Practical experience can come from employment, projects, or academic positions
        has_experience = bool(
            resume_dict.get("workExperience")
            or resume_dict.get("projects")
            or resume_dict.get("academicPositions")
        )

        sections = [
            bool(resume_dict.get("summary")),
            has_experience,
            bool(resume_dict.get("education")),
            bool(resume_dict.get("skills")),
        ]

        # Total 5 criteria: 4 sections + contact info
        score = (sum(sections) + int(has_contact)) / 5.0 * 100.0
        return round(score, 1)
    except Exception as e:
        raise CustomException(e, sys)


def _collect_date_strings(resume: Dict[str, Any]) -> List[str]:
    """Collects start and end date strings from experience, education, and academic positions."""
    dates: List[str] = []
    for exp in resume.get("workExperience") or []:
        if isinstance(exp, dict):
            if exp.get("start_date"):
                dates.append(str(exp["start_date"]))
            if exp.get("end_date"):
                dates.append(str(exp["end_date"]))

    for edu in resume.get("education") or []:
        if isinstance(edu, dict):
            if edu.get("start_date"):
                dates.append(str(edu["start_date"]))
            if edu.get("end_date"):
                dates.append(str(edu["end_date"]))

    for pos in resume.get("academicPositions") or []:
        if isinstance(pos, dict):
            if pos.get("start_date"):
                dates.append(str(pos["start_date"]))
            if pos.get("end_date"):
                dates.append(str(pos["end_date"]))

    return dates


def compute_date_consistency(resume: Union[Dict[str, Any], ResumeSchema]) -> Optional[float]:
    """
    Calculates the share of dates written in the dominant format (0-100).
    Returns None if fewer than 2 dates are present.
    """
    try:
        resume_dict = _normalize_to_dict(resume)
        date_values = _collect_date_strings(resume_dict)
        style_counts: Dict[str, int] = {}

        for value in date_values:
            for match in _DATE_PATTERN.finditer(value):
                style = match.lastgroup
                if style:
                    style_counts[style] = style_counts.get(style, 0) + 1

        total = sum(style_counts.values())
        if total < _MIN_DATES_FOR_CONSISTENCY:
            return None

        dominant = max(style_counts.values())
        return round((dominant / total) * 100.0, 1)
    except Exception as e:
        raise CustomException(e, sys)

def _generate_recommendations(
    sub_scores: Dict[str, Optional[float]],
    role: str,
    missing_skills: List[str],
    missing_keywords: List[str],
) -> List[str]:
    """Generates tailored, actionable recommendations for candidate improvement."""
    tips: List[str] = []
    keyword_score = sub_scores.get("keyword_match") or 0.0
    skills_score = sub_scores.get("skills_coverage") or 0.0
    section_score = sub_scores.get("section_completeness") or 0.0
    title_score = sub_scores.get("title_match")
    date_score = sub_scores.get("date_consistency")

    if title_score is not None and title_score < _TITLE_IN_HEADLINE and role:
        tips.append(
            f'Include the exact job title "{role}" in your resume headline. '
            "Recruiters filter titles literally, so synonyms or missing headlines are easily overlooked."
        )

    if skills_score < 70 and missing_skills:
        top_skills = ", ".join(missing_skills[:5])
        tips.append(f"Add these critical missing skills required by the JD: {top_skills}.")

    if keyword_score < 60 and missing_keywords:
        top_kw = ", ".join(missing_keywords[:5])
        tips.append(f"Incorporate these high-priority keywords into your bullet points: {top_kw}.")

    if section_score < 100:
        tips.append(
            "Ensure all standard resume sections are present: Contact Info, Professional Summary, "
            "Experience (Work Experience, Projects, or Academic Positions), Education, and Technical Skills."
        )

    if date_score is not None and date_score < 100:
        tips.append(
            'Format all dates consistently (e.g. use "Jan 2022 - Mar 2024" everywhere). '
            "Mixing numeric and text date formats confuses ATS parsers."
        )

    if keyword_score >= 80 and skills_score >= 80:
        tips.append(
            "Strong keyword and skills alignment! Consider adding quantified metrics and business impact to your achievements."
        )

    if not tips:
        tips.append("Your resume is exceptionally well-aligned with the job description.")

    return tips


def compute_ats_score(
    resume: Union[Dict[str, Any], ResumeSchema],
    jd: Union[Dict[str, Any], JDSchema],
) -> Dict[str, Any]:
    """
    Computes the complete ATS score breakdown for a resume against a job description.

    Args:
        resume: Either a ResumeSchema Pydantic object or a normalized dict.
        jd: Either a JDSchema Pydantic object or a dictionary with role, required_skills, etc.

    Returns:
        Dict containing overall_score, sub_scores, key_skills, missing_skills, recommendations.
    """
    try:
        # Convert Pydantic objects or mixed structures to dicts recursively
        resume_dict = _normalize_to_dict(resume)
        jd_dict = _normalize_to_dict(jd)

        # 1. Compute sub-scores
        title_score = compute_title_match(resume_dict, jd_dict)
        skills_score, matched_skills, missing_skills = compute_skills_coverage(resume_dict, jd_dict)
        keyword_score, matched_keywords, missing_keywords = compute_keyword_match(resume_dict, jd_dict)
        section_score = compute_section_completeness(resume_dict)
        date_score = compute_date_consistency(resume_dict)

        sub_scores: Dict[str, Optional[float]] = {
            "keyword_match": keyword_score,
            "skills_coverage": skills_score,
            "title_match": title_score,
            "section_completeness": section_score,
            "date_consistency": date_score,
        }

        # 2. Dynamic weight redistribution for scorable components
        scored = {k: v for k, v in sub_scores.items() if v is not None}
        total_weight = sum(WEIGHTS[k] for k in scored)
        overall = (
            sum(v * WEIGHTS[k] for k, v in scored.items()) / total_weight
            if total_weight > 0
            else 0.0
        )

        role = str(jd_dict.get("role") or "").strip()
        recommendations = _generate_recommendations(
            sub_scores=sub_scores,
            role=role,
            missing_skills=missing_skills,
            missing_keywords=missing_keywords,
        )

        return {
            "overall_score": round(overall, 1),
            "sub_scores": {
                k: (round(v, 1) if v is not None else None)
                for k, v in sub_scores.items()
            },
            "key_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommendations": recommendations,
        }

    except Exception as e:
        raise CustomException(e, sys)


def evaluate_and_save_ats_analysis(
    resume_id: str,
    resume: Union[Dict[str, Any], ResumeSchema],
    jd: Union[Dict[str, Any], JDSchema],
    raw_jd_text: str = "",
) -> ResumeAnalysis:
    """
    Computes the ATS score and commits a ResumeAnalysis record into PostgreSQL.
    """
    try:
        score_data = compute_ats_score(resume=resume, jd=jd)
        jd_dict = _normalize_to_dict(jd)

        # Format ATS issues dictionary for structured DB storage
        ats_issues_payload = [
            {"type": "recommendation", "issue": tip}
            for tip in score_data["recommendations"]
        ]

        with Session(engine) as session:
            analysis = ResumeAnalysis(
                resume_id=resume_id,
                jd=raw_jd_text or jd_dict.get("job_description") or jd_dict.get("role") or "",
                match_score=score_data["overall_score"],
                key_skills=score_data["key_skills"],
                missing_skills=score_data["missing_skills"],
                ats_issues=ats_issues_payload,
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis

    except Exception as e:
        raise CustomException(e, sys)