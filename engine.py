import json
import os
from typing import List, Dict
import numpy as np
from openai import OpenAI
from models import Employee

class CollabEngine:
    def __init__(self, api_key: str = None):
        self.employees: List[Employee] = []
        # Initialize OpenAI client
        # If api_key is not passed, it will look for OPENAI_API_KEY env var
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.embeddings_matrix = None

    def load_employees(self, employees: List[Employee]):
        self.employees = employees
        self._compute_embeddings()

    def _compute_embeddings(self):
        if not self.employees:
            return
        print("Generating embeddings using OpenAI...")
        texts = []
        for emp in self.employees:
            if not emp.raw_text:
                # Construct from profile if raw_text missing
                text = f"{emp.name}, {emp.profile.role} in {emp.profile.department}. "
                text += f"Skills: {', '.join(emp.profile.skills)}. "
                
                # Handle Project objects
                if emp.profile.projects:
                    project_names = [p.name if hasattr(p, 'name') else str(p) for p in emp.profile.projects]
                    text += f"Projects: {', '.join(project_names)}. "
                
                text += f"Interests: {', '.join(emp.profile.interests)}."
                emp.raw_text = text
            texts.append(emp.raw_text)
        
        # Batch generation might be needed for large sets, but for 20-50 it's fine
        # We'll do it in one go or small batches
        try:
            response = self.client.embeddings.create(
                input=texts,
                model="text-embedding-3-small"
            )
            
            for idx, emp in enumerate(self.employees):
                emp.embedding = response.data[idx].embedding
            
            # Update embeddings_matrix for similarity calculations
            self.embeddings_matrix = np.array([emp.embedding for emp in self.employees])
            
            print(f"Generated embeddings for {len(self.employees)} employees.")
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Set empty embeddings as fallback
            for emp in self.employees:
                emp.embedding = [0.0] * 1536  # Default dimension for text-embedding-3-small
            self.embeddings_matrix = None # Ensure matrix is reset if error occurs

    def find_similar_employees(self, target_employee_id: str, top_k: int = 5) -> List[Dict]:
        if self.embeddings_matrix is None:
            return []

        # Find index of target employee
        target_idx = -1
        for idx, emp in enumerate(self.employees):
            if emp.id == target_employee_id:
                target_idx = idx
                break
        
        if target_idx == -1:
            return []

        # Compute cosine similarity
        all_embeddings = self.embeddings_matrix
        target_embedding = all_embeddings[target_idx]
        
        # Normalize
        norm_target = np.linalg.norm(target_embedding)
        all_norms = np.linalg.norm(all_embeddings, axis=1)
        dot_products = np.dot(all_embeddings, target_embedding)
        cosine_sim = dot_products / (all_norms * norm_target)
        
        # Get top_k similar indices (excluding self)
        sorted_indices = cosine_sim.argsort()[::-1]  # Sort descending
        
        recommendations = []
        target_emp = self.employees[target_idx]
        
        for idx in sorted_indices:
            if idx == target_idx:
                continue  # Skip the target employee itself
            
            if len(recommendations) >= top_k:
                break
            
            emp = self.employees[idx]
            score = cosine_sim[idx]
            
            recommendations.append({
                "employee": emp,
                "score": float(score),
                "reason": self._compute_reason(target_emp, emp)
            })
        
        return recommendations
    
    def _compute_reason(self, target_emp: Employee, candidate_emp: Employee) -> str:
        """Generates a simple reason for the match based on shared skills and projects."""
        shared_skills = list(set(target_emp.profile.skills) & set(candidate_emp.profile.skills))
        
        target_project_names = [p.name for p in target_emp.profile.projects]
        candidate_project_names = [p.name for p in candidate_emp.profile.projects]
        common_projects = list(set(target_project_names) & set(candidate_project_names))

        reason_parts = []
        if shared_skills:
            reason_parts.append(f"shared skills like {', '.join(shared_skills[:2])}")
        """Generate a basic reason for the match"""
        # Extract project names for comparison
        target_project_names = set([p.name for p in target_emp.profile.projects])
        candidate_project_names = set([p.name for p in candidate_emp.profile.projects])
        common_project_names = target_project_names & candidate_project_names
        
        common_skills = set(target_emp.profile.skills) & set(candidate_emp.profile.skills)
        
        if common_skills and common_project_names:
            return f"Shared expertise in {', '.join(list(common_skills)[:2])} and similar project experience."
        elif common_skills:
            return f"Strong alignment on {', '.join(list(common_skills)[:3])}."
        elif common_project_names:
            return f"Experience on similar projects: {', '.join(list(common_project_names)[:2])}."
        elif target_emp.profile.department == candidate_emp.profile.department:
            return f"Both working in {target_emp.profile.department}."
        else:
            return "Complementary background and diverse perspective."
    
    def generate_match_reasons(self, target_emp: Employee, recommendations: List[Dict]) -> Dict[str, str]:
        print("Generating match reasons using LLM...")
        
        # Prepare context for LLM
        target_desc = f"Target: {target_emp.name}, Role: {target_emp.profile.role}, Skills: {', '.join(target_emp.profile.skills)}, Projects: {', '.join(target_emp.profile.projects)}"
        
        candidates_desc = ""
        for rec in recommendations:
            emp = rec['employee']
            candidates_desc += f"- ID: {emp.id}, Name: {emp.name}, Role: {emp.profile.role}, Skills: {', '.join(emp.profile.skills)}, Projects: {', '.join(emp.profile.projects)}\n"
        
        prompt = f"""
        You are an expert in team building and collaboration.
        
        {target_desc}
        
        Here are the recommended connections for the target employee:
        {candidates_desc}
        
        For EACH candidate, provide a concise, specific reason (1-2 sentences) why they are a good match for the target. 
        Focus on complementary skills, shared project domains, or potential mentorship.
        
        Return the output as a valid JSON object where keys are the candidate IDs and values are the reason strings.
        Example: {{ "emp123": "Matches due to shared interest in AI...", "emp456": "Can provide mentorship in..." }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Error generating match reasons: {e}")
            return {}

    def generate_detailed_match(self, target_emp: Employee, matched_emp: Employee) -> dict:
        """Generate comprehensive match details including shared skills, projects, and LLM-powered suggestions"""
        
        # Calculate shared skills
        shared_skills = list(set(target_emp.profile.skills) & set(matched_emp.profile.skills))
        
        # Find matching project domains (simplified string matching)
        target_projects = [p.name for p in target_emp.profile.projects]
        matched_projects = [p.name for p in matched_emp.profile.projects]
        
        # Check for similar project domains
        matching_project_domains = []
        common_keywords = ['API', 'Database', 'Mobile', 'Data', 'Analytics', 'Payment', 'Migration', 'Pipeline', 'Frontend', 'Backend']
        for keyword in common_keywords:
            if any(keyword in tp for tp in target_projects) and any(keyword in mp for mp in matched_projects):
                matching_project_domains.append(keyword)
        
        # Tech overlap (shared skills that are tech-related)
        tech_keywords = ['Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'React', 'Angular', 'Vue', 
                        'SQL', 'PostgreSQL', 'MongoDB', 'Docker', 'Kubernetes', 'AWS', 'GCP', 'Kafka']
        tech_overlap = [skill for skill in shared_skills if skill in tech_keywords]
        
        # Check seniority matching
        matching_seniority = target_emp.profile.seniority == matched_emp.profile.seniority
        
        # Matching domains
        matching_domains = []
        if target_emp.profile.department == matched_emp.profile.department:
            matching_domains.append(target_emp.profile.department)
        
        # Generate LLM-powered reason summary and collaboration suggestions
        reason_summary, collab_suggestions = self._generate_llm_match_content(
            target_emp, matched_emp, shared_skills, matching_project_domains, tech_overlap
        )
        
        return {
            "shared_skills": shared_skills,
            "matching_projects": matching_project_domains,
            "matching_domains": matching_domains,
            "tech_overlap": tech_overlap,
            "matching_seniority": matching_seniority,
            "reason_summary": reason_summary,
            "collaboration_suggestions": collab_suggestions
        }
    
    def _generate_llm_match_content(self, target_emp: Employee, matched_emp: Employee, 
                                     shared_skills: list, matching_projects: list, tech_overlap: list) -> tuple:
        """Use LLM to generate reason summary and collaboration suggestions"""
        
        target_desc = f"""
Target Employee:
- Name: {target_emp.name}
- Role: {target_emp.profile.role}
- Skills: {', '.join(target_emp.profile.skills[:8])}
- Recent Projects: {', '.join([p.name for p in target_emp.profile.projects[:3]])}
"""
        
        matched_desc = f"""
Matched Employee:
- Name: {matched_emp.name}
- Role: {matched_emp.profile.role}
- Skills: {', '.join(matched_emp.profile.skills[:8])}
- Recent Projects: {', '.join([p.name for p in matched_emp.profile.projects[:3]])}
"""
        
        shared_info = f"""
Overlap:
- Shared Skills: {', '.join(shared_skills[:6]) if shared_skills else 'None'}
- Tech Stack Overlap: {', '.join(tech_overlap[:5]) if tech_overlap else 'None'}
- Matching Project Domains: {', '.join(matching_projects) if matching_projects else 'None'}
"""
        
        prompt = f"""You are an expert team collaboration advisor.

{target_desc}

{matched_desc}

{shared_info}

Generate:
1. A concise 1-2 sentence reason summary explaining why these two employees are a good match
2. Exactly 2-3 specific, actionable collaboration suggestions

Return as JSON:
{{
  "reasonSummary": "...",
  "collaborationSuggestions": ["...", "...", "..."]
}}

Focus on complementary skills, shared expertise, and concrete collaboration opportunities."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            content = json.loads(response.choices[0].message.content)
            return (
                content.get("reasonSummary", "Strong skill overlap and complementary expertise."),
                content.get("collaborationSuggestions", [
                    "Collaborate on technical initiatives leveraging shared skills.",
                    "Share best practices and knowledge in areas of expertise."
                ])[:3]  # Limit to 3
            )
        except Exception as e:
            print(f"Error generating LLM match content: {e}")
            return (
                "Strong overlap in technical skills and project experience.",
                [
                    f"Collaborate on projects involving {shared_skills[0] if shared_skills else 'common technologies'}.",
                    "Share knowledge and best practices in areas of expertise."
                ]
            )

    def generate_collaboration_summary(self, target_emp: Employee, recommendations: List[Dict]) -> str:
        print("Generating AI summary...")
        
        # Prepare context for LLM
        context = f"Target Employee: {target_emp.name} ({target_emp.profile.role})\n"
        context += f"Skills: {', '.join(target_emp.profile.skills)}\n"
        context += f"Projects: {', '.join(target_emp.profile.projects)}\n\n"
        
        context += "Recommended Connections:\n"
        for rec in recommendations:
            emp = rec['employee']
            context += f"- {emp.name} ({emp.profile.role})\n"
            context += f"  Skills: {', '.join(emp.profile.skills)}\n"
            context += f"  Projects: {', '.join(emp.profile.projects)}\n"
            context += f"  Match Score: {rec['score']:.2f}\n"
        
        prompt = f"""
        You are CollabConnect, an expert in organizational dynamics.
        Analyze the following employee and their recommended connections.
        
        {context}
        
        Produce a human-friendly collaboration summary that explains:
        1. Why these people were selected (look for deeper thematic connections beyond just keyword matches).
        2. Specific ways they can collaborate (e.g., mentoring, cross-pollination of ideas, specific tech stack alignment).
        3. Potential impact on the organization.
        
        Keep it concise, encouraging, and actionable.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", # or gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {e}"
