import asyncio
import io
import sys
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlmodel import Session, select

from src.exception import CustomException
from backend.models.database import engine
from backend.models.schemas import Users, Resumes, TailoredResume, ResumeAnalysis
from backend.services.upload_file_service import sync_file_upload
from backend.services.data_extract_service import extract_markdown_from_bytes
from backend.services.llm_services import parse_resume_json
from backend.services.improver import extract_job_keywords
from backend.services.ats_service import evaluate_and_save_ats_analysis, compute_ats_score


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
    1. Uploads PDF to Backblaze B2.
    2. Extracts Markdown text via Docling.
    3. Normalizes into ResumeSchema via LLM.
    4. Persists the uploaded resume and master resume payload.
    """
    try:
        if not user_id:
            user_id = get_or_create_default_user()

        file_name = file.filename or "resume.pdf"
        file_bytes = await file.read()

        # 1. Upload the PDF to Backblaze B2; continue with in-memory processing
        # if the storage service is unavailable.
        b2_file_url = (
            f"https://s3.us-west-002.backblazeb2.com/"
            f"AI-Resume-Analyser/{file_name}"
        )
        try:
            file_obj = io.BytesIO(file_bytes)
            uploaded_url = sync_file_upload(file_obj=file_obj, file_name=file_name)
            if uploaded_url:
                b2_file_url = uploaded_url
        except Exception as b2_err:
            print(
                "[Warning] B2 upload encountered an issue, "
                f"proceeding with in-memory pipeline: {b2_err}"
            )

        # 2. Extract directly from the bytes received by the API, avoiding a
        # second network request to download the uploaded object.
        try:
            markdown_text = await asyncio.to_thread(
                extract_markdown_from_bytes,
                file_bytes,
                file_name,
            )
        except Exception as doc_err:
            print(f"[Warning] Docling extraction fallback: {doc_err}")
            markdown_text = file_bytes.decode("utf-8", errors="ignore")

        # 3. Normalize into structured ResumeSchema via OpenRouter LLM
        normalized_resume = await parse_resume_json(markdown_text)

        # 4. Save the master resume after parsing.
        with Session(engine) as session:
            resume_record = Resumes(
                user_id=user_id,
                resume_url=b2_file_url,
                master_resume_payload=normalized_resume,
            )
            session.add(resume_record)
            session.commit()
            session.refresh(resume_record)

            return {
                "resume_id": resume_record.resume_id,
                "resume_url": b2_file_url,
                "file_name": file_name,
                "master_resume_payload": normalized_resume,
            }

    except Exception as e:
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
