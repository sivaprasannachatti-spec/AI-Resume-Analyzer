from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Query
from pydantic import BaseModel

from backend.controllers.resume_controller import (
    process_resume_upload,
    analyze_resume_against_jd,
    get_resume_details,
    get_resume_history,
)

router = APIRouter(prefix="/api/resume", tags=["Resume"])


class AnalyzeRequest(BaseModel):
    resume_id: str
    jd_text: str


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """Uploads a PDF resume, extracts markdown, normalizes to ResumeSchema, and saves."""
    return await process_resume_upload(file=file, user_id=user_id)


@router.post("/analyze")
async def analyze_resume(request: AnalyzeRequest):
    """Calculates deterministic ATS score & recommendations against the provided Job Description."""
    return await analyze_resume_against_jd(
        resume_id=request.resume_id,
        jd_text=request.jd_text,
    )


@router.get("/history")
async def get_resume_history_endpoint(
    user_id: Optional[str] = Query(default=None),
):
    """List uploaded resumes for the given user (or the demo user)."""
    return get_resume_history(user_id=user_id)


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    """Retrieves resume data, latest ATS analysis, and CV payload."""
    return get_resume_details(resume_id=resume_id)
