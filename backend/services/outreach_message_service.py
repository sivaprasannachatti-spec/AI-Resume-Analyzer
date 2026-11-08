import json
import sys
from datetime import datetime, timezone

import logging
from typing import Any
from fastapi import HTTPException
from sqlmodel import Session, select

from src.exception import CustomException
from backend.models.database import engine
from backend.models.schemas import OutReachMessages, TailoredResume, Resumes, Users
from backend.prompts import get_language_name, OUTREACH_MESSAGE_PROMPT
from backend.services.llm_services import complete

logger = logging.getLogger(__name__)

async def generate_outreach_message(
    resume_data: dict[str, Any],
    job_description: str,
    language: str = "en",
) -> str:
    """Generate a cold outreach message using a tailored resume and job description."""
    try:
        if not job_description.strip():
            raise ValueError("A job description is required to generate an outreach message")

        output_language = get_language_name(language)
        prompt = OUTREACH_MESSAGE_PROMPT.format(
            job_description=job_description,
            resume_data=json.dumps(resume_data, ensure_ascii=False),
            output_language=output_language,
        )

        result = await complete(
            prompt=prompt,
            system_prompt=(
                "You are a professional networking coach. Write genuine, detailed, "
                "easy-to-personalize cold outreach messages that follow the requested "
                "length and structure. Return only the message as plain text."
            ),
            max_tokens=1200,
        )

        message = result.strip()
        logger.info("Generated outreach message (characters=%d)", len(message))
        return message
    except Exception as e:
        raise CustomException(e, sys)


async def generate_and_save_outreach_message(
    tailored_resume_id: str,
    job_description: str,
    language: str = "en",
) -> dict[str, Any]:
    """Generate an outreach message from a saved tailored resume and persist it."""
    try:
        with Session(engine) as session:
            tailored_resume = session.exec(
                select(TailoredResume).where(
                    TailoredResume.tailored_resume_id == tailored_resume_id
                )
            ).first()
            if not tailored_resume:
                raise HTTPException(
                    status_code=404,
                    detail="Tailored resume not found",
                )
            resume_data = tailored_resume.tailored_resume_payload

        message = await generate_outreach_message(
            resume_data=resume_data,
            job_description=job_description,
            language=language,
        )
        if not message:
            raise ValueError("The generated outreach message was empty")

        with Session(engine) as session:
            outreach_message = OutReachMessages(
                tailored_resume_id=tailored_resume_id,
                message=message,
            )
            session.add(outreach_message)
            session.commit()
            session.refresh(outreach_message)

            return {
                "outreach_id": outreach_message.outreach_id,
                "tailored_resume_id": outreach_message.tailored_resume_id,
                "message": outreach_message.message,
                "created_at": outreach_message.created_at,
                "updated_at": outreach_message.updated_at,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys)


def update_outreach_message(outreach_id: str, message: str) -> dict[str, Any]:
    """Replace a saved outreach message with the user's edited text."""
    try:
        updated_message = message.strip()
        if not updated_message:
            raise ValueError("Outreach message cannot be empty")

        with Session(engine) as session:
            outreach_record = session.exec(
                select(OutReachMessages).where(
                    OutReachMessages.outreach_id == outreach_id
                )
            ).first()
            if not outreach_record:
                raise HTTPException(
                    status_code=404,
                    detail="Outreach message not found",
                )

            outreach_record.message = updated_message
            outreach_record.updated_at = datetime.now(timezone.utc)
            session.add(outreach_record)
            session.commit()
            session.refresh(outreach_record)

            return {
                "outreach_id": outreach_record.outreach_id,
                "tailored_resume_id": outreach_record.tailored_resume_id,
                "message": outreach_record.message,
                "created_at": outreach_record.created_at,
                "updated_at": outreach_record.updated_at,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise CustomException(e, sys)


def get_outreach_message_history(user_id: str | None = None) -> dict[str, Any]:
    """List saved outreach drafts belonging to a user."""
    try:
        with Session(engine) as session:
            records = session.exec(
                select(OutReachMessages, TailoredResume, Resumes)
                .join(
                    TailoredResume,
                    OutReachMessages.tailored_resume_id
                    == TailoredResume.tailored_resume_id,
                )
                .join(Resumes, TailoredResume.resume_id == Resumes.resume_id)
                .where(Resumes.user_id == user_id)
                .order_by(OutReachMessages.updated_at.desc())
            ).all()

            return {
                "outreach_messages": [
                    {
                        "outreach_id": outreach.outreach_id,
                        "tailored_resume_id": tailored.tailored_resume_id,
                        "resume_id": resume.resume_id,
                        "candidate_name": (
                            (resume.master_resume_payload or {})
                            .get("personalInfo", {})
                            .get("name", "Resume")
                        ),
                        "message": outreach.message,
                        "created_at": outreach.created_at,
                        "updated_at": outreach.updated_at,
                    }
                    for outreach, tailored, resume in records
                ]
            }
    except Exception as e:
        raise CustomException(e, sys)
