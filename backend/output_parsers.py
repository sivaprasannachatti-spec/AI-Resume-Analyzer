from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import List, Optional, Literal, Union, Dict, Any

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
    id: Optional[int] = Field(None, description="Unique identifier for the project")
    project_name: str = Field(..., description="The name of the project")
    project_years: Optional[str] = Field("", description="The years during which the project was active")
    project_description: List[str] = Field(default_factory=list, description="The description of the project")
    project_url: Optional[str] = Field(None, description="The URL of the project")
    project_technologies: List[str] = Field(default_factory=list, description="Technologies used in the project")
    project_github_url: Optional[str] = Field(None, description="The GitHub URL of the project")

class WorkExperience(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the work experience entry")
    title: str = Field(..., description="The title of the position held")
    company: str = Field(..., description="The name of the company")
    location: Optional[str] = Field(None, description="Job location")
    years: Optional[str] = Field(None, description="Years of experience in the position")
    responsibilities: List[str] = Field(default_factory=list, description="Responsibilities or work done in the company")

class Education(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the education entry")
    institution: str = Field(..., description="The name of the educational institution")
    degree: str = Field(..., description="The degree obtained")
    years: Optional[str] = Field(None, description="Years of study")
    description: Optional[str] = Field(None, description="Additional details about the education")

class AdditionalInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    technicalSkills: Optional[Union[List[str], Dict[str, Any]]] = Field(default_factory=list, description="The list or map of skills present in resume")
    languages: Optional[List[str]] = Field(default_factory=list, description="Languages known by the user")
    certificationsTraining: Optional[List[str]] = Field(default_factory=list, description="Certifications and training present in resume")
    awards: Optional[List[str]] = Field(default_factory=list, description="Awards present in resume")

class CustomSectionItem(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    years: Optional[str] = None
    description: Optional[Union[str, List[str]]] = None
    descriptionStyles: Optional[List[str]] = None

class CustomSection(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Optional[str] = None
    key: Optional[str] = None
    title: Optional[str] = None
    items: Optional[List[Union[CustomSectionItem, Dict[str, Any]]]] = Field(default_factory=list)

class ResumeSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    personalInfo: PersonalInfo = Field(..., description="Personal information")
    summary: Optional[str] = Field(None, description="Summary of the candidate's profile")
    workExperience: List[WorkExperience] = Field(default_factory=list, description="List of work experiences")
    education: List[Education] = Field(default_factory=list, description="List of educational qualifications")
    projects: List[Projects] = Field(default_factory=list, description="List of projects")
    additional: Optional[Union[AdditionalInfo, Dict[str, Any], List[Any]]] = Field(default_factory=dict, description="Additional information such as skills, languages, certifications, and awards")
    customSections: Optional[List[Union[CustomSection, Dict[str, Any]]]] = Field(default_factory=list, description="Custom sections such as Academic Positions, Leadership, Extracurriculars")

class JDSchema(BaseModel):
    company: str = Field(..., description="The name of the company offering the job")
    role: str = Field(..., description="The role for which the job description is provided")
    required_skills: List[str] = Field(default_factory=list, description="Required skills for the role")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills for the role")
    experience_requirements: List[str] = Field(None, description="Experience required for the role")
    education_requirements: List[str] = Field(None, description="Education required for the role")
    key_responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities for the role")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the job description")
    experience_years: int = Field(None, description="Years of experience required for the role")
    seniority_level: str = Field(None, description="Seniority level for the role")

class ResumeChange(BaseModel):
    """A single targeted change the LLM wants to make to the resume."""

    path: str = Field(
        description=(
            "Dot+bracket path, e.g. "
            "'workExperience[0].responsibilities[1]'"
        )
    )
    action: Literal["replace", "append", "reorder", "add_skill"]
    original: str | list[str] | None = Field(
        default=None,
        description="Current text at path — for verification. May be a list (the "
        "current items) for the reorder action; only used for text verification of "
        "replace/append, ignored otherwise.",
    )
    value: str | list[str] = Field(description="New content")
    reason: str = Field(description="Why this change helps match the JD")

    @model_validator(mode="after")
    def _list_original_only_for_reorder(self) -> "ResumeChange":
        """A list ``original`` is only meaningful for ``reorder`` (the LLM sends
        the current items). For the text actions it must stay a string/None — a
        list there would silently bypass the replace verification gate and crash
        the invented-metrics check, so reject it at parse time."""
        if isinstance(self.original, list) and self.action != "reorder":
            raise ValueError("'original' may be a list only for the reorder action")
        return self


class ImproveDiffResult(BaseModel):
    """LLM output: a list of targeted resume changes."""

    changes: list[ResumeChange] = Field(default_factory=list)
    strategy_notes: str = Field(default="")
