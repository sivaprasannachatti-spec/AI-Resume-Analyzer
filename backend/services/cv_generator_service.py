import sys
import json
from sqlmodel import Session, select
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.exception import CustomException
from backend.prompts import TAILOR_RESUME_PROMPT, UPDATE_RESUME_PROMPT
from backend.models.schemas import CVS, ResumeAnalysis
from backend.models.database import engine
from backend.output_parsers import ResumeSchema
from config import OPENROUTER_API_KEY_1


def generate_new_cv(resume_id: str, raw_jd: str = "") -> dict:
    """
    Tailors an existing candidate CV to a target job description (raw_jd).
    If raw_jd is not provided, attempts to fetch it from ResumeAnalysis for this resume_id.
    """
    try:
        # 1. Fetch existing candidate CV from DB
        with Session(engine) as session:
            cv_record = session.exec(select(CVS).where(CVS.resume_id == resume_id)).first()
            if not cv_record or not cv_record.cv_payload:
                raise CustomException(f"No CV payload found for resume_id: {resume_id}", sys)
            existing_cv_payload = cv_record.cv_payload

            # If raw_jd not passed, fallback to saved JD in ResumeAnalysis
            if not raw_jd:
                analysis = session.exec(select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)).first()
                if analysis and analysis.jd:
                    raw_jd = analysis.jd

        # 2. Initialize LLM
        model = ChatOpenAI(
            model="mistralai/mistral-small-3.2-24b-instruct",
            api_key=OPENROUTER_API_KEY_1,
            base_url="https://openrouter.ai/api/v1",
        )

        # 3. Invoke structured tailoring chain
        chain = (
            ChatPromptTemplate.from_template(TAILOR_RESUME_PROMPT)
            | model.with_structured_output(schema=ResumeSchema)
        )
        tailored_cv = chain.invoke({
            "resume_schema": json.dumps(existing_cv_payload, indent=2),
            "jd_schema": "",
            "raw_jd": raw_jd or "General role optimization",
        })
        tailored_cv_dict = tailored_cv.model_dump()

        # 4. Save tailored CV payload in database
        with Session(engine) as session:
            cv_record = session.exec(select(CVS).where(CVS.resume_id == resume_id)).first()
            if cv_record:
                cv_record.cv_payload = tailored_cv_dict
                session.add(cv_record)
                session.commit()
                session.refresh(cv_record)

        return tailored_cv_dict

    except Exception as e:
        raise CustomException(e, sys)


def update_cv(resume_id: str, user_query: str, cv_payload: dict | None = None) -> dict:
    """
    Updates candidate CV based on user_query and saves the updated payload in database.
    If cv_payload is not provided, fetches current cv_payload from database.
    """
    try:
        # 1. Obtain current CV payload
        if not cv_payload:
            with Session(engine) as session:
                cv_record = session.exec(select(CVS).where(CVS.resume_id == resume_id)).first()
                if not cv_record or not cv_record.cv_payload:
                    raise CustomException(f"No CV payload found for resume_id: {resume_id}", sys)
                current_payload = cv_record.cv_payload
        else:
            current_payload = cv_payload

        # 2. Initialize LLM
        model = ChatOpenAI(
            model="mistralai/mistral-small-3.2-24b-instruct",
            api_key=OPENROUTER_API_KEY_1,
            base_url="https://openrouter.ai/api/v1",
        )

        # 3. Invoke structured update chain
        chain = (
            ChatPromptTemplate.from_template(UPDATE_RESUME_PROMPT)
            | model.with_structured_output(schema=ResumeSchema)
        )
        updated_cv = chain.invoke({
            "cv_payload": json.dumps(current_payload, indent=2),
            "user_query": user_query,
        })
        updated_cv_dict = updated_cv.model_dump()

        # 4. Save updated payload back to database
        with Session(engine) as session:
            cv_record = session.exec(select(CVS).where(CVS.resume_id == resume_id)).first()
            if not cv_record:
                raise CustomException(f"Failed to fetch the CV from database for resume_id: {resume_id}", sys)
            cv_record.cv_payload = updated_cv_dict
            session.add(cv_record)
            session.commit()
            session.refresh(cv_record)

        return updated_cv_dict

    except Exception as e:
        raise CustomException(e, sys)


def save_cv(resume_id: str, file_name: str, file_url: str) -> str:
    """
    Saves the finalized file_name and Backblaze B2 file_url into the CVS record.
    Returns the cv_id.
    """
    try:
        with Session(engine) as session:
            cv = session.exec(select(CVS).where(CVS.resume_id == resume_id)).first()
            if not cv:
                raise CustomException(f"Failed to fetch the CV from database for resume_id: {resume_id}", sys)
            cv.file_name = file_name
            cv.file_url = file_url
            session.add(cv)
            session.commit()
            session.refresh(cv)
            return cv.cv_id

    except Exception as e:
        raise CustomException(e, sys)