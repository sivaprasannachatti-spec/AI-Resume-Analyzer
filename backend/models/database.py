import sys
from logging import getLogger
import backend.models.schemas

from sqlalchemy import inspect, text
from sqlmodel import Session, create_engine, SQLModel

from src.exception import CustomException
from config import DATABASE_URL

logger = getLogger(__name__)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS master_resume_payload JSON "
                    "NOT NULL DEFAULT '{}'::json"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE tailored_resumes "
                    "ADD COLUMN IF NOT EXISTS template_settings JSON "
                    "NOT NULL DEFAULT '{}'::json"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE resume_analysis "
                    "ADD COLUMN IF NOT EXISTS tailored_match_score FLOAT"
                )
            )
        columns = {
            column["name"] for column in inspect(engine).get_columns("resumes")
        }
        if "master_resume_payload" not in columns:
            raise RuntimeError(
                "Database migration failed: resumes.master_resume_payload was not created"
            )
        tailored_columns = {
            column["name"]
            for column in inspect(engine).get_columns("tailored_resumes")
        }
        if "template_settings" not in tailored_columns:
            raise RuntimeError(
                "Database migration failed: tailored_resumes.template_settings was not created"
            )
        analysis_columns = {
            column["name"]
            for column in inspect(engine).get_columns("resume_analysis")
        }
        if "tailored_match_score" not in analysis_columns:
            raise RuntimeError(
                "Database migration failed: resume_analysis.tailored_match_score was not created"
            )
        logger.info("Database schema verified: resumes.master_resume_payload is available")
    except Exception as e:
        raise CustomException(e, sys)

def get_session():
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        raise CustomException(e, sys)
