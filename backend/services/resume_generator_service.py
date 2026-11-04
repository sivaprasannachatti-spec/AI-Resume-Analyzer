import sys
import json
from datetime import datetime, timezone
from sqlmodel import Session, select

from src.exception import CustomException
from backend.models.schemas import Resumes, TailoredResume, TemplateSettings
from backend.models.database import engine
from backend.output_parsers import ResumeSchema
from backend.services.ats_service import compute_ats_score, evaluate_and_save_ats_analysis
from backend.services.improver import (
    apply_resume_diff,
    extract_job_keywords,
    improve_resume,
    generate_resume_diffs,
    generate_skill_target_plan,
    refine_resume,
    verify_skill_target_plan,
)
async def generate_tailored_resume(
    resume_id: str,
    raw_jd: str,
    language: str = "en",
    prompt_id: str | None = None,
) -> dict:
    """Generate a tailored preview without persisting it."""
    try:
        if not raw_jd or not raw_jd.strip():
            raise ValueError("A job description is required for tailoring")

        with Session(engine) as session:
            resume_record = session.exec(
                select(Resumes).where(Resumes.resume_id == resume_id)
            ).first()
            if not resume_record or not resume_record.master_resume_payload:
                raise CustomException(
                    f"No master resume found for resume_id: {resume_id}", sys
                )
            original_resume = resume_record.master_resume_payload

        job_keywords = await extract_job_keywords(raw_jd)
        raw_skill_plan = await generate_skill_target_plan(
            original_resume_data=original_resume,
            job_description=raw_jd,
            job_keywords=job_keywords,
            language=language,
        )
        skill_plan = verify_skill_target_plan(
            raw_plan=raw_skill_plan,
            original_resume_data=original_resume,
            job_keywords=job_keywords,
            job_description=raw_jd,
        )
        try:
            ResumeSchema.model_validate(original_resume)
            is_structured = True
        except Exception:
            is_structured = False

        if is_structured:
            diff_result = await generate_resume_diffs(
                original_resume=json.dumps(original_resume, ensure_ascii=False),
                job_description=raw_jd,
                job_keywords=job_keywords,
                language=language,
                prompt_id=prompt_id,
                original_resume_data=original_resume,
                skill_targets=skill_plan["accepted"],
            )
            preview = apply_resume_diff(
                original_resume_data=original_resume,
                diff_result=diff_result,
                allowed_skill_targets=skill_plan["accepted"],
            )
            tailored_payload = preview["final_tailored_resume"]
            diff_data = {
                "strategy_notes": preview["strategy_notes"],
                "applied_changes": preview["applied_changes"],
                "rejected_changes": preview["rejected_changes"],
            }
        else:
            tailored_payload = await improve_resume(
                original_resume, raw_jd, job_keywords
            )
            preview = {"writing_checks": [], "strategy_notes": ""}
            diff_data = {"strategy_notes": "", "applied_changes": [], "rejected_changes": []}

        refined = await refine_resume(
            initial_tailored=tailored_payload,
            master_resume=original_resume,
            job_description=raw_jd,
            job_keywords=job_keywords,
        )
        tailored_payload = ResumeSchema.model_validate(
            refined["refined_data"]
        ).model_dump()
        preview["writing_checks"] = preview["writing_checks"] + [
            warning
            for warning in refined["writing_checks"]
            if warning != "No changes were applied"
        ]
        ats_scores = {
            "original": compute_ats_score(original_resume, job_keywords),
            "tailored": compute_ats_score(tailored_payload, job_keywords),
        }

        return {
            "resume_id": resume_id,
            "original_resume_payload": original_resume,
            "tailored_resume_payload": tailored_payload,
            "raw_jd": raw_jd,
            "ats_scores": ats_scores,
            "job_keywords": job_keywords,
            "skill_targets": skill_plan,
            "diff_result": diff_data,
            "writing_checks": preview["writing_checks"],
            "refinement": refined,
            "requires_confirmation": True,
        }
    except Exception as e:
        raise CustomException(e, sys)


def confirm_tailored_resume(
    resume_id: str,
    tailored_resume_payload: dict,
    raw_jd: str = "",
    template_settings: dict | None = None,
    job_keywords: dict | None = None,
) -> dict:
    """Persist the preview only after the user confirms/applies it."""
    try:
        validated_payload = ResumeSchema.model_validate(
            tailored_resume_payload
        ).model_dump()
        with Session(engine) as session:
            resume_record = session.exec(
                select(Resumes).where(Resumes.resume_id == resume_id)
            ).first()
            if not resume_record:
                raise ValueError(f"Resume not found for id: {resume_id}")
            original_payload = resume_record.master_resume_payload
            validated_settings = TemplateSettings.model_validate(
                template_settings or {}
            ).model_dump()
            tailored_resume = session.exec(
                select(TailoredResume).where(TailoredResume.resume_id == resume_id)
            ).first()
            if not tailored_resume:
                tailored_resume = TailoredResume(
                    resume_id=resume_id,
                    tailored_resume_payload=validated_payload,
                    template_settings=validated_settings,
                )
            else:
                tailored_resume.tailored_resume_payload = validated_payload
                tailored_resume.template_settings = validated_settings
            tailored_resume.updated_at = datetime.now(timezone.utc)
            session.add(tailored_resume)
            session.commit()
            session.refresh(tailored_resume)

        ats_scores = None
        if job_keywords is not None:
            original_score = compute_ats_score(
                original_payload,
                job_keywords,
            )
            tailored_score = compute_ats_score(validated_payload, job_keywords)
            evaluate_and_save_ats_analysis(
                resume_id=resume_id,
                resume=validated_payload,
                original_resume=original_payload,
                jd=job_keywords,
                raw_jd_text=raw_jd,
            )
            ats_scores = {"original": original_score, "tailored": tailored_score}

        return {
            "tailored_resume_id": tailored_resume.tailored_resume_id,
            "resume_id": resume_id,
            "tailored_resume_payload": validated_payload,
            "template_settings": validated_settings,
            "ats_scores": ats_scores,
            "confirmed": True,
        }
    except Exception as e:
        raise CustomException(e, sys)


def update_tailored_resume(
    resume_id: str,
    tailored_resume_payload: dict,
    template_settings: dict | None = None,
    raw_jd: str = "",
    job_keywords: dict | None = None,
) -> dict:
    """
    Persist the manually edited tailored resume payload for an existing resume.
    """
    try:
        if not isinstance(tailored_resume_payload, dict):
            raise ValueError("tailored_resume_payload must be an object")
        validated_payload = ResumeSchema.model_validate(
            tailored_resume_payload
        ).model_dump()
        validated_settings = (
            TemplateSettings.model_validate(template_settings).model_dump()
            if template_settings is not None
            else None
        )

        with Session(engine) as session:
            resume_record = session.exec(
                select(Resumes).where(Resumes.resume_id == resume_id)
            ).first()
            if not resume_record:
                raise ValueError(f"Resume not found for id: {resume_id}")
            original_payload = resume_record.master_resume_payload
            tailored_resume = session.exec(
                select(TailoredResume).where(TailoredResume.resume_id == resume_id)
            ).first()
            if not tailored_resume:
                raise CustomException(
                    f"Failed to fetch tailored resume for resume_id: {resume_id}", sys
                )
            current_settings = tailored_resume.template_settings

        with Session(engine) as session:
            tailored_resume = session.exec(
                select(TailoredResume).where(TailoredResume.resume_id == resume_id)
            ).first()
            if not tailored_resume:
                raise ValueError(f"Tailored resume not found for resume_id: {resume_id}")
            tailored_resume.tailored_resume_payload = validated_payload
            if validated_settings is not None:
                tailored_resume.template_settings = validated_settings
            tailored_resume.updated_at = datetime.now(timezone.utc)
            session.add(tailored_resume)
            session.commit()
            session.refresh(tailored_resume)

        ats_scores = None
        if job_keywords is not None:
            original_score = compute_ats_score(
                original_payload,
                job_keywords,
            )
            tailored_score = compute_ats_score(validated_payload, job_keywords)
            evaluate_and_save_ats_analysis(
                resume_id=resume_id,
                resume=validated_payload,
                original_resume=original_payload,
                jd=job_keywords,
                raw_jd_text=raw_jd,
            )
            ats_scores = {"original": original_score, "tailored": tailored_score}

        return {
            "tailored_resume_payload": validated_payload,
            "template_settings": validated_settings or current_settings,
            "ats_scores": ats_scores,
        }

    except Exception as e:
        raise CustomException(e, sys)


def save_cv(resume_id: str, file_name: str, file_url: str) -> str:
    """
    Saves the downloaded file metadata on the tailored resume record.
    Returns the tailored resume ID.
    """
    try:
        with Session(engine) as session:
            tailored_resume = session.exec(
                select(TailoredResume).where(TailoredResume.resume_id == resume_id)
            ).first()
            if not tailored_resume:
                raise CustomException(
                    f"Failed to fetch tailored resume for resume_id: {resume_id}", sys
                )
            tailored_resume.file_name = file_name
            tailored_resume.file_url = file_url
            tailored_resume.updated_at = datetime.now(timezone.utc)
            session.add(tailored_resume)
            session.commit()
            session.refresh(tailored_resume)
            return tailored_resume.tailored_resume_id

    except Exception as e:
        raise CustomException(e, sys)