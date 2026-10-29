import sys
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import List, Optional, Dict
from uuid import uuid4
from datetime import datetime, timezone
from logging import getLogger

from src.exception import CustomException

logger = getLogger(__name__)

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
        uploaded_at: datetime = Field(default_factory=_now, description="The timestamp when the resume was uploaded")

        # Relationships (Fixed name to avoid shadowing user_id)
        user: Optional[Users] = Relationship(back_populates="resumes")
        analyses: List["ResumeAnalysis"] = Relationship(back_populates="resume", cascade_delete=True)
        cvs: List["CVS"] = Relationship(back_populates="resume", cascade_delete=True)

    class ResumeAnalysis(SQLModel, table=True):
        __tablename__ = "resume_analysis"
        
        analysis_id: str = Field(default_factory=_uuid, primary_key=True)
        resume_id: str = Field(..., foreign_key="resumes.resume_id", description="The ID of the resume being analyzed")
        jd: str = Field(..., description="The job description for the role the user is applying")
        match_score: float = Field(..., description="The match score between the resume and the job description")
        key_skills: List[str] = Field(default=[], sa_column=Column(JSON), description="The key skills extracted from the resume")
        missing_skills: List[str] = Field(default=[], sa_column=Column(JSON), description="The skills missing in the resume compared to the JD")
        ats_issues: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON), description="The ATS issues found in the resume")

        # Relationships (Fixed foreign_key table name typo from 'resume' to 'resumes')
        resume: Optional[Resumes] = Relationship(back_populates="analyses")

    class CVS(SQLModel, table=True):
        __tablename__ = "cvs"
        
        cv_id: str = Field(default_factory=_uuid, primary_key=True)
        resume_id: str = Field(..., foreign_key="resumes.resume_id", description="The ID of the resume associated with the CV")
        cv_payload: Dict = Field(default={}, sa_column=Column(JSON), description="The payload of the CV in JSON format")
        file_name: Optional[str] = Field(default=None, description="The name of the CV file")
        file_url: Optional[str] = Field(default=None, description="The URL of the CV file")
        created_at: datetime = Field(default_factory=_now, description="The timestamp when the CV was created")
        updated_at: datetime = Field(default_factory=_now, description="The timestamp when the CV was last updated")

        # Relationships
        resume: Optional[Resumes] = Relationship(back_populates="cvs")
        chat: Optional["Chats"] = Relationship(back_populates="cv", sa_relationship_kwargs={"uselist": False}, cascade_delete=True)

    class Chats(SQLModel, table=True):
        __tablename__ = "chats"
        
        chat_id: str = Field(default_factory=_uuid, primary_key=True)
        cv_id: str = Field(..., foreign_key="cvs.cv_id", unique=True, description="The ID of the CV associated with the chat (Unique enforces 1-to-1)")
        chat_title: str = Field(..., description="The title of the chat")
        created_at: datetime = Field(default_factory=_now, description="The timestamp when the chat was created")

        # Relationships
        cv: Optional[CVS] = Relationship(back_populates="chat")
        messages: List["Messages"] = Relationship(back_populates="chat", cascade_delete=True)

    class Messages(SQLModel, table=True):
        __tablename__ = "messages"
        
        message_id: str = Field(default_factory=_uuid, primary_key=True)
        chat_id: str = Field(..., foreign_key="chats.chat_id", description="The ID of the chat associated with the message")
        type: str = Field(..., description="The type of the message (e.g., user, assistant)")
        message: str = Field(..., description="The content of the message")

        # Relationships
        chat: Optional[Chats] = Relationship(back_populates="messages")

except Exception as e:
    raise CustomException(e, sys)