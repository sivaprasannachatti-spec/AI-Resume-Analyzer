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

class Projects(BaseModel):
    project_name: str = Field(..., description="The name of the project")
    project_description: List[str] = Field(default_factory=list, description="The description of the project")
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
    cgpa: Optional[float] = Field(None, description="CGPA, percentage, or class, as written in the resume")
    percentage: Optional[float] = Field(None, description="Percentage of user")

class Achievements(BaseModel):
    title: str = Field(..., description="The title of the achievement")
    description: Optional[List[str]] = Field(default_factory=list, description="The description of the achievement")

class AcademicPositions(BaseModel):
    position_title: Optional[str] = Field(None, description="The name of the position")
    start_date: Optional[str] = Field(None, description="The year when the position held")
    end_date: Optional[str] = Field(None, description="The year when the position lost")
    position_description: Optional[List[str]] = Field(default_factory=list, description="The description of the position")

class Certifications(BaseModel):
    certification_name: str = Field(..., description="The name of the certification")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    certification_description: Optional[List[str]] = Field(default_factory=list, description="The description of the certification")
    issue_date: Optional[str] = Field(None, description="Year obtained")
    expiry_date: Optional[str] = Field(None, description="Year when the certificate expires")

class ResumeSchema(BaseModel):
    personalInfo: PersonalInfo = Field(..., description="Personal information")
    summary: Optional[str] = Field(None, description="Summary of the candidate's profile")
    projects: List[Projects] = Field(default_factory=list, description="List of projects")
    workExperience: List[WorkExperience] = Field(default_factory=list, description="List of work experiences")
    education: List[Education] = Field(default_factory=list, description="List of educational qualifications")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    certifications: Optional[List[Certifications]] = Field(default_factory=list, description="List of certifications")
    achievements: Optional[List[Achievements]] = Field(default_factory=list, description="List of achievements")
    academicPositions: Optional[List[AcademicPositions]] = Field(default_factory=list, description="List of academic positions")

class JDSchema(BaseModel):
    role: str = Field(..., description="The role for which the job description is provided")
    job_description: str = Field(..., description="The job description text")
    required_skills: List[str] = Field(default_factory=list, description="Required skills for the role")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills for the role")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the job description")