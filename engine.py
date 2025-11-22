import json
import os
from typing import List, Dict
import numpy as np
import difflib
import google.generativeai as genai
from models import Employee

class CollabEngine:
    def __init__(self, api_key: str = None):
        self.employees: List[Employee] = []
        # Initialize Gemini client
        if api_key:
            genai.configure(api_key=api_key)
        elif os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
        self.embeddings_matrix = None

    def load_employees(self, employees: List[Employee]):
        self.employees = employees
        self._compute_embeddings()

    def _compute_embeddings(self):
        if not self.employees:
            return
        print("Generating embeddings using Gemini...")
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
        # Batch generation might be needed for large sets, but for 20-50 it's fine
        # We'll do it in one go or small batches
        try:
            # Gemini embedding model
            # Using 'models/text-embedding-004'
            
            for idx, emp in enumerate(self.employees):
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=emp.raw_text,
                    task_type="retrieval_document",
                    title="Employee Profile"
                )
                emp.embedding = result['embedding']
            
            # Update embeddings_matrix for similarity calculations
            self.embeddings_matrix = np.array([emp.embedding for emp in self.employees])
            
            print(f"Generated embeddings for {len(self.employees)} employees.")
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Set empty embeddings as fallback
            for emp in self.employees:
                emp.embedding = [0.0] * 768  # Default dimension for text-embedding-004 is 768
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

    def search_employees(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search employees using a hybrid approach:
        - Keyword matching (exact and partial)
        - Semantic search (embedding similarity)
        """
        if not self.employees:
            return []

        print(f"Searching for: {query}")
        
        # 1. Compute Embedding Similarity
        try:
            query_embedding_result = genai.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = query_embedding_result['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            query_embedding = [0.0] * 768

        # Calculate cosine similarity if matrix exists
        semantic_scores = np.zeros(len(self.employees))
        if self.embeddings_matrix is not None:
            norm_query = np.linalg.norm(query_embedding)
            all_norms = np.linalg.norm(self.embeddings_matrix, axis=1)
            # Avoid division by zero
            all_norms[all_norms == 0] = 1e-9
            if norm_query == 0: norm_query = 1e-9
            
            dot_products = np.dot(self.embeddings_matrix, query_embedding)
            semantic_scores = dot_products / (all_norms * norm_query)

        # 2. Compute Keyword Scores
        query_terms = query.lower().split()
        keyword_scores = np.zeros(len(self.employees))
        
        results = []
        for idx, emp in enumerate(self.employees):
            # Prepare text for keyword search
            # We search in skills, tools, domain knowledge (if any), projects, title
            searchable_text = f"{emp.name} {emp.profile.role} {emp.profile.department} "
            searchable_text += " ".join(emp.profile.skills) + " "
            searchable_text += " ".join(emp.profile.tools) + " "
            searchable_text += " ".join([p.name for p in emp.profile.projects]) + " "
            searchable_text += " ".join([p.description for p in emp.profile.projects])
            
            searchable_text_lower = searchable_text.lower()
            
            # Calculate keyword score
            k_score = 0.0
            matched_terms = []
            
            # Exact phrase match bonus
            if query.lower() in searchable_text_lower:
                k_score += 0.4
            
            # Term matching
            for term in query_terms:
                if term in searchable_text_lower:
                    k_score += 0.2
                    matched_terms.append(term)
            
            keyword_scores[idx] = min(k_score, 0.6) # Cap keyword contribution
            
            # 3. Combined Score
            # Weights: Keyword (0.4) + Partial/Fuzzy (0.2 - handled in keyword) + Embedding (0.4)
            # We'll just sum them with weights
            final_score = (keyword_scores[idx] * 0.6) + (semantic_scores[idx] * 0.4)
            
            # Normalize to 0-1 range roughly, though it might exceed 1 slightly with bonuses
            # Let's clip it
            final_score = min(final_score, 1.0)
            
            if final_score > 0.1: # Threshold to filter noise
                results.append({
                    "employee": emp,
                    "score": float(final_score),
                    "whyMatched": self._compute_search_reason(emp, query, matched_terms)
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]

    def search_employees_by_name(self, name_query: str, top_k: int = 10) -> List[Dict]:
        """
        Search employees by name using fuzzy matching.
        """
        if not self.employees:
            return []

        print(f"Searching for name: {name_query}")
        
        results = []
        query_lower = name_query.lower()
        
        for emp in self.employees:
            score = 0.0
            reasons = []
            
            name_lower = emp.name.lower()
            email_lower = emp.email.lower()
            
            # 1. Exact match (highest score)
            if query_lower == name_lower:
                score = 1.0
                reasons.append(f"Exact name match: {emp.name}")
            
            # 2. Substring match
            elif query_lower in name_lower:
                score = 0.8
                reasons.append(f"Name contains '{name_query}'")
            
            # 3. Fuzzy match using SequenceMatcher
            else:
                # Check similarity ratio
                matcher = difflib.SequenceMatcher(None, query_lower, name_lower)
                similarity = matcher.ratio()
                
                # Check partial ratio (if query is a part of the name but with typos)
                # We can simulate partial ratio by checking if the matching block is significant
                match = matcher.find_longest_match(0, len(query_lower), 0, len(name_lower))
                if match.size > 2: # At least 3 chars match
                    # Boost score if the matched block is a significant portion of the query
                    if match.size / len(query_lower) > 0.7:
                        similarity = max(similarity, 0.7)
                
                if similarity > 0.6: # Threshold for fuzzy match
                    score = similarity * 0.9 # Penalty for being fuzzy
                    reasons.append(f"Similar name to '{name_query}'")
            
            # 4. Email prefix match
            if score < 1.0:
                email_prefix = email_lower.split('@')[0]
                if query_lower == email_prefix:
                    score = max(score, 0.9)
                    reasons.append(f"Matches email prefix: {emp.email}")
                elif query_lower in email_prefix:
                    score = max(score, 0.7)
                    reasons.append(f"Matches part of email: {emp.email}")

            if score > 0.4:
                results.append({
                    "employee": emp,
                    "score": float(score),
                    "whyMatched": reasons
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]

    def _compute_search_reason(self, emp: Employee, query: str, matched_terms: List[str]) -> List[str]:
        """Generate reasons why this employee matched the search query."""
        reasons = []
        
        # Check for skill matches
        query_lower = query.lower()
        matched_skills = [s for s in emp.profile.skills if s.lower() in query_lower]
        if matched_skills:
            reasons.append(f"Matches skill{'s' if len(matched_skills)>1 else ''}: {', '.join(matched_skills[:3])}.")
            
        # Check for tool matches
        matched_tools = [t for t in emp.profile.tools if t.lower() in query_lower]
        if matched_tools:
            reasons.append(f"Experience with tool{'s' if len(matched_tools)>1 else ''}: {', '.join(matched_tools[:3])}.")
            
        # Check for project matches
        matched_projects = [p.name for p in emp.profile.projects if query_lower in p.name.lower() or query_lower in p.description.lower()]
        if matched_projects:
            reasons.append(f"Worked on relevant project: {matched_projects[0]}.")
            
        # Check for role/title match
        if query_lower in emp.profile.role.lower():
            reasons.append(f"Current role is {emp.profile.role}.")
            
        # Fallback if no specific matches found but score was high (likely semantic)
        if not reasons:
            reasons.append("Profile content is semantically similar to your search.")
            
        return reasons[:3]
    
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
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            content = response.text
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
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            content = json.loads(response.text)
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
        You are Talent Navigator, an expert in organizational dynamics, collaboration design, and cross-team alignment.

        Your purpose is to transform structured match data — including similarity scores, shared skills, project overlap, domain alignment, and keyword-based search results — into clear, motivational, and actionable human-readable insights.

        You will be given a data package in the variable {{context}}, which may include:
        - The target employee’s background
        - A list of recommended or matched colleagues
        - Match percentages or search relevance scores
        - "Why recommended" or "why matched" explanations
        - Extracted skill and project overlaps
        - Collaboration opportunity metadata

        Using this data, produce a concise but high-value collaboration summary that includes:

        1. Why these individuals were selected:
           - Highlight deeper thematic connections such as shared technical focus areas, complementary strengths, parallel project histories, or domain alignment.
           - Interpret the relevance rather than restating raw data.

        2. Specific collaboration opportunities:
           - Provide 2–4 actionable suggestions (mentorship, joint projects, cross-functional knowledge sharing, combining complementary skills, or accelerating work in shared areas).

        3. Potential organizational impact:
           - Describe how these connections can reduce silos, accelerate delivery, strengthen cross-team workflows, expand knowledge sharing, or drive innovation.

        Style Requirements:
        - Professional, clear, and friendly.
        - Action-oriented and encouraging.
        - No speculative personal attributes.
        - 3–5 short paragraphs.
        - Do not reveal any underlying scoring algorithms or system logic.

        Now analyze the following data and produce the collaboration summary:

        {context}
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            return f"Error generating summary: {e}"
