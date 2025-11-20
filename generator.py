import random
from faker import Faker
from models import Employee, Profile, Project

fake = Faker()

ROLES = [
    "Software Engineer", "Senior Software Engineer", "Staff Engineer",
    "Backend Engineer", "Frontend Engineer", "Full Stack Engineer",
    "DevOps Engineer", "Data Engineer", "ML Engineer",
    "Engineering Manager", "Product Manager", "Tech Lead",
    "Designer", "UX Researcher", "QA Engineer"
]

SENIORITY_LEVELS = ["Junior", "Mid-level", "Senior", "Staff", "Principal"]
DEPARTMENTS = ["Engineering", "Product", "Design", "Data", "Platform Engineering", "Infrastructure"]
LOCATIONS = ["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Remote", "Berlin, Germany", "London, UK", "Toronto, Canada"]

TECH_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++",
    "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
    "SQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
    "Kafka", "RabbitMQ", "GraphQL", "REST API", "gRPC",
    "Machine Learning", "TensorFlow", "PyTorch", "Scikit-learn",
    "Git", "CI/CD", "Jenkins", "GitHub Actions", "Microservices"
]

TOOLS = [
    "VSCode", "IntelliJ", "Vim", "Jira", "Confluence", "Slack",
    "Figma", "Sketch", "Datadog", "Grafana", "Prometheus",
    "Postman", "Jupyter", "Tableau"
]

PROJECT_TEMPLATES = [
    {"name": "Payment Gateway Modernization", "desc": "Migrated legacy payment system to microservices architecture, reducing latency by 40%", "tech_pool": ["Java", "Kubernetes", "Kafka", "PostgreSQL"]},
    {"name": "Real-time Analytics Dashboard", "desc": "Built scalable analytics platform processing 10M events/day", "tech_pool": ["Python", "Kafka", "Elasticsearch", "React"]},
    {"name": "Mobile App Redesign", "desc": "Led complete redesign of iOS/Android apps, increasing user engagement by 35%", "tech_pool": ["React Native", "TypeScript", "GraphQL"]},
    {"name": "Database Sharding Initiative", "desc": "Implemented horizontal sharding to support 10x traffic growth", "tech_pool": ["PostgreSQL", "Python", "Redis"]},
    {"name": "CI/CD Pipeline Automation", "desc": "Automated deployment pipeline, reducing release time from 2 days to 2 hours", "tech_pool": ["Docker", "Kubernetes", "Jenkins", "Terraform"]},
    {"name": "ML-powered Recommendation Engine", "desc": "Developed personalized recommendations using collaborative filtering", "tech_pool": ["Python", "TensorFlow", "Kubernetes", "PostgreSQL"]},
    {"name": "API Rate Limiting Service", "desc": "Built distributed rate limiting service handling 100K requests/sec", "tech_pool": ["Go", "Redis", "Kubernetes"]},
    {"name": "Data Pipeline Optimization", "desc": "Optimized ETL pipelines, reducing processing time by 60%", "tech_pool": ["Python", "Apache Spark", "Airflow", "AWS"]},
    {"name": "Frontend Component Library", "desc": "Created reusable component library used across 15+ products", "tech_pool": ["React", "TypeScript", "Storybook"]},
    {"name": "Security Audit Platform", "desc": "Built automated security scanning and vulnerability reporting system", "tech_pool": ["Python", "Docker", "PostgreSQL"]},
]

PROFESSIONAL_SUMMARIES = [
    "{role} with {years} years of experience in {domain}. Passionate about building scalable systems and mentoring junior engineers.",
    "Experienced {role} specializing in {domain}. Strong background in distributed systems and cloud infrastructure.",
    "{role} focused on {domain}. Known for delivering high-quality code and driving technical excellence.",
    "Senior {role} with expertise in {domain}. Led multiple cross-functional teams to successful product launches.",
    "{role} passionate about {domain}. Combines technical depth with strong communication skills."
]

def generate_synthetic_data(count: int = 20) -> list[Employee]:
    employees = []
    
    for i in range(count):
        # Basic info
        name = fake.name()
        role = random.choice(ROLES)
        seniority = random.choice(SENIORITY_LEVELS)
        department = random.choice(DEPARTMENTS)
        location = random.choice(LOCATIONS)
        email = f"{name.lower().replace(' ', '.')}.{random.randint(1, 999)}@company.com"
        
        # Manager (pick from common manager names)
        managers = ["Sarah Thompson", "Michael Chen", "Emily Rodriguez", "David Park", "Lisa Johnson"]
        manager = random.choice(managers)
        
        # Experience
        experience_years = random.randint(2, 15)
        
        # Skills
        num_skills = random.randint(6, 12)
        skills = random.sample(TECH_SKILLS, num_skills)
        primary_skills = skills[:4]
        secondary_skills = skills[4:8] if len(skills) > 4 else []
        
        # Tools
        tools = random.sample(TOOLS, random.randint(3, 6))
        
        # Interests
        interests = random.sample([
            "Open Source", "AI/ML", "Cloud Architecture", "DevOps",
            "Frontend Development", "Backend Systems", "Data Engineering",
            "Security", "Performance Optimization", "API Design"
        ], k=random.randint(2, 4))
        
        # Projects (2-4 per employee)
        num_projects = random.randint(2, 4)
        project_samples = random.sample(PROJECT_TEMPLATES, num_projects)
        projects = []
        for proj_template in project_samples:
            # Randomize tech stack from the pool
            num_tech = min(random.randint(2, 4), len(proj_template["tech_pool"]))
            tech_stack = random.sample(proj_template["tech_pool"], num_tech)
            projects.append(Project(
                name=proj_template["name"],
                description=proj_template["desc"],
                tech=tech_stack
            ))
        
        # Professional summary
        domain_map = {
            "Backend Engineer": "backend development and API design",
            "Frontend Engineer": "modern frontend frameworks and UI/UX",
            "Full Stack Engineer": "end-to-end web application development",
            "DevOps Engineer": "infrastructure automation and cloud deployment",
            "Data Engineer": "data pipeline development and analytics",
            "ML Engineer": "machine learning and predictive modeling",
        }
        domain = domain_map.get(role, "software development and system design")
        summary_template = random.choice(PROFESSIONAL_SUMMARIES)
        professional_summary = summary_template.format(
            role=role,
            years=experience_years,
            domain=domain
        )
        
        # Create raw text for embedding
        raw_text = f"{name} is a {role} with {experience_years} years of experience. "
        raw_text += f"Expert in {', '.join(primary_skills[:3])}. "
        raw_text += f"Recently worked on: {', '.join([p.name for p in projects])}. "
        raw_text += professional_summary
        
        # Create profile
        profile = Profile(
            role=role,
            seniority=seniority,
            department=department,
            location=location,
            manager=manager,
            experience_years=experience_years,
            professional_summary=professional_summary,
            skills=skills,
            primary_skills=primary_skills,
            secondary_skills=secondary_skills,
            tools=tools,
            projects=projects,
            interests=interests
        )
        
        # Create employee
        employee = Employee(
            id=f"emp{i+1:03d}",
            name=name,
            email=email,
            profile=profile,
            raw_text=raw_text
        )
        
        employees.append(employee)
    
    return employees
