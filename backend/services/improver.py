import sys
import re
import json
import copy
import logging

from typing import Any

from src.exception import CustomException
from backend.prompts import (
    DEFAULT_IMPROVE_PROMPT_ID,
    DIFF_FIXED_ROWS_INSTRUCTION,
    DIFF_IMPROVE_PROMPT,
    DIFF_STRATEGY_INSTRUCTIONS,
    EXTRACT_KEYWORDS_PROMPT,
    SKILL_TARGET_PLAN_PROMPT,
    get_language_name,
)
from backend.output_parsers import ImproveDiffResult, ResumeSchema
from backend.services.llm_services import complete_json
from backend.services.text_match import keyword_in_text, normalize_skill_key

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+i`nstructions",
    r"disregard\s+(all\s+)?above",
    r"forget\s+(everything|all)",
    r"new\s+instructions?:",
    r"system\s*:",
    r"<\s*/?\s*system\s*>",
    r"\[\s*INST\s*\]",
    r"\[\s*/\s*INST\s*\]",
]

_PATH_SEGMENT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?$")
_ALLOWED_PATH_RE = re.compile(
    r"^(?:summary|workExperience\[\d+\]\.responsibilities(?:\[\d+\])?"
    r"|projects\[\d+\]\.project_description(?:\[\d+\])?"
    r"|education\[\d+\]\.description"
    r"|additional\.(?:technicalSkills|languages|certificationsTraining|awards)"
    r"|additional\[\d+\]\.(?:technicalSkills|languages|certificationsTraining|awards))$"
)
_BLOCKED_FIELDS = {
    "id",
    "name",
    "email",
    "phone",
    "title",
    "company",
    "location",
    "years",
    "institution",
    "degree",
    "project_name",
    "project_years",
    "project_url",
    "project_github_url",
}
_METRIC_RE = re.compile(r"(?<!\d)\d+[%x]|\$\d+")

AI_PHRASE_REPLACEMENTS = {
    "spearheaded": "led",
    "orchestrated": "coordinated",
    "championed": "advocated for",
    "leveraged": "used",
    "utilized": "used",
    "facilitated": "helped",
    "in order to": "to",
    "moving forward": "",
    "going forward": "",
    "on a daily basis": "daily",
    "at the end of the day": "",
    "due to the fact that": "because",
    "—": ", ",
    "---": ", ",
    "--": ", ",
}
AI_PHRASE_BLACKLIST = set(AI_PHRASE_REPLACEMENTS) | {
    "synergy",
    "paradigm",
    "best-in-class",
    "world-class",
    "cutting-edge",
    "game-changing",
    "disruptive",
    "holistic",
    "robust",
    "scalable",
    "actionable",
    "impactful",
    "proactive",
    "stakeholder",
    "deliverables",
    "bandwidth",
    "circle back",
    "deep dive",
}


def _validate_resume_payload(result: dict[str, Any]) -> dict[str, Any]:
    try:
        if not isinstance(result, dict):
            raise ValueError("Resume result must be an object")
        return ResumeSchema.model_validate(result).model_dump()
    except Exception as e:
        raise CustomException(e, sys)

def _skill_present_in_resume_text(skill: str, resume_data: dict[str, Any]) -> bool:
    """Return True when a skill phrase already appears in the resume text."""
    text = json.dumps(resume_data, ensure_ascii=False)
    return keyword_in_text(skill, text)


def _sanitize_user_input(text: str) -> str:
    """LLM-011: Sanitize user input to prevent prompt injection.

    Removes or redacts common injection patterns that could manipulate LLM behavior.
    """
    sanitized = text
    for pattern in _INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized

def _validate_string_list_field(
    result: dict[str, Any],
    field: str,
) -> list[str]:
    """Return a normalized required list of non-empty strings."""
    value = result.get(field)
    if not isinstance(value, list):
        raise ValueError(f"LLM response requires a '{field}' list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"LLM response field '{field}' must contain text")
    return [item.strip() for item in value]


def _validate_requirement_list_field(
    result: dict[str, Any],
    field: str,
) -> list[str]:
    """Normalize an absent numeric requirement while preserving text requirements."""
    try:
        value = result.get(field)
        if value == [0]:
            return []
        if not isinstance(value, list):
            raise ValueError(f"LLM response requires a '{field}' list")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError(f"LLM response field '{field}' must contain text")
        return [item.strip() for item in value]
    except Exception as e:
        raise CustomException(e, sys)


def _validate_keyword_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate keyword fields consumed by tailoring while allowing sparse output."""
    validated = dict(result)
    for field in ("required_skills", "preferred_skills", "keywords"):
        validated[field] = _validate_string_list_field(result, field)
    for field in (
        "experience_requirements",
        "education_requirements",
        "key_responsibilities",
    ):
        if field in result:
            validated[field] = _validate_requirement_list_field(result, field)
    return validated


async def extract_job_keywords(job_description: str) -> dict[str, Any]:
    try:
        """Extract keywords and requirements from job description.
        
        Args:
            job_description: Raw job description text
    
        Returns:
            Structured keywords and requirements
        """
        # LLM-011: Sanitize job description before using in prompt
        sanitized_jd = _sanitize_user_input(job_description)
        prompt = EXTRACT_KEYWORDS_PROMPT.format(job_description=sanitized_jd)
    
        result = await complete_json(
            prompt=prompt,
            system_prompt="You are an expert job description analyzer.",
            schema_type="keywords",
            response_validator=_validate_keyword_result,
        )
        return _validate_keyword_result(result)
    except Exception as e:
        raise CustomException(e, sys)

def _validate_diff_result(result: dict[str, Any]) -> dict[str, Any]:
    try:
        """Validate an explicit diff result, including a legitimate empty list."""
        if "changes" not in result:
            raise ValueError("LLM diff response is missing 'changes'")
        return ImproveDiffResult.model_validate(result).model_dump()
    except Exception as e:
        raise CustomException(e, sys)


def _validate_skill_plan_result(result: dict[str, Any]) -> dict[str, Any]:
    try:
        """Validate an explicit skill-target plan without coercing invalid leaves."""
        raw_targets = result.get("target_skills")
        if not isinstance(raw_targets, list):
            raise ValueError("LLM skill plan requires a 'target_skills' list")

        normalized: list[dict[str, str]] = []
        for target in raw_targets:
            if isinstance(target, str):
                skill = target.strip()
                reason = ""
            elif isinstance(target, dict):
                raw_skill = target.get("skill")
                raw_reason = target.get("reason", "")
                if not isinstance(raw_skill, str) or not isinstance(raw_reason, str):
                    raise ValueError("Skill targets require text skill and reason fields")
                skill = raw_skill.strip()
                reason = raw_reason.strip()
            else:
                raise ValueError("Skill targets must be strings or objects")
            if not skill:
                raise ValueError("Skill targets cannot be blank")
            normalized.append({"skill": skill, "reason": reason})

        raw_notes = result.get("strategy_notes", "")
        if not isinstance(raw_notes, str):
            raise ValueError("Skill plan strategy_notes must be text")

        return {
            **result,
            "target_skills": normalized,
            "strategy_notes": raw_notes.strip(),
        }
    except Exception as e:
        raise CustomException(e, sys)

def _prepare_keywords_for_prompt(job_keywords: dict[str, Any]) -> str:
    """Format job keywords as a focused, readable list for the LLM prompt.

    Extracts only actionable fields (skills and keywords) and drops
    informational fields that add noise without helping the LLM tailor.
    """
    sections: list[str] = []

    required = job_keywords.get("required_skills", [])
    if required:
        sections.append(
            "Required skills to emphasize:\n- " + "\n- ".join(str(s) for s in required)
        )

    preferred = job_keywords.get("preferred_skills", [])
    if preferred:
        sections.append(
            "Preferred skills (include only if resume supports them):\n- "
            + "\n- ".join(str(s) for s in preferred)
        )

    keywords = job_keywords.get("keywords", [])
    if keywords:
        sections.append(
            "Additional keywords to weave in naturally:\n- "
            + "\n- ".join(str(k) for k in keywords)
        )

    return "\n\n".join(sections) if sections else "No specific keywords extracted."

def _prepare_skill_targets_for_prompt(
    skill_targets: list[dict[str, Any]] | None,
) -> str:
    """Format verified skill targets for the diff prompt."""
    if not skill_targets:
        return "No verified skill targets."
    lines: list[str] = []
    for target in skill_targets:
        skill = str(target.get("skill", "")).strip()
        if not skill:
            continue
        source = str(target.get("source", "unknown")).strip() or "unknown"
        reason = str(target.get("reason", "")).strip()
        suffix = f": {reason}" if reason else ""
        lines.append(f"- {skill} ({source}){suffix}")
    return "\n".join(lines) if lines else "No verified skill targets."


def _extract_skill_index(items: Any) -> dict[str, str]:
    """Build a normalized skill index from a string list."""
    if not isinstance(items, list):
        return {}
    index: dict[str, str] = {}
    for item in items:
        if not isinstance(item, str):
            continue
        skill = item.strip()
        if skill:
            index.setdefault(normalize_skill_key(skill), skill)
    return index

def _extract_jd_skill_index(
    job_keywords: dict[str, Any],
    job_description: str | None = None,
) -> dict[str, str]:
    """Build a normalized index of explicit JD skills."""
    index: dict[str, str] = {}
    for field in ("required_skills", "preferred_skills"):
        values = job_keywords.get(field, [])
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, str):
                continue
            skill = value.strip()
            if skill and (
                job_description is None or keyword_in_text(skill, job_description)
            ):
                index.setdefault(normalize_skill_key(skill), skill)
    return index


def _extract_resume_skills(resume_data: dict[str, Any]) -> Any:
    """Read technical skills from either supported local resume shape."""
    additional = resume_data.get("additional", [])
    if isinstance(additional, dict):
        return additional.get("technicalSkills", [])
    if isinstance(additional, list):
        skills: list[Any] = []
        for item in additional:
            if isinstance(item, dict):
                skills.extend(item.get("technicalSkills", []))
        return skills
    return []


def _resolve_resume_path(data: dict[str, Any], path: str) -> tuple[Any, bool]:
    """Resolve a local resume dot/bracket path."""
    current: Any = data
    parts = path.split(".")
    for part in parts:
        match = _PATH_SEGMENT_RE.fullmatch(part)
        if not match or not isinstance(current, dict):
            return None, False
        key, index_text = match.groups()
        if key not in current:
            return None, False
        current = current[key]
        if index_text is not None:
            index = int(index_text)
            if not isinstance(current, list) or index >= len(current):
                return None, False
            current = current[index]
    return current, True


def _set_resume_path(data: dict[str, Any], path: str, value: Any) -> bool:
    parts = path.split(".")
    if not parts:
        return False
    current: Any = data
    for part in parts[:-1]:
        match = _PATH_SEGMENT_RE.fullmatch(part)
        if not match or not isinstance(current, dict):
            return False
        key, index_text = match.groups()
        if key not in current:
            return False
        current = current[key]
        if index_text is not None:
            index = int(index_text)
            if not isinstance(current, list) or index >= len(current):
                return False
            current = current[index]

    match = _PATH_SEGMENT_RE.fullmatch(parts[-1])
    if not match or not isinstance(current, dict):
        return False
    key, index_text = match.groups()
    if key not in current:
        return False
    if index_text is None:
        current[key] = value
        return True
    target = current[key]
    index = int(index_text)
    if not isinstance(target, list) or index >= len(target):
        return False
    target[index] = value
    return True


def _allowed_skill_keys(
    targets: list[dict[str, Any] | str] | None,
) -> set[str]:
    keys: set[str] = set()
    for target in targets or []:
        skill = target if isinstance(target, str) else target.get("skill", "")
        if isinstance(skill, str) and skill.strip():
            keys.add(normalize_skill_key(skill))
    return keys


def _matches_original(actual: Any, expected: str | list[str] | None) -> bool:
    if not isinstance(actual, str) or not isinstance(expected, str):
        return False
    return actual.strip().casefold() == expected.strip().casefold()


def _is_blocked_resume_path(path: str) -> bool:
    leaf = path.rsplit(".", 1)[-1]
    leaf = re.sub(r"\[\d+\]$", "", leaf)
    return leaf in _BLOCKED_FIELDS


def _is_fixed_row_append(path: str, fixed_row_sections: tuple[str, ...]) -> bool:
    return (
        path.split("[", 1)[0] in fixed_row_sections
        and path.endswith(("responsibilities", "project_description"))
    )


def _reorder_list(actual: list[Any], proposed: list[Any]) -> list[str] | None:
    if not all(isinstance(item, str) for item in actual + proposed):
        return None
    buckets: dict[str, list[str]] = {}
    for item in actual:
        buckets.setdefault(item.casefold(), []).append(item)
    if sorted(item.casefold() for item in actual) != sorted(
        item.casefold() for item in proposed
    ):
        return None
    result: list[str] = []
    for item in proposed:
        values = buckets.get(item.casefold(), [])
        if not values:
            return None
        result.append(values.pop(0))
    return result


def apply_diffs(
    original: dict[str, Any],
    changes: list[Any],
    allowed_skill_targets: list[dict[str, Any] | str] | None = None,
    *,
    fixed_row_sections: tuple[str, ...] = (),
) -> tuple[dict[str, Any], list[Any], list[Any]]:
    """Apply only safe, schema-valid changes to a copied resume payload."""
    try:
        result = copy.deepcopy(original)
        applied: list[Any] = []
        rejected: list[Any] = []
        allowed_skills = _allowed_skill_keys(allowed_skill_targets)

        for change in changes:
            path = change.path
            value, resolved = _resolve_resume_path(result, path)
            if (
                not _ALLOWED_PATH_RE.fullmatch(path)
                or _is_blocked_resume_path(path)
                or not resolved
            ):
                rejected.append(change)
                continue

            if change.action == "replace":
                if not _matches_original(value, change.original) or not isinstance(
                    change.value, str
                ):
                    rejected.append(change)
                    continue
                _set_resume_path(result, path, change.value)
            elif change.action == "append":
                if (
                    _is_fixed_row_append(path, fixed_row_sections)
                    or not isinstance(value, list)
                    or not isinstance(change.value, str)
                    or not change.value.strip()
                ):
                    rejected.append(change)
                    continue
                value.append(change.value)
            elif change.action == "reorder":
                if not isinstance(value, list) or not isinstance(change.value, list):
                    rejected.append(change)
                    continue
                reordered = _reorder_list(value, change.value)
                if reordered is None:
                    rejected.append(change)
                    continue
                _set_resume_path(result, path, reordered)
            elif change.action == "add_skill":
                if (
                    not path.endswith(".technicalSkills")
                    or not isinstance(value, list)
                    or not isinstance(change.value, str)
                    or not change.value.strip()
                    or normalize_skill_key(change.value) not in allowed_skills
                    or any(
                        isinstance(item, str)
                        and item.casefold() == change.value.strip().casefold()
                        for item in value
                    )
                ):
                    rejected.append(change)
                    continue
                value.append(change.value.strip())
            else:
                rejected.append(change)
                continue
            applied.append(change)
        return result, applied, rejected
    except Exception as e:
        raise CustomException(e, sys)


def verify_diff_result(
    original: dict[str, Any],
    result: dict[str, Any],
    applied_changes: list[Any],
    job_keywords: dict[str, Any] | None = None,
) -> list[str]:
    """Run local writing and factual-preservation checks on tailored data."""
    try:
        warnings: list[str] = []
        if not applied_changes:
            warnings.append("No changes were applied")

        for section in ("workExperience", "education", "projects"):
            if len(original.get(section, [])) != len(result.get(section, [])):
                warnings.append(f"Section count changed: {section}")

        for section, fields in (
            ("workExperience", ("id", "company", "title", "years")),
            ("education", ("id", "institution", "degree", "years")),
            ("projects", ("id", "project_name", "project_years")),
        ):
            for old, new in zip(original.get(section, []), result.get(section, [])):
                if isinstance(old, dict) and isinstance(new, dict):
                    for field in fields:
                        if old.get(field) != new.get(field):
                            warnings.append(f"Identity field changed: {section}.{field}")

        def word_count(data: dict[str, Any]) -> int:
            total = len(str(data.get("summary") or "").split())
            for section, field in (
                ("workExperience", "responsibilities"),
                ("projects", "project_description"),
                ("education", "description"),
            ):
                for entry in data.get(section, []):
                    value = entry.get(field, []) if isinstance(entry, dict) else []
                    values = value if isinstance(value, list) else [value]
                    total += sum(len(str(item).split()) for item in values)
            return total

        old_words = word_count(original)
        new_words = word_count(result)
        if old_words and new_words > old_words * 1.8:
            warnings.append("Tailored resume grew by more than 80 percent")

        for change in applied_changes:
            if change.action in ("replace", "append") and isinstance(change.value, str):
                added = set(_METRIC_RE.findall(change.value))
                existing = set(_METRIC_RE.findall(change.original or ""))
                if added - existing:
                    warnings.append(f"Possible unsupported metric in {change.path}")
        return warnings
    except Exception as e:
        raise CustomException(e, sys)


def _remove_ai_phrases(
    data: dict[str, Any],
    master_resume: dict[str, Any],
    job_description: str,
) -> tuple[dict[str, Any], list[str]]:
    try:
        protected = json.dumps(master_resume, ensure_ascii=False).lower()
        jd_text = job_description.lower()
        removed: set[str] = set()

        def clean(value: Any) -> Any:
            if isinstance(value, str):
                result = value
                for phrase in sorted(AI_PHRASE_BLACKLIST, key=len, reverse=True):
                    if phrase in protected or phrase in jd_text:
                        continue
                    pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.I)
                    if pattern.search(result):
                        removed.add(phrase)
                        replacement = AI_PHRASE_REPLACEMENTS.get(phrase, "")
                        result = pattern.sub(replacement, result)
                result = re.sub(r"[ \t]{2,}", " ", result)
                return result.strip()
            if isinstance(value, list):
                return [clean(item) for item in value]
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            return value

        return clean(copy.deepcopy(data)), sorted(removed)
    except Exception as e:
        raise CustomException(e, sys)


def _restore_master_invariants(
    candidate: dict[str, Any],
    master: dict[str, Any],
) -> dict[str, Any]:
    """Keep identity, chronology, and collection shape owned by the master resume."""
    result = copy.deepcopy(candidate)
    if isinstance(master.get("personalInfo"), dict):
        result["personalInfo"] = copy.deepcopy(master["personalInfo"])
    if "customSections" in master:
        result["customSections"] = copy.deepcopy(master["customSections"])
    else:
        result.pop("customSections", None)

    protected_fields = {
        "workExperience": ("id", "title", "company", "location", "years"),
        "education": ("id", "institution", "degree", "years"),
        "projects": ("id", "project_name", "project_years", "project_url", "project_github_url"),
    }
    for section, fields in protected_fields.items():
        master_items = master.get(section, [])
        candidate_items = result.get(section, [])
        if not isinstance(master_items, list):
            continue
        if not isinstance(candidate_items, list) or len(candidate_items) != len(master_items):
            candidate_items = copy.deepcopy(master_items)
        else:
            for index, master_item in enumerate(master_items):
                if not isinstance(master_item, dict) or not isinstance(candidate_items[index], dict):
                    candidate_items[index] = copy.deepcopy(master_item)
                    continue
                for field in fields:
                    candidate_items[index][field] = copy.deepcopy(master_item.get(field))
        result[section] = candidate_items
    return result


async def improve_resume(
    original_resume: dict[str, Any],
    job_description: str,
    job_keywords: dict[str, Any],
) -> dict[str, Any]:
    """Fallback whole-document improvement for non-structured resume data."""
    try:
        prompt = (
            "Improve this resume for the job description. Preserve all facts and "
            "return only a JSON object. Do not invent skills, metrics, employers, "
            "dates, or achievements.\n\n"
            f"Job description:\n{_sanitize_user_input(job_description)}\n\n"
            f"Keywords:\n{_prepare_keywords_for_prompt(job_keywords)}\n\n"
            f"Resume:\n{json.dumps(original_resume, ensure_ascii=False)}"
        )
        return await complete_json(
            prompt=prompt,
            system_prompt="You are a truthful resume editor. Return only JSON.",
            max_tokens=8192,
            schema_type="resume",
            response_validator=_validate_resume_payload,
        )
    except Exception as e:
        raise CustomException(e, sys)


async def refine_resume(
    initial_tailored: dict[str, Any],
    master_resume: dict[str, Any],
    job_description: str,
    job_keywords: dict[str, Any],
) -> dict[str, Any]:
    """Run deterministic refinement checks after tailoring."""
    try:
        refined, removed = _remove_ai_phrases(
            initial_tailored, master_resume, job_description
        )
        refined = _restore_master_invariants(refined, master_resume)
        checks = [
            warning
            for warning in verify_diff_result(
                master_resume, refined, [], job_keywords
            )
            if warning != "No changes were applied"
        ]
        master_additional = master_resume.get("additional", {})
        refined_additional = refined.get("additional", {})
        master_skill_values = (
            master_additional.get("technicalSkills", [])
            if isinstance(master_additional, dict)
            else _extract_resume_skills(master_resume)
        )
        tailored_skill_values = (
            refined_additional.get("technicalSkills", [])
            if isinstance(refined_additional, dict)
            else _extract_resume_skills(refined)
        )
        master_skills = {
            normalize_skill_key(skill)
            for skill in master_skill_values
            if isinstance(skill, str)
        }
        tailored_skills = {
            skill for skill in tailored_skill_values if isinstance(skill, str)
        }
        invented_skills = sorted(
            skill for skill in tailored_skills
            if normalize_skill_key(skill) not in master_skills
        )
        if invented_skills:
            if isinstance(refined_additional, dict):
                refined_additional["technicalSkills"] = [
                    skill
                    for skill in refined_additional.get("technicalSkills", [])
                    if isinstance(skill, str)
                    and normalize_skill_key(skill) in master_skills
                ]
            checks.append(
                "Possible invented skills: " + ", ".join(invented_skills)
            )
        searchable_text = json.dumps(refined, ensure_ascii=False)
        keywords = [
            keyword
            for field in ("required_skills", "preferred_skills", "keywords")
            for keyword in job_keywords.get(field, [])
            if isinstance(keyword, str)
        ]
        matched = sum(
            1 for keyword in keywords if keyword_in_text(keyword, searchable_text)
        )
        return {
            "refined_data": refined,
            "ai_phrases_removed": removed,
            "writing_checks": checks,
            "final_match_percentage": round((matched / len(keywords)) * 100, 2)
            if keywords
            else 0.0,
            "invented_skills": invented_skills,
        }
    except Exception as e:
        raise CustomException(e, sys)


def apply_resume_diff(
    original_resume_data: dict[str, Any],
    diff_result: ImproveDiffResult,
    allowed_skill_targets: list[dict[str, Any] | str] | None = None,
    *,
    fixed_row_sections: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Create the final in-memory tailoring preview from validated diffs."""
    try:
        tailored, applied, rejected = apply_diffs(
            original_resume_data,
            diff_result.changes,
            allowed_skill_targets,
            fixed_row_sections=fixed_row_sections,
        )
        return {
            "tailored_resume_data": tailored,
            "final_tailored_resume": tailored,
            "applied_changes": applied,
            "rejected_changes": rejected,
            "writing_checks": verify_diff_result(
                original_resume_data, tailored, applied
            ),
            "strategy_notes": diff_result.strategy_notes,
        }
    except Exception as e:
        raise CustomException(e, sys)


def verify_skill_target_plan(
    raw_plan: dict[str, Any],
    original_resume_data: dict[str, Any],
    job_keywords: dict[str, Any],
    job_description: str | None = None,
) -> dict[str, list[dict[str, str]] | str]:
    try:
        """Filter and classify LLM-proposed skill targets before diff generation."""
        original_skills = _extract_skill_index(
            _extract_resume_skills(original_resume_data)
        )
        jd_skills = _extract_jd_skill_index(job_keywords, job_description)
        raw_targets = raw_plan.get("target_skills", [])
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()

        if not isinstance(raw_targets, list):
            raw_targets = []

        for target in raw_targets:
            if isinstance(target, str):
                skill = target.strip()
                reason = ""
            elif isinstance(target, dict):
                skill = str(target.get("skill", "")).strip()
                reason = str(target.get("reason", "")).strip()
            else:
                continue

            skill_key = normalize_skill_key(skill)
            if not skill or skill_key in seen:
                continue
            seen.add(skill_key)

            if skill_key in original_skills:
                accepted.append(
                    {
                        "skill": original_skills[skill_key],
                        "source": "existing",
                        "reason": reason or "Already present in resume skills",
                    }
                )
            elif skill_key in jd_skills:
                accepted.append(
                    {
                        "skill": jd_skills[skill_key],
                        "source": "jd_added",
                        "reason": reason
                        or "Required or preferred by the job description",
                    }
                )
            elif _skill_present_in_resume_text(skill, original_resume_data):
                accepted.append(
                    {
                        "skill": skill,
                        "source": "supported_by_resume",
                        "reason": reason
                        or "Appears in the existing resume content",
                    }
                )
            else:
                rejected.append(
                    {
                        "skill": skill,
                        "source": "unsupported",
                        "reason": reason or "Not found in resume or job keywords",
                    }
                )

        return {
            "accepted": accepted,
            "rejected": rejected,
            "strategy_notes": str(raw_plan.get("strategy_notes", "")),
        }
    except Exception as e:
        raise CustomException(e, sys)


async def generate_skill_target_plan(
    original_resume_data: dict[str, Any],
    job_description: str,
    job_keywords: dict[str, Any],
    language: str = "en",
) -> dict[str, Any]:
    try:
        """Ask the LLM for a compact skill target plan before editing diffs."""
        output_language = get_language_name(language)
        existing_skills = _extract_resume_skills(original_resume_data)
        sanitized_jd = _sanitize_user_input(job_description)
        prompt = SKILL_TARGET_PLAN_PROMPT.format(
            output_language=output_language,
            existing_skills=json.dumps(existing_skills, ensure_ascii=False),
            job_keywords=_prepare_keywords_for_prompt(job_keywords),
            job_description=sanitized_jd,
            original_resume=json.dumps(original_resume_data, ensure_ascii=False),
        )

        result = await complete_json(
            prompt=prompt,
            system_prompt=(
                "You are a resume skill planning agent. Output only valid JSON with "
                "target_skills and strategy_notes."
            ),
            max_tokens=2048,
            schema_type="diff",
            response_validator=_validate_skill_plan_result,
        )
        return _validate_skill_plan_result(result)
    except Exception as e:
        raise CustomException(e, sys)


async def generate_resume_diffs(
    original_resume: str,
    job_description: str,
    job_keywords: dict[str, Any],
    language: str = "en",
    prompt_id: str | None = None,
    original_resume_data: dict[str, Any] | None = None,
    skill_targets: list[dict[str, Any]] | None = None,
    *,
    fixed_row_sections: tuple[str, ...] = (),
) -> ImproveDiffResult:
    """Generate validated, targeted resume changes without applying them."""
    try:
        selected_strategy = prompt_id or DEFAULT_IMPROVE_PROMPT_ID
        strategy_instruction = DIFF_STRATEGY_INSTRUCTIONS.get(
            selected_strategy,
            DIFF_STRATEGY_INSTRUCTIONS[DEFAULT_IMPROVE_PROMPT_ID],
        )
        if fixed_row_sections:
            strategy_instruction += " " + DIFF_FIXED_ROWS_INSTRUCTION.format(
                sections=" and ".join(fixed_row_sections)
            )

        if original_resume_data is not None:
            resume_input = json.dumps(original_resume_data, ensure_ascii=False)
        else:
            resume_input = original_resume

        prompt = DIFF_IMPROVE_PROMPT.format(
            strategy_instruction=strategy_instruction,
            output_language=get_language_name(language),
            job_keywords=_prepare_keywords_for_prompt(job_keywords),
            skill_targets=_prepare_skill_targets_for_prompt(skill_targets),
            job_description=_sanitize_user_input(job_description),
            original_resume=resume_input,
        )

        result = await complete_json(
            prompt=prompt,
            system_prompt=(
                "You are an expert resume editor. Return only valid JSON with "
                "targeted, fact-preserving changes."
            ),
            max_tokens=4096,
            schema_type="diff",
            response_validator=_validate_diff_result,
        )
        return ImproveDiffResult.model_validate(_validate_diff_result(result))
    except Exception as e:
        raise CustomException(e, sys)
