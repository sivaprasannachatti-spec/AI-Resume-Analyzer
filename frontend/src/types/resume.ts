export interface PersonalInfo {
  name: string;
  email: string;
  phone?: string | null;
  title?: string | null;
  location?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
}

export interface Project {
  id: number;
  project_name: string;
  project_years: string;
  project_description: string[];
  project_url?: string | null;
  project_technologies: string[];
  project_github_url?: string | null;
}

export interface WorkExperience {
  id: number;
  company: string;
  title: string;
  location?: string | null;
  years: string;
  responsibilities: string[];
}

export interface Education {
  institution: string;
  degree: string;
  field_of_study?: string | null;
  years: string;
  description?: string | null;
}

export interface AdditionalInfo {
  technicalSkills?: string[] | Record<string, string[] | string>;
  languages?: string[];
  certificationsTraining?: string[];
  awards?: string[];
  [key: string]: any;
}

export interface CustomSectionItem {
  id?: number;
  title?: string;
  years?: string;
  description?: string | string[];
  descriptionStyles?: string[];
}

export interface CustomSection {
  type?: string;
  key?: string;
  title?: string;
  items?: CustomSectionItem[];
  [key: string]: any;
}

export interface ResumeSchema {
  personalInfo: PersonalInfo;
  summary?: string | null;
  projects: Project[];
  workExperience: WorkExperience[];
  education: Education[];
  additional?: AdditionalInfo | AdditionalInfo[] | Record<string, any>;
  customSections?: CustomSection[];
  skills?: string[] | Record<string, string[] | string>;
  [key: string]: any;
}

export interface AtsSubScores {
  keyword_match?: number | null;
  skills_coverage?: number | null;
  title_match?: number | null;
  section_completeness?: number | null;
  date_consistency?: number | null;
}

export interface AtsAnalysisResult {
  analysis_id: string;
  overall_score: number;
  sub_scores: AtsSubScores;
  key_skills: string[];
  missing_skills: string[];
  recommendations: string[];
  jd_parsed?: {
    role: string;
    job_description: string;
    required_skills: string[];
    preferred_skills: string[];
    keywords: string[];
  };
}

export interface AtsScoreBreakdown {
  overall_score: number;
  sub_scores: AtsSubScores;
  key_skills: string[];
  missing_skills: string[];
  recommendations: string[];
}

export interface AtsScorePair {
  original: AtsScoreBreakdown;
  tailored: AtsScoreBreakdown;
}

export interface ChatMessage {
  id?: string;
  type: "User" | "AI" | "assistant" | "user";
  message: string;
}
