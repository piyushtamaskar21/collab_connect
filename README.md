# CollabConnect

**AI-Powered Employee Collaboration Recommendation System**

CollabConnect is an intelligent platform that helps employees discover the best colleagues to collaborate with based on their skills, experience, and project history. By analyzing resumes and comparing them against an internal employee database, the system provides personalized recommendations with AI-generated insights.

---

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Project Purpose](#project-purpose)
- [Architecture](#architecture)
- [Features](#features)
- [How It Works](#how-it-works)
- [API Documentation](#api-documentation)
- [Setup Instructions](#setup-instructions)
- [Technology Stack](#technology-stack)
- [Future Enhancements](#future-enhancements)

---

## 🎯 Problem Statement

In large organizations, employees often struggle to:
- **Discover colleagues** with complementary skills for collaboration
- **Find mentors** or team members with specific expertise
- **Identify cross-functional partners** for projects
- **Break down silos** between departments and teams

Traditional employee directories provide basic information but lack intelligent matching and contextual recommendations.

---

## 💡 Project Purpose

CollabConnect solves this by:

1. **Analyzing Skills & Experience**: Extracting meaningful data from resumes and employee profiles
2. **Semantic Matching**: Using AI embeddings to find deep connections beyond keyword matching
3. **Personalized Recommendations**: Providing tailored suggestions with specific collaboration ideas
4. **Detailed Insights**: Explaining *why* each person is recommended and *how* to collaborate

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Resume       │  │ Employee     │  │ Profile Modal    │  │
│  │ Uploader     │  │ Cards        │  │ (Detailed View)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ API Server   │→ │ CollabEngine │→ │ Data Generator   │  │
│  │ (server.py)  │  │ (engine.py)  │  │ (generator.py)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   LLM Agent (OpenAI GPT-4)                   │
│  • Generate embeddings for semantic search                   │
│  • Create match explanations                                 │
│  • Suggest collaboration opportunities                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User uploads resume** → PDF parsed in browser (pdfjs-dist)
2. **Text sent to backend** → `/api/recommend` endpoint
3. **Embedding generation** → OpenAI creates vector representation
4. **Similarity search** → Cosine similarity against employee database
5. **LLM analysis** → GPT-4 generates match reasons & collaboration ideas
6. **Response returned** → Detailed employee profiles with insights
7. **Frontend displays** → Cards with "Read More" for full details

---

## ✨ Features

### Completed Features

#### 1. **Resume Upload & PDF Parsing**
- Drag-and-drop file upload interface
- Client-side PDF text extraction using `pdfjs-dist`
- Support for multi-page PDF documents
- Real-time processing feedback

#### 2. **Employee Recommendation Cards**
- **Match Score**: Percentage-based compatibility rating
- **Short Explanation**: AI-generated 1-2 sentence summary
- **Shared Skills Highlighting**: Blue badges for overlapping skills
- **Colorful Accents**: Left border colors for visual distinction
- **Action Buttons**: Message, Read More, Connect

#### 3. **Detailed Profile Modal**
Opens when clicking "Read More" on any card:

**Left Column:**
- Years of experience
- Manager name
- Professional summary
- Primary & secondary skills (with shared highlighting)
- Tools & technologies

**Right Column:**
- Current projects with descriptions
- Detailed match explanation
- Shared skills breakdown
- Tech stack overlap
- Seniority alignment
- AI-generated collaboration suggestions

**UX Features:**
- Smooth fade-in/slide-up animations
- ESC key to close
- Click outside to close
- Scrollable content
- Responsive design (2-column desktop, 1-column mobile)

#### 4. **AI-Powered Insights**
- **Match Reason Summaries**: Specific explanations for each recommendation
- **Collaboration Suggestions**: 2-3 actionable ideas per match
- **Resume Comparison**: Automatic identification of shared skills and projects

---

## 🔧 How It Works

### Resume Upload + PDF Parsing

```typescript
// Frontend: ResumeUploader.tsx
1. User drops PDF file or clicks to browse
2. pdfjs-dist library loads the PDF
3. Text extracted page-by-page
4. Combined text sent to backend API
```

**Key Implementation:**
```typescript
const extractText = async (file: File) => {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let fullText = '';
    
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map(item => item.str).join(' ');
        fullText += pageText + ' ';
    }
    
    onTextExtracted(fullText);
};
```

### Employee Recommendation Engine

```python
# Backend: engine.py
1. Create temporary employee profile from resume text
2. Generate embedding using OpenAI text-embedding-3-small
3. Compute cosine similarity against all employees
4. Rank by similarity score
5. Return top 5 matches
```

**Similarity Scoring:**
```python
# Cosine Similarity Formula
similarity = (A · B) / (||A|| × ||B||)

# Where:
# A = Resume embedding vector
# B = Employee profile embedding vector
# Result: 0.0 (no match) to 1.0 (perfect match)
```

### Resume Comparison Logic

```python
# engine.py: generate_detailed_match()
1. Extract skills from both profiles
2. Find intersection (shared skills)
3. Compare project domains
4. Identify tech stack overlap
5. Check seniority alignment
6. Generate LLM-powered summary
```

**Example Match Analysis:**
```json
{
  "sharedSkills": ["Python", "Docker", "Kubernetes"],
  "matchingProjects": ["Backend Engineering", "Infrastructure"],
  "techOverlap": ["Python", "AWS", "PostgreSQL"],
  "matchingSeniority": true,
  "reasonSummary": "Strong backend alignment with shared expertise in containerization and cloud infrastructure."
}
```

### LLM Agent Integration

**Two Main LLM Calls:**

1. **Match Reason Generation** (`_generate_llm_match_content`):
```python
# Input to GPT-4
{
  "target_employee": {
    "name": "...",
    "role": "...",
    "skills": [...],
    "projects": [...]
  },
  "matched_employee": {...},
  "overlap": {
    "shared_skills": [...],
    "tech_overlap": [...]
  }
}

# Output from GPT-4
{
  "reasonSummary": "1-2 sentence explanation",
  "collaborationSuggestions": [
    "Specific suggestion 1",
    "Specific suggestion 2",
    "Specific suggestion 3"
  ]
}
```

2. **Embedding Generation**:
- Model: `text-embedding-3-small`
- Dimension: 1536
- Input: Combined text from profile (role, skills, projects, summary)
- Output: Vector representation for semantic search

---

## 📡 API Documentation

### POST `/api/recommend`

**Description:** Get employee recommendations based on resume text

**Request:**
```json
{
  "resumeText": "string (extracted from PDF)"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "id": "emp001",
      "name": "Rebecca Taylor",
      "title": "Backend Engineer",
      "department": "Platform Engineering",
      "location": "Berlin, Germany",
      "email": "rebecca.taylor@company.com",
      "manager": "Sarah Thompson",
      "experienceYears": 6,
      "professionalSummary": "Backend engineer with strong experience...",
      "skills": ["Java", "Python", "Kubernetes", "SQL"],
      "primarySkills": ["Java", "Kubernetes"],
      "secondarySkills": ["Python", "SQL"],
      "tools": ["IntelliJ", "Docker", "Grafana"],
      "projects": [
        {
          "name": "Payment Gateway Modernization",
          "description": "Migrated legacy payment system...",
          "tech": ["Java", "Kubernetes", "Kafka"]
        }
      ],
      "matchScore": 0.78,
      "summary": "Strong backend alignment and similar distributed system exposure.",
      "avatarUrl": "https://ui-avatars.com/api/?name=Rebecca+Taylor&background=random",
      "resumeMatch": {
        "sharedSkills": ["Java", "Python"],
        "matchingProjects": ["Backend Engineering"],
        "matchingDomains": ["Engineering"],
        "techOverlap": ["Java", "SQL"],
        "matchingSeniority": true,
        "reasonSummary": "Extensive backend skills align with your experience..."
      },
      "collaborationSuggestions": [
        "Collaborate on distributed system scaling tasks.",
        "Pair on backend migration work due to shared Java/K8s skills."
      ]
    }
  ]
}
```

---

## 🚀 Setup Instructions

### Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **OpenAI API Key**

### Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd collab_connect
```

#### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
EOF
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
```

### Running Locally

#### Start Backend Server
```bash
# From project root
python3 server.py
```
Server runs on: `http://localhost:8000`

#### Start Frontend Development Server
```bash
# From frontend directory
npm run dev
```
Frontend runs on: `http://localhost:5173`

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings & LLM | Yes |

---

## 🧪 Synthetic Data for POC

For this proof-of-concept, we generate **30 synthetic employees** with realistic profiles:

**Generated Data Includes:**
- Names (via Faker library)
- Roles: Backend Engineer, Frontend Engineer, Data Engineer, etc.
- Departments: Engineering, Product, Design, Data, Infrastructure
- Locations: San Francisco, New York, Berlin, London, Remote
- 6-12 skills per employee
- 2-4 projects with descriptions and tech stacks
- Professional summaries
- Manager names
- Experience years (2-15)

**Data Generation:**
```python
# generator.py
employees = generate_synthetic_data(count=30)
# Creates rich, realistic employee profiles
```

**Why Synthetic Data?**
- No privacy concerns
- Consistent testing
- Easy to regenerate
- Demonstrates full functionality

---

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **TailwindCSS** for styling
- **pdfjs-dist** for PDF parsing
- **Lucide React** for icons

### Backend
- **FastAPI** for REST API
- **Python 3.9+**
- **NumPy** for vector operations
- **OpenAI SDK** for embeddings & LLM
- **Faker** for synthetic data
- **python-dotenv** for environment management

### AI/ML
- **OpenAI GPT-4** for text generation
- **text-embedding-3-small** for embeddings
- **Cosine Similarity** for matching

---

## 🔮 Future Enhancements

### Short-term
- [ ] **Real Resume Parsing**: Extract structured data (education, work history, certifications)
- [ ] **Filtering & Sorting**: Filter by department, location, skills; sort by relevance
- [ ] **Save Connections**: Track who you've connected with
- [ ] **Email Integration**: Send connection requests via email
- [ ] **User Authentication**: Login system for personalized experience

### Medium-term
- [ ] **Advanced Search**: Full-text search across employee profiles
- [ ] **Team Recommendations**: Suggest entire teams for projects
- [ ] **Skill Gap Analysis**: Identify missing skills for project requirements
- [ ] **Analytics Dashboard**: Track collaboration patterns and success rates
- [ ] **Slack/Teams Integration**: Connect directly from chat platforms

### Long-term
- [ ] **Real-time Updates**: Live employee status and availability
- [ ] **Project Matching**: Match employees to open projects
- [ ] **Learning Paths**: Recommend courses based on skill gaps
- [ ] **Network Graph**: Visualize collaboration networks
- [ ] **Sentiment Analysis**: Analyze collaboration feedback

---

## 📝 Project Structure

```
collab_connect/
├── backend/
│   ├── server.py           # FastAPI server & endpoints
│   ├── engine.py           # Recommendation engine & LLM integration
│   ├── generator.py        # Synthetic data generation
│   ├── models.py           # Data models (Employee, Profile, etc.)
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EmployeeCard.tsx          # Recommendation card
│   │   │   ├── EmployeeProfileModal.tsx  # Detailed view modal
│   │   │   ├── RecommendationsGrid.tsx   # Card grid layout
│   │   │   ├── ResumeUploader.tsx        # PDF upload component
│   │   │   └── SkillChip.tsx             # Skill badge component
│   │   ├── App.tsx          # Main application
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Global styles
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
│
├── .env                     # Environment variables (not in git)
└── README.md               # This file
```

---

## 🤝 Contributing

This is a proof-of-concept project. For production use, consider:
- Adding comprehensive error handling
- Implementing rate limiting
- Adding request validation
- Setting up proper logging
- Creating unit and integration tests
- Implementing caching for embeddings
- Adding database persistence

---

## 📄 License

This project is for demonstration purposes.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 and embedding models
- **Mozilla** for pdf.js library
- **FastAPI** team for the excellent framework
- **React** and **Vite** communities

---

**Built with ❤️ to break down organizational silos and foster collaboration**
