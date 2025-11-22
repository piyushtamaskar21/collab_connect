# CollabConnect

**AI-Powered Employee Collaboration Recommendation System**

CollabConnect is an intelligent platform that helps employees discover the best colleagues to collaborate with based on their skills, experience, and project history. By analyzing resumes and comparing them against an internal employee database, the system provides personalized recommendations with AI-generated insights.

---

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Project Purpose](#project-purpose)
- [Architecture](#architecture)
- [Features](#features)
- [How It Works (For Everyone)](#how-it-works-for-everyone)
- [How It Works (Technical)](#how-it-works-technical)
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
│  │ Unified      │  │ Employee     │  │ Profile Modal    │  │
│  │ Input Box    │  │ Cards        │  │ (Detailed View)  │  │
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
│               LLM Agent (Google Gemini 1.5 Pro)              │
│  • Generate embeddings for semantic search                   │
│  • Create match explanations                                 │
│  • Suggest collaboration opportunities                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Resume upload OR search query
2. **Intent Detection** → Frontend determines mode (Resume, Keyword Search, Name Search)
3. **Backend Processing** → `/api/recommend` endpoint
4. **Embedding/Search** → Gemini creates vector representation or performs fuzzy search
5. **Similarity/Matching** → Cosine similarity or fuzzy string matching
6. **LLM Analysis** → Gemini 1.5 Pro generates match reasons & collaboration ideas
7. **Response Returned** → Detailed employee profiles with insights
8. **Frontend Displays** → Cards with "Read More" for full details

---

## ✨ Features

### Completed Features

#### 1. **Unified Smart Input**
- **Resume Analysis**: Upload a PDF/DOCX or paste resume text to find colleagues with complementary skills.
- **Keyword Search**: Type queries like "Find Python experts" or "Who knows React?" to find specific skills.
- **Name Search**: Search for colleagues by name (e.g., "Joshua Hart") with fuzzy matching support (finds "Josh Hart").

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

#### 4. **AI-Powered Insights**
- **Match Reason Summaries**: Specific explanations for each recommendation
- **Collaboration Suggestions**: 2-3 actionable ideas per match
- **Resume Comparison**: Automatic identification of shared skills and projects

---

## 🧠 How It Works (For Everyone)

Curious about what happens when you click "Analyze"? Here is the non-technical breakdown:

### 1. The "Reading" Phase (Ingestion)
Imagine a super-fast reader who can read a resume in milliseconds. When you upload a file or type a search query, CollabConnect "reads" it to understand **who you are** (if it's a resume) or **what you are looking for** (if it's a search). It identifies key information like skills, job titles, and project experience.

### 2. The "Understanding" Phase (AI Analysis)
This is where the magic happens. We use **Google Gemini**, a powerful Artificial Intelligence, to understand the *meaning* behind the words.
- It knows that "React" and "Frontend" are related.
- It understands that a "Data Scientist" and a "Machine Learning Engineer" might work well together.
- It converts your profile into a mathematical "fingerprint" (called an embedding) that represents your professional identity.

### 3. The "Matching" Phase (Connection)
CollabConnect then compares your "fingerprint" against every other employee in the database. It looks for:
- **Similarities**: People who do what you do (good for mentorship or sharing knowledge).
- **Complementary Skills**: People who have skills you need (e.g., a Backend Engineer matching with a Frontend Engineer).
- **Name Matches**: If you searched for a name, it looks for close matches, even if you made a typo (like "Josh" instead of "Joshua").

### 4. The "Explanation" Phase (Insights)
Finally, the system doesn't just give you a list of names. It acts like a helpful colleague introducing you. It writes a personalized summary explaining **why** it picked these people and **how** you could collaborate (e.g., "You both know Python, but she specializes in AI—you could learn a lot from her!").

---

## 🔧 How It Works (Technical)

### Resume Upload + PDF Parsing

```typescript
// Frontend: ResumeUploader.tsx
1. User drops PDF file or clicks to browse
2. pdfjs-dist library loads the PDF
3. Text extracted page-by-page
4. Combined text sent to backend API
```

### Employee Recommendation Engine

```python
# Backend: engine.py
1. Create temporary employee profile from resume text
2. Generate embedding using Gemini text-embedding-004
3. Compute cosine similarity against all employees
4. Rank by similarity score
5. Return top 5 matches
```

### Similarity Scoring
```python
# Cosine Similarity Formula
similarity = (A · B) / (||A|| × ||B||)

# Where:
# A = Resume embedding vector
# B = Employee profile embedding vector
# Result: 0.0 (no match) to 1.0 (perfect match)
```

### LLM Agent Integration

**Two Main LLM Calls (Google Gemini 1.5 Pro):**

1. **Match Reason Generation** (`_generate_llm_match_content`):
```python
# Input to Gemini
{
  "target_employee": {...},
  "matched_employee": {...},
  "overlap": {...}
}

# Output from Gemini
{
  "reasonSummary": "1-2 sentence explanation",
  "collaborationSuggestions": ["Suggestion 1", "Suggestion 2"]
}
```

2. **Embedding Generation**:
- Model: `text-embedding-004`
- Dimension: 768
- Input: Combined text from profile (role, skills, projects, summary)
- Output: Vector representation for semantic search

---

## 📡 API Documentation

### POST `/api/recommend`

**Description:** Get employee recommendations based on resume text or search query.

**Request (Resume Mode):**
```json
{
  "resumeText": "string (extracted from PDF)",
  "mode": "resume"
}
```

**Request (Search Mode):**
```json
{
  "searchQuery": "Find Python experts",
  "mode": "search"
}
```

**Request (Name Search Mode):**
```json
{
  "searchQuery": "Joshua Hart",
  "mode": "name_search"
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
      "matchScore": 0.78,
      "summary": "Strong backend alignment...",
      "whyMatched": ["Matches skill: Python"],
      "collaborationSuggestions": ["Collaborate on distributed systems..."]
      // ... other fields
    }
  ]
}
```

---

## 🚀 Setup Instructions

### Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **Google Gemini API Key**

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
GEMINI_API_KEY=your_gemini_api_key_here
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
| `GEMINI_API_KEY` | Google Gemini API key for embeddings & LLM | Yes |

---

## 🧪 Synthetic Data for POC

For this proof-of-concept, we generate **30 synthetic employees** with realistic profiles using the `Faker` library. This ensures privacy and provides consistent testing data.

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
- **Google Generative AI SDK** for embeddings & LLM
- **Faker** for synthetic data
- **python-dotenv** for environment management

### AI/ML
- **Google Gemini 1.5 Pro** for text generation
- **text-embedding-004** for embeddings
- **Cosine Similarity** & **Fuzzy Matching** for matching

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
│   │   │   ├── ResumeUploader.tsx        # Unified input component
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

- **Google** for Gemini 1.5 Pro and embedding models
- **Mozilla** for pdf.js library
- **FastAPI** team for the excellent framework
- **React** and **Vite** communities

---

**Built with ❤️ to break down organizational silos and foster collaboration**
