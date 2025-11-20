import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from engine import CollabEngine
from generator import generate_synthetic_data
from models import Employee
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engine
api_key = os.getenv("OPENAI_API_KEY")
engine = CollabEngine(api_key=api_key)

# Load initial data
print("Loading synthetic data...")
employees = generate_synthetic_data(30)
engine.load_employees(employees)
print("Data loaded.")

class RecommendRequest(BaseModel):
    resumeText: str

class ProjectResponse(BaseModel):
    name: str
    description: str
    tech: List[str]

class ResumeMatchResponse(BaseModel):
    sharedSkills: List[str]
    matchingProjects: List[str]
    matchingDomains: List[str]
    techOverlap: List[str]
    matchingSeniority: bool
    reasonSummary: str

class Recommendation(BaseModel):
    id: str
    name: str
    title: str
    department: str
    location: str
    email: str
    manager: str
    experienceYears: int
    professionalSummary: str
    skills: List[str]
    primarySkills: List[str]
    secondarySkills: List[str]
    tools: List[str]
    projects: List[ProjectResponse]
    matchScore: float
    summary: str
    avatarUrl: str
    resumeMatch: Optional[ResumeMatchResponse] = None
    collaborationSuggestions: List[str] = []

class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]

@app.post("/api/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    if not request.resumeText:
        raise HTTPException(status_code=400, detail="Resume text is required")

    # Create a temporary employee object for the target
    # In a real app, we'd parse the resume text to extract skills/role first
    # Here we'll just use the raw text for embedding generation if the engine supports it
    # or we might need to fake a profile.
    # Since our engine uses `emp.raw_text` in `_compute_embeddings`, we can create a dummy emp.
    
    # Hack: We need to add this temp employee to the engine to get its embedding, 
    # then find similar, then remove it? Or just expose a method to get embedding for text.
    # For this POC, let's add it, find similar, then remove.
    
    target_id = "temp_target"
    target_profile = Employee(
        id=target_id,
        name="Candidate",
        email="candidate@example.com",
        profile=type('obj', (object,), {
            'role': 'Unknown', 'department': 'Unknown', 'seniority': 'Unknown',
            'skills': [], 'projects': [], 'interests': []
        }),
        raw_text=request.resumeText
    )
    
    # We need to re-compute embeddings including this new one. 
    # This is inefficient but fine for POC.
    current_employees = engine.employees
    engine.load_employees(current_employees + [target_profile])
    
    recommendations = engine.find_similar_employees(target_id)
    
    # Generate detailed match data for each recommendation
    response_list = []
    for rec in recommendations:
        emp = rec['employee']
        
        # Generate detailed match explanation
        match_details = engine.generate_detailed_match(target_profile, emp)
        
        # Create resume match response
        resume_match = ResumeMatchResponse(
            sharedSkills=match_details['shared_skills'],
            matchingProjects=match_details['matching_projects'],
            matchingDomains=match_details['matching_domains'],
            techOverlap=match_details['tech_overlap'],
            matchingSeniority=match_details['matching_seniority'],
            reasonSummary=match_details['reason_summary']
        )
        
        # Create project responses
        projects_response = [
            ProjectResponse(name=p.name, description=p.description, tech=p.tech)
            for p in emp.profile.projects
        ]
        
        # Use LLM-generated reason for short summary
        short_summary = match_details['reason_summary']
        
        response_list.append(Recommendation(
            id=emp.id,
            name=emp.name,
            title=emp.profile.role,
            department=emp.profile.department,
            location=emp.profile.location,
            email=emp.email,
            manager=emp.profile.manager,
            experienceYears=emp.profile.experience_years,
            professionalSummary=emp.profile.professional_summary,
            skills=emp.profile.skills,
            primarySkills=emp.profile.primary_skills,
            secondarySkills=emp.profile.secondary_skills,
            tools=emp.profile.tools,
            projects=projects_response,
            matchScore=rec['score'],
            summary=short_summary,
            avatarUrl=f"https://ui-avatars.com/api/?name={emp.name.replace(' ', '+')}&background=random",
            resumeMatch=resume_match,
            collaborationSuggestions=match_details['collaboration_suggestions']
        ))
        
    # Restore original list to avoid polluting state
    engine.load_employees(current_employees)
    
    return RecommendResponse(recommendations=response_list)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
