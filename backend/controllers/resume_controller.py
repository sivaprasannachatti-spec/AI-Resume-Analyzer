import logging
import sys
import time
import asyncio
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlmodel import Session, select

from src.exception import CustomException
from backend.models.database import engine
from backend.models.schemas import Users, Resumes, TailoredResume, ResumeAnalysis
from backend.services.data_extract_service import extract_markdown_from_bytes
from backend.services.llm_services import parse_resume_json
from backend.services.improver import extract_job_keywords
from backend.services.ats_service import evaluate_and_save_ats_analysis, compute_ats_score

logger = logging.getLogger(__name__)


def get_or_create_default_user() -> str:
    """Ensures a default user exists for the demo session and returns their user_id."""
    try:
        with Session(engine) as session:
            user = session.exec(select(Users).where(Users.email == "demo@resumeanalyser.ai")).first()
            if not user:
                user = Users(
                    name="Demo Candidate",
                    email="demo@resumeanalyser.ai",
                    password="demo_password_hash"
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            return user.user_id
    except Exception as e:
        raise CustomException(e, sys)


async def process_resume_upload(
    file: UploadFile, user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handles resume upload:
    1. Extracts Markdown directly from uploaded PDF bytes via Docling.
    2. Normalizes into ResumeSchema via LLM.
    3. Persists the parsed resume payload.
    """
    upload_started_at = time.perf_counter()
    try:
        if not user_id:
            user_id = get_or_create_default_user()

        file_name = file.filename or "resume.pdf"
        file_bytes = await file.read()
        logger.info(
            "Resume upload request received (user_id=%s, file_name=%s, file_size_bytes=%d)",
            user_id,
            file_name,
            len(file_bytes),
        )

        # Extract directly from the received bytes without uploading the PDF.
        logger.info(
            "Skipping object storage upload; extracting %s directly from memory",
            file_name,
        )
        extraction_started_at = time.perf_counter()
        try:
            markdown_text = await extract_markdown_from_bytes(file_bytes, filename=file_name)
            logger.info(
                "Docling extraction completed for %s in %.2f seconds",
                file_name,
                time.perf_counter() - extraction_started_at,
            )
        except Exception as doc_err:
            logger.warning(
                "Docling extraction failed for %s; using raw bytes fallback. Error=%s",
                file_name,
                doc_err,
                exc_info=True,
            )
            markdown_text = file_bytes.decode("utf-8", errors="ignore")

        # Normalize into structured ResumeSchema via OpenRouter LLM
        llm_started_at = time.perf_counter()
        normalized_resume = await parse_resume_json(markdown_text)
        logger.info(
            "Resume parsing completed for %s in %.2f seconds",
            file_name,
            time.perf_counter() - llm_started_at,
        )

        # Save the parsed resume payload. No source PDF URL is available because
        # source files are not uploaded to object storage.
        with Session(engine) as session:
            resume_record = Resumes(
                user_id=user_id,
                resume_url="",
                master_resume_payload=normalized_resume,
            )
            session.add(resume_record)
            session.commit()
            session.refresh(resume_record)

        logger.info(
            "Resume upload pipeline completed for %s (user_id=%s, total_duration=%.2f seconds)",
            file_name,
            user_id,
            time.perf_counter() - upload_started_at,
        )

        return {
            "resume_id": resume_record.resume_id,
            "resume_url": resume_record.resume_url,
            "file_name": file_name,
            "master_resume_payload": normalized_resume,
        }

    except Exception as e:
        logger.exception(
            "Resume upload pipeline failed for user_id=%s, file_name=%s",
            user_id,
            file.filename or "resume.pdf",
        )
        raise CustomException(e, sys)


async def analyze_resume_against_jd(
    resume_id: str, jd_text: str
) -> Dict[str, Any]:
    """
    Parses the target JD, evaluates ATS score against candidate's CV payload,
    and commits ResumeAnalysis record.
    """
    try:
        # 1. Fetch the confirmed tailored payload when available; otherwise
        # evaluate the uploaded master resume.
        with Session(engine) as session:
            resume = session.exec(
                select(Resumes).where(Resumes.resume_id == resume_id)
            ).first()
            tailored_resume = session.exec(
                select(TailoredResume).where(TailoredResume.resume_id == resume_id)
            ).first()
            if not resume:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resume not found for id: {resume_id}",
                )
            cv_payload = (
                tailored_resume.tailored_resume_payload
                if tailored_resume and tailored_resume.tailored_resume_payload
                else resume.master_resume_payload
            )
            original_payload = resume.master_resume_payload
            if not cv_payload:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resume payload not found for id: {resume_id}",
                )

        # 2. Extract structured JD content
        jd_dict = await extract_job_keywords(jd_text)

        # 3. Compute deterministic ATS score & save to database
        analysis_record = evaluate_and_save_ats_analysis(
            resume_id=resume_id,
            resume=cv_payload,
            jd=jd_dict,
            raw_jd_text=jd_text,
            original_resume=original_payload,
        )

        # 4. Return both scores against the same job description.
        original_score = compute_ats_score(resume=original_payload, jd=jd_dict)
        tailored_score = compute_ats_score(resume=cv_payload, jd=jd_dict)

        return {
            "analysis_id": analysis_record.analysis_id,
            "overall_score": tailored_score["overall_score"],
            "original_score": original_score,
            "tailored_score": tailored_score,
            "sub_scores": tailored_score["sub_scores"],
            "key_skills": tailored_score["key_skills"],
            "missing_skills": tailored_score["missing_skills"],
            "recommendations": tailored_score["recommendations"],
            "jd_parsed": jd_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys)


def get_resume_details(resume_id: str) -> Dict[str, Any]:
    """Retrieves resume, latest analysis, and CV payload."""
    try:
        with Session(engine) as session:
            resume = session.exec(select(Resumes).where(Resumes.resume_id == resume_id)).first()
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")

            tailored_resume = session.exec(
                select(TailoredResume).where(TailoredResume.resume_id == resume_id)
            ).first()
            analysis = session.exec(
                select(ResumeAnalysis)
                .where(ResumeAnalysis.resume_id == resume_id)
                .order_by(ResumeAnalysis.analysis_id.desc())
            ).first()

            return {
                "resume_id": resume.resume_id,
                "resume_url": resume.resume_url,
                "tailored_resume_payload": (
                    tailored_resume.tailored_resume_payload
                    if tailored_resume
                    else {}
                ),
                "analysis": {
                    "match_score": analysis.match_score,
                    "tailored_match_score": analysis.tailored_match_score,
                    "key_skills": analysis.key_skills,
                    "missing_skills": analysis.missing_skills,
                    "ats_issues": analysis.ats_issues,
                    "jd": analysis.jd
                } if analysis else None
            }

    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys)


def get_resume_history(user_id: Optional[str] = None) -> Dict[str, Any]:
    """List a user's uploaded resumes and their saved tailored-resume records."""
    try:
        if not user_id:
            user_id = get_or_create_default_user()

        with Session(engine) as session:
            resumes = session.exec(
                select(Resumes)
                .where(Resumes.user_id == user_id)
                .order_by(Resumes.uploaded_at.desc())
            ).all()
            if not resumes:
                return {"resumes": []}

            resume_ids = [resume.resume_id for resume in resumes]
            tailored_resumes = session.exec(
                select(TailoredResume).where(
                    TailoredResume.resume_id.in_(resume_ids)
                )
            ).all()
            tailored_by_resume_id = {
                tailored.resume_id: tailored for tailored in tailored_resumes
            }

            history = []
            for resume in resumes:
                tailored = tailored_by_resume_id.get(resume.resume_id)
                personal_info = (resume.master_resume_payload or {}).get(
                    "personalInfo", {}
                )
                history.append({
                    "resume_id": resume.resume_id,
                    "candidate_name": personal_info.get("name", "Resume"),
                    "resume_url": resume.resume_url,
                    "uploaded_at": resume.uploaded_at,
                    "tailored_resume_id": (
                        tailored.tailored_resume_id if tailored else None
                    ),
                    "tailored_updated_at": (
                        tailored.updated_at if tailored else None
                    ),
                    "tailored_file_url": tailored.file_url if tailored else None,
                })

            return {"resumes": history}
    except Exception as e:
        raise CustomException(e, sys)
