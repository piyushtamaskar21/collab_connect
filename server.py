import os
import sys
# Monkeypatch for Python < 3.10 compatibility
if sys.version_info < (3, 10):
    try:
        import importlib.metadata
        import importlib_metadata
        if not hasattr(importlib.metadata, "packages_distributions"):
            importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
    except ImportError:
        pass
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
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"API Key loaded: {api_key[:4]}...{api_key[-4:]}")
else:
    print("API Key NOT loaded from env")
engine = CollabEngine(api_key=api_key)

# Load initial data
print("Loading synthetic data...")
employees = generate_synthetic_data(30)
print("Generated Employees:")
for emp in employees[:5]:
    print(f"- {emp.name}")
engine.load_employees(employees)
print("Data loaded.")

class RecommendRequest(BaseModel):
    resumeText: Optional[str] = None
    searchQuery: Optional[str] = None
    mode: str = "resume"  # "resume" or "search"

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
    resumeMatch: Optional[ResumeMatchResponse] = None
    collaborationSuggestions: List[str] = []
    whyMatched: List[str] = []

class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]

@app.post("/api/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    if request.mode == "search":
        if not request.searchQuery:
            raise HTTPException(status_code=400, detail="Search query is required for search mode")
            
        # Check for "Typed Background Profile" (Heuristic: > 8 words)
        is_typed_background = len(request.searchQuery.split()) > 8
        
        if is_typed_background:
            print(f"Typed background detected (len={len(request.searchQuery.split())}). Switching to profile mode.")
            # Treat as resume/profile
            raw_text = request.searchQuery
            
            # Parse structured data
            parsed_profile = engine.parse_profile_from_text(raw_text)
            
            # Create target profile object
            # Mock Project objects for compatibility
            mock_projects = []
            for p in parsed_profile.get("projects", []):
                mock_p = type('obj', (object,), {
                    'name': p.get('name', 'Unknown Project'), 
                    'description': p.get('description', ''), 
                    'tech': p.get('tech', [])
                })
                mock_projects.append(mock_p)

            target_profile = Employee(
                id="typed_search_user",
                name="Search User",
                email="user@example.com",
                profile=type('obj', (object,), {
                    'role': parsed_profile.get("role", "Unknown"), 
                    'department': parsed_profile.get("department", "Unknown"), 
                    'seniority': parsed_profile.get("seniority", "Unknown"),
                    'skills': parsed_profile.get("skills", []), 
                    'projects': mock_projects, 
                    'interests': []
                }),
                raw_text=raw_text
            )
            
            # Use embedding search on the text
            recommendations = engine.find_similar_employees_by_text(raw_text)
            
            # Proceed to parallel detailed match generation (shared logic below)
            # We need to jump to the parallel execution block. 
            # To avoid code duplication, we can set a flag or structure the code to fall through.
            # But since we are inside an if/else block, we'll duplicate the parallel execution logic for clarity 
            # or refactor. Given the constraints, duplication with a shared helper function is safest if possible,
            # but defining a helper inside `recommend` is easier.
            
        else:
            # Standard Keyword/Short Search
            recommendations = engine.search_employees(request.searchQuery)
            
            # Create temp target profile from query for detailed matching
            target_profile = Employee(
                id="search_query",
                name="Search Query",
                email="search@example.com",
                profile=type('obj', (object,), {
                    'role': 'Search Context', 
                    'department': 'Unknown', 
                    'seniority': 'Unknown',
                    'skills': request.searchQuery.split(), # Treat query terms as skills
                    'projects': [], 
                    'interests': []
                }),
                raw_text=request.searchQuery
            )
            
            # For standard search, we might skip the heavy LLM detailed match for speed, 
            # BUT the user wants "Why Recommended" to be high quality.
            # The current implementation does a "FAST mode - no LLM" for standard search (line 124 in original).
            # We should keep that for short queries to be fast.
            
            response_list = []
            for rec in recommendations:
                emp = rec['employee']
                # Fast match (heuristic)
                match_details = engine.generate_detailed_match(target_profile, emp, use_llm=False)
                
                resume_match = ResumeMatchResponse(
                    sharedSkills=match_details['shared_skills'],
                    matchingProjects=match_details['matching_projects'],
                    matchingDomains=match_details['matching_domains'],
                    techOverlap=match_details['tech_overlap'],
                    matchingSeniority=match_details['matching_seniority'],
                    reasonSummary=match_details['reason_summary']
                )
                
                projects_response = [
                    ProjectResponse(name=p.name, description=p.description, tech=p.tech)
                    for p in emp.profile.projects
                ]
                
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
                    summary=match_details['reason_summary'],
                    avatarUrl=f"https://ui-avatars.com/api/?name={emp.name.replace(' ', '+')}&background=random",
                    resumeMatch=resume_match,
                    collaborationSuggestions=match_details['collaboration_suggestions'],
                    whyMatched=rec['whyMatched']
                ))
            return RecommendResponse(recommendations=response_list)

    elif request.mode == "name_search":
        if not request.searchQuery:
            raise HTTPException(status_code=400, detail="Search query is required for name search mode")
            
        recommendations = engine.search_employees_by_name(request.searchQuery)
        
        response_list = []
        for rec in recommendations:
            emp = rec['employee']
            projects_response = [
                ProjectResponse(name=p.name, description=p.description, tech=p.tech)
                for p in emp.profile.projects
            ]
            
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
                summary=" • ".join(rec['whyMatched']),
                avatarUrl=f"https://ui-avatars.com/api/?name={emp.name.replace(' ', '+')}&background=random",
                resumeMatch=None,
                collaborationSuggestions=[],
                whyMatched=rec['whyMatched']
            ))
        return RecommendResponse(recommendations=response_list)

    else:
        # Default to Resume Mode (or Typed Background fall-through)
        # If we fell through from "is_typed_background", we need to handle it here.
        # But we can't easily fall through from the `if` block above without refactoring.
        # So we'll handle the "Resume Mode" logic here and copy it for the typed background case above?
        # No, better to unify.
        pass

    # ---- UNIFIED RESUME / TYPED BACKGROUND LOGIC ----
    # If we are here, it's either explicit resume mode OR typed background mode.
    
    if request.mode == "search" and is_typed_background:
        raw_text = request.searchQuery
    elif request.resumeText:
        raw_text = request.resumeText
    else:
        raise HTTPException(status_code=400, detail="Resume text is required")

    # Parse structured data (Improved for BOTH resume and typed background)
    parsed_profile = engine.parse_profile_from_text(raw_text)
    
    mock_projects = []
    for p in parsed_profile.get("projects", []):
        mock_p = type('obj', (object,), {
            'name': p.get('name', 'Unknown Project'), 
            'description': p.get('description', ''), 
            'tech': p.get('tech', [])
        })
        mock_projects.append(mock_p)

    target_profile = Employee(
        id="target_user",
        name="Candidate",
        email="candidate@example.com",
        profile=type('obj', (object,), {
            'role': parsed_profile.get("role", "Unknown"), 
            'department': parsed_profile.get("department", "Unknown"), 
            'seniority': parsed_profile.get("seniority", "Unknown"),
            'skills': parsed_profile.get("skills", []), 
            'projects': mock_projects, 
            'interests': []
        }),
        raw_text=raw_text
    )
    
    # Optimized Search
    recommendations = engine.find_similar_employees_by_text(raw_text)
    
    # Parallelize LLM Calls
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    loop = asyncio.get_running_loop()
    
    def generate_details(emp):
        return engine.generate_detailed_match(target_profile, emp)

    with ThreadPoolExecutor() as pool:
        tasks = [
            loop.run_in_executor(pool, generate_details, rec['employee'])
            for rec in recommendations
        ]
        match_details_list = await asyncio.gather(*tasks)

    response_list = []
    for rec, match_details in zip(recommendations, match_details_list):
        emp = rec['employee']
        
        resume_match = ResumeMatchResponse(
            sharedSkills=match_details['shared_skills'],
            matchingProjects=match_details['matching_projects'],
            matchingDomains=match_details['matching_domains'],
            techOverlap=match_details['tech_overlap'],
            matchingSeniority=match_details['matching_seniority'],
            reasonSummary=match_details['reason_summary']
        )
        
        projects_response = [
            ProjectResponse(name=p.name, description=p.description, tech=p.tech)
            for p in emp.profile.projects
        ]
        
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
            summary=match_details['reason_summary'],
            avatarUrl=f"https://ui-avatars.com/api/?name={emp.name.replace(' ', '+')}&background=random",
            resumeMatch=resume_match,
            collaborationSuggestions=match_details['collaboration_suggestions'],
            whyMatched=[]
        ))
        
    return RecommendResponse(recommendations=response_list)

class MatchDetailsRequest(BaseModel):
    targetText: str
    employeeId: str

class MatchDetailsResponse(BaseModel):
    resumeMatch: ResumeMatchResponse
    collaborationSuggestions: List[str]

@app.post("/api/match-details", response_model=MatchDetailsResponse)
async def get_match_details(request: MatchDetailsRequest):
    # Find the employee
    emp = next((e for e in engine.employees if e.id == request.employeeId), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    # Create temp target profile from text
    target_profile = Employee(
        id="search_query",
        name="Search Context",
        email="search@example.com",
        profile=type('obj', (object,), {
            'role': 'Search Context', 
            'department': 'Unknown', 
            'seniority': 'Unknown',
            'skills': request.targetText.split(), 
            'projects': [], 
            'interests': []
        }),
        raw_text=request.targetText
    )
    
    # Generate detailed match info using LLM
    match_details = engine.generate_detailed_match(target_profile, emp, use_llm=True)
    
    resume_match = ResumeMatchResponse(
        sharedSkills=match_details['shared_skills'],
        matchingProjects=match_details['matching_projects'],
        matchingDomains=match_details['matching_domains'],
        techOverlap=match_details['tech_overlap'],
        matchingSeniority=match_details['matching_seniority'],
        reasonSummary=match_details['reason_summary']
    )
    
    return MatchDetailsResponse(
        resumeMatch=resume_match,
        collaborationSuggestions=match_details['collaboration_suggestions']
    )

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
