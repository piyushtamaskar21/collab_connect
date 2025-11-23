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

    def find_similar_employees_by_text(self, text: str, top_k: int = 5) -> List[Dict]:
        """Find similar employees using a raw text query (e.g., resume)."""
        if self.embeddings_matrix is None or not self.employees:
            return []

        print("Generating embedding for resume text...")
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            query_embedding = result['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

        # Compute cosine similarity
        norm_query = np.linalg.norm(query_embedding)
        all_norms = np.linalg.norm(self.embeddings_matrix, axis=1)
        
        # Avoid division by zero
        all_norms[all_norms == 0] = 1e-9
        if norm_query == 0: norm_query = 1e-9
        
        dot_products = np.dot(self.embeddings_matrix, query_embedding)
        cosine_sim = dot_products / (all_norms * norm_query)
        
        # Get top_k similar indices
        sorted_indices = cosine_sim.argsort()[::-1]
        
        recommendations = []
        
        for idx in sorted_indices:
            if len(recommendations) >= top_k:
                break
            
            emp = self.employees[idx]
            score = cosine_sim[idx]
            
            # Filter low relevance
            if score > 0.2:
                recommendations.append({
                    "employee": emp,
                    "score": float(score),
                    "reason": "" # Will be computed later
                })
        
        return recommendations

    def _is_likely_name(self, query: str) -> bool:
        """
        Heuristic to check if a query is likely a name.
        - 2-3 words, capitalized (e.g. "John Doe")
        - No common technical keywords
        """
        parts = query.split()
        if len(parts) > 3 or len(parts) < 1:
            return False
            
        # Check for common tech keywords that might look like names but aren't
        tech_keywords = {'python', 'java', 'react', 'node', 'aws', 'cloud', 'data', 'manager', 'lead', 'developer', 'engineer'}
        if any(p.lower() in tech_keywords for p in parts):
            return False
            
        # If capitalized and short, likely a name
        if all(p[0].isupper() for p in parts):
            return True
            
        return False

    def _fuzzy_match(self, term: str, text: str, threshold: float = 0.8) -> bool:
        """Check if term fuzzy matches any word in text."""
        term_lower = term.lower()
        text_lower = text.lower()
        
        if term_lower in text_lower:
            return True
            
        # Check individual words for fuzzy match
        for word in text_lower.split():
            if difflib.SequenceMatcher(None, term_lower, word).ratio() > threshold:
                return True
        return False

    def search_employees(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search employees using strict embedding similarity for non-name queries.
        """
        if not self.employees:
            return []

        # STRICT RULE: If it looks like a name, ONLY do name search
        if self._is_likely_name(query):
            print(f"Query '{query}' detected as name. Routing to name search.")
            return self.search_employees_by_name(query, top_k)

        print(f"Embedding similarity search triggered for: {query}")
        
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
            return []

        # Calculate cosine similarity if matrix exists
        if self.embeddings_matrix is None:
            print("Embeddings matrix is empty. Cannot perform search.")
            return []

        norm_query = np.linalg.norm(query_embedding)
        all_norms = np.linalg.norm(self.embeddings_matrix, axis=1)
        
        # Avoid division by zero
        all_norms[all_norms == 0] = 1e-9
        if norm_query == 0: norm_query = 1e-9
        
        dot_products = np.dot(self.embeddings_matrix, query_embedding)
        semantic_scores = dot_products / (all_norms * norm_query)

        # Collect results
        results = []
        for idx, score in enumerate(semantic_scores):
            # Filter low relevance
            if score > 0.25:
                emp = self.employees[idx]
                results.append({
                    "employee": emp,
                    "score": float(score),
                    "whyMatched": self._compute_search_reason(emp, query, [])
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        top_results = results[:top_k]
        
        if top_results:
            print(f"Top match score: {top_results[0]['score']:.4f}")
        else:
            print("No matches found above threshold.")
            
        return top_results

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
        query_lower = query.lower()
        
        # Synonyms map
        synonyms = {
            'js': 'javascript', 'ts': 'typescript', 'py': 'python', 
            'ml': 'machine learning', 'ai': 'artificial intelligence',
            'fe': 'frontend', 'be': 'backend'
        }
        
        # Expand query with synonyms
        query_terms = query_lower.split()
        expanded_terms = set(query_terms)
        for term in query_terms:
            if term in synonyms:
                expanded_terms.add(synonyms[term])
        
        # Check for skill matches (fuzzy)
        matched_skills = []
        for skill in emp.profile.skills:
            skill_lower = skill.lower()
            if any(self._fuzzy_match(term, skill_lower) for term in expanded_terms):
                matched_skills.append(skill)
        
        if matched_skills:
            reasons.append(f"Matches skill{'s' if len(matched_skills)>1 else ''}: {', '.join(matched_skills[:3])}.")
            
        # Check for tool matches (fuzzy)
        matched_tools = []
        for tool in emp.profile.tools:
            tool_lower = tool.lower()
            if any(self._fuzzy_match(term, tool_lower) for term in expanded_terms):
                matched_tools.append(tool)
                
        if matched_tools:
            reasons.append(f"Experience with tool{'s' if len(matched_tools)>1 else ''}: {', '.join(matched_tools[:3])}.")
            
        # Check for project matches
        matched_projects = [p.name for p in emp.profile.projects if any(term in p.name.lower() or term in p.description.lower() for term in expanded_terms)]
        if matched_projects:
            reasons.append(f"Worked on relevant project: {matched_projects[0]}.")
            
        # Check for role/title match
        if any(term in emp.profile.role.lower() for term in expanded_terms):
            reasons.append(f"Current role is {emp.profile.role}.")
            
        # Fallback if no specific matches found but score was high (likely semantic)
        if not reasons:
            reasons.append("Profile content is semantically similar to your search.")
            
        return list(set(reasons))[:3] # Deduplicate and limit
    
    def _compute_reason(self, target_emp: Employee, candidate_emp: Employee) -> str:
        """Generates a simple, deterministic reason for the match based on shared skills and projects."""
        
        # 1. Shared Skills
        shared_skills = list(set(target_emp.profile.skills) & set(candidate_emp.profile.skills))
        
        # 2. Project Overlap (Fuzzy)
        target_projects = [p.name.lower() for p in target_emp.profile.projects]
        candidate_projects = [p.name.lower() for p in candidate_emp.profile.projects]
        
        common_projects = []
        for tp in target_projects:
            for cp in candidate_projects:
                if self._fuzzy_match(tp, cp, threshold=0.85): # High threshold for project names
                    common_projects.append(cp.title()) # Capitalize for display
                    
        # 3. Domain Categories
        domains = {
            'Backend': ['python', 'java', 'go', 'rust', 'api', 'database', 'sql'],
            'Frontend': ['react', 'vue', 'angular', 'javascript', 'typescript', 'css'],
            'Data': ['sql', 'python', 'pandas', 'spark', 'kafka', 'etl'],
            'Mobile': ['ios', 'android', 'swift', 'kotlin', 'react native']
        }
        
        shared_domains = []
        for domain, keywords in domains.items():
            t_has = any(k in ' '.join(target_emp.profile.skills).lower() for k in keywords)
            c_has = any(k in ' '.join(candidate_emp.profile.skills).lower() for k in keywords)
            if t_has and c_has:
                shared_domains.append(domain)

        # Generate Sentence
        if common_projects:
            return f"Shared experience on similar projects like {common_projects[0]}."
        elif len(shared_skills) >= 2:
            return f"Strong alignment on {', '.join(shared_skills[:3])}."
        elif shared_domains:
            return f"Both have expertise in {shared_domains[0]} development."
        elif target_emp.profile.department == candidate_emp.profile.department:
            return f"Colleagues in the {target_emp.profile.department} department."
        else:
            return "Complementary technical background and skills."
    
    def generate_match_reasons(self, target_emp: Employee, recommendations: List[Dict]) -> Dict[str, str]:
        print("Generating match reasons using LLM...")
        
        # Prepare context for LLM as JSON
        target_data = {
            "name": target_emp.name,
            "role": target_emp.profile.role,
            "skills": target_emp.profile.skills,
            "projects": [p.name for p in target_emp.profile.projects]
        }
        
        candidates_data = []
        for rec in recommendations:
            emp = rec['employee']
            candidates_data.append({
                "id": emp.id,
                "name": emp.name,
                "role": emp.profile.role,
                "skills": emp.profile.skills,
                "projects": [p.name for p in emp.profile.projects]
            })
            
        prompt = f"""
        You are an expert in team building. Analyze the following data:
        
        TARGET: {json.dumps(target_data)}
        
        CANDIDATES: {json.dumps(candidates_data)}
        
        For EACH candidate, provide a concise reason (1 sentence) why they match the target.
        
        STRICT OUTPUT RULES:
        1. Return ONLY valid JSON.
        2. Format: {{ "candidate_id": "Reason string..." }}
        3. Do NOT invent skills or projects. Use only provided data.
        4. Be specific: Mention exact shared skills or project domains. Avoid generic "good match" phrases.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5, # Lower temperature for consistency
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error generating match reasons: {e}")
            return {}

    def generate_detailed_match(self, target_emp: Employee, matched_emp: Employee, use_llm: bool = True) -> dict:
        """Generate comprehensive match details including shared skills, projects, and LLM-powered suggestions"""
        
        # Calculate shared skills
        shared_skills = list(set(target_emp.profile.skills) & set(matched_emp.profile.skills))
        
        # Find matching project domains (simplified string matching)
        target_projects = [p.name for p in target_emp.profile.projects]
        matched_projects = [p.name for p in matched_emp.profile.projects]
        
        # Check for similar project domains
        matching_project_domains = []
        common_keywords = ['API', 'Database', 'Mobile', 'Data', 'Analytics', 'Payment', 'Migration', 'Pipeline', 'Frontend', 'Backend', 'Cloud', 'Security', 'DevOps']
        for keyword in common_keywords:
            if any(keyword.lower() in tp.lower() for tp in target_projects) and any(keyword.lower() in mp.lower() for mp in matched_projects):
                matching_project_domains.append(keyword)
        
        # Tech overlap (shared skills that are tech-related)
        tech_keywords = ['Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'React', 'Angular', 'Vue', 
                        'SQL', 'PostgreSQL', 'MongoDB', 'Docker', 'Kubernetes', 'AWS', 'GCP', 'Kafka', 'Redis', 'Elasticsearch', 'Terraform']
        tech_overlap = [skill for skill in shared_skills if skill in tech_keywords]
        
        # Check seniority matching
        seniority_levels = {'Junior': 1, 'Mid': 2, 'Senior': 3, 'Lead': 4, 'Staff': 5, 'Principal': 6}
        t_level = seniority_levels.get(target_emp.profile.seniority, 0)
        m_level = seniority_levels.get(matched_emp.profile.seniority, 0)
        matching_seniority = abs(t_level - m_level) <= 1 # Match if within 1 level
        
        # Matching domains
        matching_domains = []
        if target_emp.profile.department == matched_emp.profile.department:
            matching_domains.append(target_emp.profile.department)
        
        # Generate reason summary and collaboration suggestions
        if use_llm:
            reason_summary, collab_suggestions = self._generate_llm_match_content(
                target_emp, matched_emp, shared_skills, matching_project_domains, tech_overlap
            )
        else:
            # Heuristic fallback
            reason_summary = self._compute_reason(target_emp, matched_emp)
            collab_suggestions = []
            if shared_skills:
                collab_suggestions.append(f"Collaborate on tasks involving {shared_skills[0]}.")
            if matching_project_domains:
                collab_suggestions.append(f"Share knowledge on {matching_project_domains[0]} projects.")
            if not collab_suggestions:
                collab_suggestions.append("Connect to discuss shared professional interests.")
        
        return {
            "shared_skills": shared_skills,
            "matching_projects": matching_project_domains,
            "matching_domains": matching_domains,
            "tech_overlap": tech_overlap,
            "matching_seniority": matching_seniority,
            "reason_summary": reason_summary,
            "collaboration_suggestions": collab_suggestions
        }
    
    def parse_profile_from_text(self, text: str) -> Dict:
        """
        Uses LLM to parse raw text (resume or typed background) into a structured profile.
        Extracts: Role, Seniority, Skills, Projects, Department.
        """
        print("Parsing profile from text...")
        
        prompt = f"""
        Analyze the following professional background text and extract structured data.
        
        TEXT:
        "{text[:4000]}"  # Truncate to avoid token limits
        
        EXTRACT THE FOLLOWING IN STRICT JSON FORMAT:
        {{
            "role": "Inferred Job Title (e.g. Senior Backend Engineer)",
            "seniority": "Junior|Mid|Senior|Staff|Principal",
            "department": "Engineering|Product|Data|Design|Sales|Marketing",
            "skills": ["skill1", "skill2", ...],
            "projects": [
                {{
                    "name": "Project Name (or inferred summary)",
                    "description": "Brief description of what was built/achieved",
                    "tech": ["tech1", "tech2"]
                }}
            ]
        }}
        
        Rules:
        - If specific details are missing, infer reasonable defaults or use "Unknown".
        - Extract at least 3-5 skills if possible.
        - Extract at least 1 project if mentioned.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1, # Low temp for extraction
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing profile: {e}")
            # Return safe default
            return {
                "role": "Unknown",
                "seniority": "Unknown",
                "department": "Engineering",
                "skills": [],
                "projects": []
            }

    def _generate_llm_match_content(
        self,
        target_emp: Employee,
        matched_emp: Employee,
        shared_skills: list,
        matching_projects: list,
        tech_overlap: list
    ) -> tuple:
        """Use LLM to generate reason summary and collaboration suggestions 
        using strict JSON prompts + anti-hallucination rules.
        """

        # ---- CONTEXT EXTRACTION HELPERS ----
        def extract_patterns(skills: List[str], projects: List[object]) -> Dict[str, List[str]]:
            patterns = {
                "architecture": [],
                "tooling": []
            }
            
            arch_keywords = {
                "Microservices": ["microservice", "distributed"],
                "Serverless": ["lambda", "serverless", "cloud functions"],
                "Event-Driven": ["kafka", "rabbitmq", "event", "pub/sub"],
                "REST/GraphQL": ["rest", "graphql", "api"],
                "Data Pipelines": ["etl", "pipeline", "airflow", "spark"]
            }
            
            tool_keywords = {
                "Containerization": ["docker", "kubernetes", "k8s", "container"],
                "CI/CD": ["jenkins", "github actions", "gitlab ci", "circleci"],
                "IaC": ["terraform", "ansible", "cloudformation"],
                "Observability": ["prometheus", "grafana", "datadog", "new relic"],
                "Cloud": ["aws", "gcp", "azure"]
            }
            
            # Check skills and project descriptions
            text_corpus = " ".join(skills).lower() + " " + " ".join([p.name + " " + getattr(p, "description", "") for p in projects]).lower()
            
            for cat, kws in arch_keywords.items():
                if any(kw in text_corpus for kw in kws):
                    patterns["architecture"].append(cat)
                    
            for cat, kws in tool_keywords.items():
                if any(kw in text_corpus for kw in kws):
                    patterns["tooling"].append(cat)
            
            return patterns

        target_patterns = extract_patterns(target_emp.profile.skills, target_emp.profile.projects)
        match_patterns = extract_patterns(matched_emp.profile.skills, matched_emp.profile.projects)
        
        shared_arch = list(set(target_patterns["architecture"]) & set(match_patterns["architecture"]))
        shared_tooling = list(set(target_patterns["tooling"]) & set(match_patterns["tooling"]))

        # ---- PREPARE STRUCTURED JSON INPUT FOR THE LLM ----
        def project_to_dict(p):
            return {
                "name": p.name,
                "description": getattr(p, "description", ""),
                "tech": getattr(p, "tech", [])
            }

        target_json = {
            "name": target_emp.name,
            "role": target_emp.profile.role,
            "skills": target_emp.profile.skills[:15], # Increased limit
            "projects": [project_to_dict(p) for p in target_emp.profile.projects],
            "department": target_emp.profile.department,
            "seniority": target_emp.profile.seniority,
        }

        match_json = {
            "name": matched_emp.name,
            "role": matched_emp.profile.role,
            "skills": matched_emp.profile.skills[:15],
            "projects": [project_to_dict(p) for p in matched_emp.profile.projects],
            "department": matched_emp.profile.department,
            "seniority": matched_emp.profile.seniority,
        }

        overlap_json = {
            "sharedSkills": shared_skills,
            "sharedTech": tech_overlap,
            "projectDomainOverlap": matching_projects,
            "architecturePatterns": shared_arch,
            "toolingOverlap": shared_tooling,
            "matchingSeniority": target_emp.profile.seniority == matched_emp.profile.seniority,
        }

        full_payload = {
            "target": target_json,
            "match": match_json,
            "overlap": overlap_json
        }

        # ---- TALENT NAVIGATOR PROMPT ----
        prompt = f"""
You are Talent Navigator, an expert in engineering collaboration, technical synergy analysis, and organizational development.

You will receive STRICT structured JSON with real project descriptions, tech stacks, and overlap information.  
You MUST use only the provided fields. No assumptions. No invented skills or projects.

Your job:
1. Produce a highly specific 1–2 sentence match reason.
2. Produce 2–3 deeply actionable collaboration ideas tied directly to shared engineering context.

Forbidden:
- generic statements (“Both have frontend expertise”)
- vague suggestions (“discuss shared interests”)
- invented data

Required output format:
{{
  "reasonSummary": "...",
  "collaborationSuggestions": ["...", "...", "..."]
}}

Here is your input JSON:
```json
{json.dumps(full_payload, indent=2)}
"""
        # ---- CALL THE MODEL ----
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,              # Low temperature for strictness
                    response_mime_type="application/json"
                )
            )

            content = response.text.strip()
            parsed = json.loads(content)

            reason_summary = parsed.get("reasonSummary", "")
            collab_suggestions = parsed.get("collaborationSuggestions", [])

            # ---- VALIDATION LOGIC ----
            is_valid = True
            if not reason_summary or len(reason_summary) < 10:
                is_valid = False
            
            forbidden_phrases = ["both have expertise", "discuss shared interests", "similar areas", "good match"]
            if any(phrase in reason_summary.lower() for phrase in forbidden_phrases):
                print(f"LLM returned generic reason: '{reason_summary}'. Triggering fallback.")
                is_valid = False

            if not is_valid:
                raise ValueError("Generated content failed validation checks.")

            return reason_summary, collab_suggestions[:3]

        except Exception as e:
            print(f"[ERROR] generate_llm_match_content failed or rejected: {e}")

            # ---- DETERMINISTIC FALLBACK ----
            # Build a specific reason from the extracted data
            if shared_arch:
                fallback_reason = f"Both engineers work with {shared_arch[0]} architectures, creating a strong foundation for technical collaboration."
            elif matching_projects:
                fallback_reason = f"Shared experience in {matching_projects[0]} domains suggests high potential for knowledge exchange."
            elif tech_overlap:
                fallback_reason = f"Strong technical alignment on {', '.join(tech_overlap[:3])} enables immediate collaboration on codebases."
            else:
                fallback_reason = "Complementary skill sets with potential for cross-functional collaboration."

            fallback_collab = []
            if shared_arch:
                fallback_collab.append(f"Co-design systems using {shared_arch[0]} patterns.")
            if tech_overlap:
                fallback_collab.append(f"Pair program on complex {tech_overlap[0]} modules.")
            if matching_projects:
                fallback_collab.append(f"Share insights on {matching_projects[0]} challenges.")
            
            # Fill remaining suggestions
            if len(fallback_collab) < 2:
                fallback_collab.append("Conduct code reviews to share best practices.")
                fallback_collab.append("Discuss architectural trade-offs in recent projects.")

            return fallback_reason, fallback_collab[:3]

    
    def generate_collaboration_summary(self, target_emp: Employee, recommendations: List[Dict]) -> str:
        print("Generating AI summary...")
        
        # Prepare context as JSON
        context = {
            "target": {
                "name": target_emp.name,
                "role": target_emp.profile.role,
                "skills": target_emp.profile.skills,
                "projects": [p.name for p in target_emp.profile.projects]
            },
            "recommendations": []
        }
        
        for rec in recommendations:
            emp = rec['employee']
            context["recommendations"].append({
                "name": emp.name,
                "role": emp.profile.role,
                "skills": emp.profile.skills[:5],
                "match_score": f"{rec['score']:.2f}",
                "reason": rec.get('summary', 'Matched based on skills and experience')
            })
        
        prompt = f"""
        You are Talent Navigator, an expert in organizational dynamics.
        
        Analyze the following match data:
        {json.dumps(context, indent=2)}
        
        Produce a concise, high-value collaboration summary that includes:
        
        1. **Why these individuals were selected**: Highlight deeper thematic connections (shared tech, complementary strengths).
        2. **Specific collaboration opportunities**: Provide 2-3 actionable suggestions (mentorship, joint projects).
        3. **Potential organizational impact**: How these connections reduce silos or accelerate delivery.
        
        Style Requirements:
        - Professional, clear, and encouraging.
        - 3-5 short paragraphs.
        - Do NOT reveal scoring algorithms.
        - Output raw text (Markdown supported).
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
