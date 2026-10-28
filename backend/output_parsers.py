from pydantic import BaseModel, Field
from typing import List, Optional


class PersonalInfo(BaseModel):
    name: str = Field(..., description="The name of the candidate")
    email: str = Field(..., description="The email of the candidate")
    phone: Optional[str] = Field(None, description="The phone number of the candidate")
    title: Optional[str] = Field(None, description="The title or position of the candidate")
    location: Optional[str] = Field(None, description="City/state/country of the candidate")
    github_url: Optional[str] = Field(None, description="The GitHub profile URL")
    linkedin_url: Optional[str] = Field(None, description="The LinkedIn profile URL")
    twitter_url: Optional[str] = Field(None, description="The Twitter profile URL")
    portfolio_url: Optional[str] = Field(None, description="Personal website or portfolio URL")


class Project(BaseModel):
    project_name: str = Field(..., description="The name of the project")
    project_description: str = Field(..., description="The description of the project")
    project_url: Optional[str] = Field(None, description="The URL of the project")
    project_technologies: List[str] = Field(default_factory=list, description="Technologies used in the project")
    project_github_url: Optional[str] = Field(None, description="The GitHub URL of the project")


class WorkExperience(BaseModel):
    company: str = Field(..., description="The name of the company")
    position: str = Field(..., description="The position held at the company")
    location: Optional[str] = Field(None, description="Job location")
    start_date: str = Field(..., description="The start date of the position")
    end_date: Optional[str] = Field(None, description="The end date (None if current)")
    responsibilities: List[str] = Field(default_factory=list, description="Responsibilities and achievements at the position")


class Education(BaseModel):
    institution: str = Field(..., description="The name of the educational institution")
    degree: str = Field(..., description="The degree obtained")
    field_of_study: Optional[str] = Field(None, description="The field of study")
    start_date: Optional[str] = Field(None, description="The start date of the education")
    end_date: Optional[str] = Field(None, description="The end date (None if ongoing)")
    grade: Optional[str] = Field(None, description="CGPA, percentage, or class, as written in the resume")
    thesis_title: Optional[str] = Field(None, description="Thesis or dissertation title, if mentioned")


class Achievement(BaseModel):
    title: str = Field(..., description="The title of the achievement")
    description: Optional[str] = Field(None, description="The description of the achievement")


class Certification(BaseModel):
    certification_name: str = Field(..., description="The name of the certification")
    certification_description: Optional[str] = Field(None, description="The description of the certification")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    year: Optional[str] = Field(None, description="Year obtained")


# --- CV-specific sections (all optional; only filled if present in the resume) ---

class Publication(BaseModel):
    title: str
    venue: Optional[str] = None
    year: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class TeachingExperience(BaseModel):
    course_or_role: str
    institution: Optional[str] = None
    period: Optional[str] = None
    description: Optional[str] = None


class Language(BaseModel):
    language: str
    proficiency: Optional[str] = None


class Reference(BaseModel):
    name: str
    designation: Optional[str] = None
    organization: Optional[str] = None
    contact: Optional[str] = None


class ResumeSchema(BaseModel):
    personalInfo: PersonalInfo = Field(..., description="Personal information")
    summary: Optional[str] = Field(None, description="Summary of the candidate's profile")
    projects: List[Project] = Field(default_factory=list, description="List of projects")
    workExperience: List[WorkExperience] = Field(default_factory=list, description="List of work experiences")
    education: List[Education] = Field(default_factory=list, description="List of educational qualifications")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    certifications: List[Certification] = Field(default_factory=list, description="List of certifications")
    achievements: List[Achievement] = Field(default_factory=list, description="List of achievements")

    # CV-only extras
    publications: List[Publication] = Field(default_factory=list)
    teachingExperience: List[TeachingExperience] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)


class JDSchema(BaseModel):
    role: str = Field(..., description="The role for which the job description is provided")
    job_description: str = Field(..., description="The job description text")
    required_skills: List[str] = Field(default_factory=list, description="Required skills for the role")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills for the role")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the job description")