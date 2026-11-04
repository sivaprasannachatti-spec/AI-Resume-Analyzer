import sys
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
from uuid import uuid4
from datetime import datetime, timezone
from logging import getLogger

from src.exception import CustomException

logger = getLogger(__name__)


class TemplateSettings(BaseModel):
    template: str = "swiss-single"
    pageSize: Literal["A4", "LETTER"] = "A4"
    margins: Dict[str, float] = Field(
        default_factory=lambda: {"top": 10, "bottom": 10, "left": 10, "right": 10}
    )
    spacing: Dict[str, int] = Field(
        default_factory=lambda: {"section": 3, "item": 2, "lineHeight": 3}
    )
    fontSize: Dict[str, object] = Field(
        default_factory=lambda: {
            "base": 3,
            "headerScale": 3,
            "headerFont": "serif",
            "bodyFont": "sans-serif",
        }
    )
    compactMode: bool = False
    showContactIcons: bool = False
    accentColor: Literal["blue", "green", "orange", "red"] = "blue"

def _uuid() -> str:
    return str(uuid4())

def _now() -> datetime:
    return datetime.now(timezone.utc)

try:
    class Users(SQLModel, table=True):
        __tablename__ = "users"
        
        user_id: str = Field(default_factory=_uuid, primary_key=True)
        name: str = Field(..., description="The name of the user")
        email: str = Field(..., description="The email of the user", unique=True, index=True)
        password: str = Field(..., description="The password of the user")
        created_at: datetime = Field(default_factory=_now, description="The timestamp when the user was created")

        # Relationships
        resumes: List["Resumes"] = Relationship(back_populates="user", cascade_delete=True)

    class Resumes(SQLModel, table=True):
        __tablename__ = "resumes"
        
        resume_id: str = Field(default_factory=_uuid, primary_key=True)
        user_id: str = Field(..., foreign_key="users.user_id", description="The ID of the user who owns the resume")
        resume_url: str = Field(..., description="The URL of the resume")
        master_resume_payload: Dict = Field(
            default_factory=dict,
            sa_column=Column(JSON),
            description="The original parsed resume payload used as the source of truth",
        )
        uploaded_at: datetime = Field(default_factory=_now, description="The timestamp when the resume was uploaded")

        # Relationships (Fixed name to avoid shadowing user_id)
        user: Optional[Users] = Relationship(back_populates="resumes")
        analyses: List["ResumeAnalysis"] = Relationship(back_populates="resume", cascade_delete=True)
        tailored_resumes: List["TailoredResume"] = Relationship(
            back_populates="resume", cascade_delete=True
        )

    class ResumeAnalysis(SQLModel, table=True):
        __tablename__ = "resume_analysis"
        
        analysis_id: str = Field(default_factory=_uuid, primary_key=True)
        resume_id: str = Field(..., foreign_key="resumes.resume_id", description="The ID of the resume being analyzed")
        jd: str = Field(..., description="The job description for the role the user is applying")
        match_score: float = Field(..., description="The match score between the resume and the job description")
        tailored_match_score: Optional[float] = Field(
            default=None,
            description="The ATS match score for the tailored resume against the same job description",
        )
        key_skills: List[str] = Field(default=[], sa_column=Column(JSON), description="The key skills extracted from the resume")
        missing_skills: List[str] = Field(default=[], sa_column=Column(JSON), description="The skills missing in the resume compared to the JD")
        ats_issues: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON), description="The ATS issues found in the resume")

        # Relationships (Fixed foreign_key table name typo from 'resume' to 'resumes')
        resume: Optional[Resumes] = Relationship(back_populates="analyses")

    class TailoredResume(SQLModel, table=True):
        __tablename__ = "tailored_resumes"
        
        tailored_resume_id: str = Field(default_factory=_uuid, primary_key=True)
        resume_id: str = Field(
            ...,
            foreign_key="resumes.resume_id",
            unique=True,
            index=True,
            description="The ID of the resume associated with this tailored resume",
        )
        tailored_resume_payload: Dict = Field(
            default_factory=dict,
            sa_column=Column(JSON),
            description="The tailored resume payload in JSON format",
        )
        template_settings: Dict = Field(
            default_factory=lambda: TemplateSettings().model_dump(),
            sa_column=Column(JSON),
            description="Formatting settings used by the shared resume renderer",
        )
        file_name: Optional[str] = Field(
            default=None,
            description="The downloaded tailored resume file name",
        )
        file_url: Optional[str] = Field(
            default=None,
            description="The downloaded tailored resume URL",
        )
        created_at: datetime = Field(
            default_factory=_now,
            description="The timestamp when the tailored resume was created",
        )
        updated_at: datetime = Field(
            default_factory=_now,
            description="The timestamp when the tailored resume was last updated",
        )

        # Relationships
        resume: Optional[Resumes] = Relationship(back_populates="tailored_resumes")
except Exception as e:
    raise CustomException(e, sys)