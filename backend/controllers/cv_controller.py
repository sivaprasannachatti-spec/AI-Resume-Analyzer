import asyncio
import sys
import io
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlmodel import Session, select

from src.exception import CustomException
from backend.models.database import engine
from backend.models.schemas import TailoredResume
from backend.services.resume_generator_service import (
    confirm_tailored_resume,
    generate_tailored_resume,
    update_tailored_resume,
    save_cv,
)
from backend.services.upload_file_service import sync_file_upload
from backend.services.improver import extract_job_keywords
from backend.services.outreach_message_service import (
    generate_and_save_outreach_message,
    get_outreach_message_history,
    update_outreach_message,
)


async def handle_tailor_cv(resume_id: str, raw_jd: str = "") -> Dict[str, Any]:
    """Tailors candidate's CV payload specifically for the target JD."""
    try:
        tailored_cv = await generate_tailored_resume(
            resume_id=resume_id,
            raw_jd=raw_jd,
        )
        return {
            "status": "success",
            "message": "Resume tailored successfully",
            **tailored_cv,
        }
    except Exception as e:
        raise CustomException(e, sys)


async def handle_confirm_tailored_resume(
    resume_id: str,
    tailored_resume_payload: Dict[str, Any],
    raw_jd: str = "",
    template_settings: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    try:
        job_keywords = await extract_job_keywords(raw_jd) if raw_jd.strip() else None
        return {
            "status": "success",
            "message": "Tailored resume applied successfully",
            **confirm_tailored_resume(
                resume_id=resume_id,
                tailored_resume_payload=tailored_resume_payload,
                raw_jd=raw_jd,
                template_settings=template_settings,
                job_keywords=job_keywords,
            ),
        }
    except Exception as e:
        raise CustomException(e, sys)


async def handle_update_tailored_resume(
    resume_id: str,
    tailored_resume_payload: Dict[str, Any],
    template_settings: Dict[str, Any] | None = None,
    raw_jd: str = "",
) -> Dict[str, Any]:
    """Persists manual edits to the tailored resume payload."""
    try:
        if not raw_jd.strip():
            raise ValueError("The job description is required to refresh the ATS score")
        job_keywords = await extract_job_keywords(raw_jd)
        updated_resume = update_tailored_resume(
            resume_id=resume_id,
            tailored_resume_payload=tailored_resume_payload,
            template_settings=template_settings,
            raw_jd=raw_jd,
            job_keywords=job_keywords,
        )
        return {
            "status": "success",
            "message": "Tailored resume updated successfully",
            **updated_resume,
        }
    except Exception as e:
        raise CustomException(e, sys)


async def handle_generate_outreach_message(
    tailored_resume_id: str,
    job_description: str,
    language: str = "en",
) -> Dict[str, Any]:
    try:
        message = await generate_and_save_outreach_message(
            tailored_resume_id=tailored_resume_id,
            job_description=job_description,
            language=language,
        )
        return {
            "status": "success",
            "message": "Outreach message generated and saved",
            **message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys)


def handle_update_outreach_message(
    outreach_id: str,
    message: str,
) -> Dict[str, Any]:
    try:
        updated_message = update_outreach_message(
            outreach_id=outreach_id,
            message=message,
        )
        return {
            "status": "success",
            "message": "Outreach message updated",
            **updated_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys)


def handle_get_outreach_message_history(user_id: str | None = None) -> Dict[str, Any]:
    try:
        return get_outreach_message_history(user_id=user_id)
    except Exception as e:
        raise CustomException(e, sys)


async def handle_save_cv_pdf(resume_id: str, file: UploadFile) -> Dict[str, Any]:
    """Uploads the finalized PDF and updates downloaded file metadata."""
    try:
        file_name = file.filename or f"tailored_cv_{resume_id}.pdf"
        file_bytes = await file.read()

        # 1. Upload PDF bytes to Backblaze B2 with fallback
        file_url = f"https://s3.us-west-002.backblazeb2.com/AI-Resume-Analyser/{file_name}"
        try:
            file_obj = io.BytesIO(file_bytes)
            uploaded = await asyncio.to_thread(
                sync_file_upload,
                file_obj=file_obj,
                file_name=file_name,
            )
            if uploaded:
                file_url = uploaded
        except Exception as b2_err:
            print(f"[Warning] Cloud sync issue: {b2_err}")

        # 2. Save metadata in DB
        tailored_resume_id = save_cv(
            resume_id=resume_id, file_name=file_name, file_url=file_url
        )

        return {
            "status": "success",
            "tailored_resume_id": tailored_resume_id,
            "file_name": file_name,
            "file_url": file_url
        }
    except Exception as e:
        raise CustomException(e, sys)


def get_current_cv(resume_id: str) -> Dict[str, Any]:
    """Fetches the latest tailored resume payload for the given resume_id."""
    try:
        with Session(engine) as session:
            tailored_resume = session.exec(
                select(TailoredResume).where(TailoredResume.resume_id == resume_id)
            ).first()
            if not tailored_resume:
                raise HTTPException(
                    status_code=404,
                    detail="Tailored resume not found for this resume",
                )
            return {
                "tailored_resume_id": tailored_resume.tailored_resume_id,
                "resume_id": tailored_resume.resume_id,
                "file_name": tailored_resume.file_name,
                "file_url": tailored_resume.file_url,
                "tailored_resume_payload": tailored_resume.tailored_resume_payload,
                "template_settings": tailored_resume.template_settings,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys)
