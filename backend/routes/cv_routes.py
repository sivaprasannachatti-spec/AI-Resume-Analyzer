from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, Query
from pydantic import BaseModel

from backend.controllers.cv_controller import (
    handle_tailor_cv,
    handle_confirm_tailored_resume,
    handle_generate_outreach_message,
    handle_update_tailored_resume,
    handle_update_outreach_message,
    handle_get_outreach_message_history,
    handle_save_cv_pdf,
    get_current_cv
)
router = APIRouter(prefix="/api/cv", tags=["CV Generator & Editor"])


class TailorCVRequest(BaseModel):
    resume_id: str
    raw_jd: Optional[str] = ""


class UpdateTailoredResumeRequest(BaseModel):
    resume_id: str
    tailored_resume_payload: Dict[str, Any]
    raw_jd: str
    template_settings: Optional[Dict[str, Any]] = None


class ConfirmTailoredResumeRequest(BaseModel):
    resume_id: str
    tailored_resume_payload: Dict[str, Any]
    raw_jd: Optional[str] = ""
    template_settings: Optional[Dict[str, Any]] = None


class GenerateOutreachMessageRequest(BaseModel):
    job_description: str
    language: str = "en"


class UpdateOutreachMessageRequest(BaseModel):
    message: str


@router.post("/tailor")
async def tailor_cv(request: TailorCVRequest):
    """Tailors candidate's CV specifically for the target job description."""
    return await handle_tailor_cv(
        resume_id=request.resume_id,
        raw_jd=request.raw_jd,
    )


@router.post("/tailored-resume/{tailored_resume_id}/outreach-messages")
async def generate_outreach_message_endpoint(
    tailored_resume_id: str,
    request: GenerateOutreachMessageRequest,
):
    """Generate an outreach message for a saved tailored resume and persist it."""
    return await handle_generate_outreach_message(
        tailored_resume_id=tailored_resume_id,
        job_description=request.job_description,
        language=request.language,
    )


@router.put("/outreach-messages/{outreach_id}")
async def update_outreach_message_endpoint(
    outreach_id: str,
    request: UpdateOutreachMessageRequest,
):
    """Persist user edits to an outreach message."""
    return handle_update_outreach_message(
        outreach_id=outreach_id,
        message=request.message,
    )


@router.get("/outreach-messages/history")
async def get_outreach_message_history_endpoint(
    user_id: Optional[str] = Query(default=None),
):
    """List saved outreach drafts for the given user (or the demo user)."""
    return handle_get_outreach_message_history(user_id=user_id)


@router.put("/tailored-resume")
async def update_tailored_resume_endpoint(request: UpdateTailoredResumeRequest):
    """Persists manual edits to the tailored resume."""
    return await handle_update_tailored_resume(
        resume_id=request.resume_id,
        tailored_resume_payload=request.tailored_resume_payload,
        template_settings=request.template_settings,
        raw_jd=request.raw_jd,
    )


@router.post("/tailored-resume/confirm")
async def confirm_tailored_resume_endpoint(request: ConfirmTailoredResumeRequest):
    """Persist the tailored-resume preview after user confirmation."""
    return await handle_confirm_tailored_resume(
        resume_id=request.resume_id,
        tailored_resume_payload=request.tailored_resume_payload,
        raw_jd=request.raw_jd or "",
        template_settings=request.template_settings,
    )


@router.post("/save-pdf")
async def save_pdf_endpoint(
    resume_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Uploads finalized in-browser generated PDF to Backblaze B2 and links file_url in DB."""
    return await handle_save_cv_pdf(resume_id=resume_id, file=file)


@router.get("/{resume_id}")
async def get_cv_endpoint(resume_id: str):
    """Fetches the latest structured CV payload for rendering."""
    return get_current_cv(resume_id=resume_id)
