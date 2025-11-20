from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Project:
    name: str
    description: str
    tech: List[str] = field(default_factory=list)

@dataclass
class ResumeMatch:
    shared_skills: List[str] = field(default_factory=list)
    matching_projects: List[str] = field(default_factory=list)
    matching_domains: List[str] = field(default_factory=list)
    tech_overlap: List[str] = field(default_factory=list)
    matching_seniority: bool = False
    reason_summary: str = ""

@dataclass
class Profile:
    role: str
    seniority: str
    department: str
    location: str = ""
    manager: str = ""
    experience_years: int = 0
    professional_summary: str = ""
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    primary_skills: List[str] = field(default_factory=list)
    secondary_skills: List[str] = field(default_factory=list)

@dataclass
class Employee:
    id: str
    name: str
    email: str
    profile: Profile
    raw_text: str = ""  # For resume text or summary
    embedding: Optional[List[float]] = None
    resume_match: Optional[ResumeMatch] = None
    collaboration_suggestions: List[str] = field(default_factory=list)

    def to_dict(self):
        projects_dict = [
            {"name": p.name, "description": p.description, "tech": p.tech}
            for p in self.profile.projects
        ]
        
        resume_match_dict = None
        if self.resume_match:
            resume_match_dict = {
                "sharedSkills": self.resume_match.shared_skills,
                "matchingProjects": self.resume_match.matching_projects,
                "matchingDomains": self.resume_match.matching_domains,
                "techOverlap": self.resume_match.tech_overlap,
                "matchingSeniority": self.resume_match.matching_seniority,
                "reasonSummary": self.resume_match.reason_summary
            }
        
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "profile": {
                "role": self.profile.role,
                "seniority": self.profile.seniority,
                "department": self.profile.department,
                "location": self.profile.location,
                "manager": self.profile.manager,
                "experienceYears": self.profile.experience_years,
                "professionalSummary": self.profile.professional_summary,
                "skills": self.profile.skills,
                "tools": self.profile.tools,
                "projects": projects_dict,
                "interests": self.profile.interests,
                "primarySkills": self.profile.primary_skills,
                "secondarySkills": self.profile.secondary_skills
            },
            "resumeMatch": resume_match_dict,
            "collaborationSuggestions": self.collaboration_suggestions
        }

