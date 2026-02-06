# Smart Resume Screener

AI-Powered Resume Screening and Candidate Matching System using LLMs (Ollama & Gemini API)

## Project Overview

Smart Resume Screener intelligently parses resumes, extracts skills and experience, and matches them with job descriptions using advanced Large Language Models (LLMs). The system provides semantic matching, scoring, and detailed justifications for each candidate-job pairing.

## Features

- **Resume Parsing**: Extract structured data from PDF and DOCX resumes
- **Job Description Management**: Create and manage job postings
- **AI-Powered Matching**: Semantic similarity scoring using LLMs
- **Detailed Analysis**: Get match scores (1-10) with justifications
- **Skill Gap Analysis**: Identify matched and missing skills
- **User Authentication**: Secure login and registration system
- **Dashboard**: Intuitive web interface for all operations

## Technology Stack

### Backend
- **Framework**: Python Flask
- **API**: RESTful architecture
- **Database**: SQLite3
- **Authentication**: Werkzeug password hashing

### AI/ML Components
- **Local LLM**: Ollama with Llama 3.2
- **Cloud LLM**: Google Gemini API (optional)
- **Document Processing**: PyPDF2, pdfplumber, python-docx
- **NLP**: spaCy for text analysis

### Frontend
- **HTML5/CSS3/JavaScript**: Vanilla JS (no framework)
- **Responsive Design**: Mobile-friendly interface

## Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (HTML/CSS/JS)          │
│  - Login/Register                       │
│  - Resume Upload                        │
│  - Job Description Input                │
│  - Match Results Display                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Flask Backend API               │
│  /api/login                             │
│  /api/upload-resume                     │
│  /api/job-description                   │
│  /api/match                             │
│  /api/matches/:jobId                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Resume Parser & LLM Matcher        │
│  - Extract skills, experience           │
│  - Semantic similarity analysis         │
│  - Generate match scores                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         SQLite Database                 │
│  - users                                │
│  - resumes                              │
│  - job_descriptions                     │
│  - match_results                        │
└─────────────────────────────────────────┘
```

## Installation

### Prerequisites

1. **Python 3.9+**
2. **Ollama** (for local LLM)
3. **Git** (for version control)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/smart-resume-screener.git
cd smart-resume-screener
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install and Setup Ollama

1. Download Ollama from https://ollama.ai/download
2. Install and start Ollama:

```bash
# Start Ollama server
ollama serve

# In another terminal, pull the model
ollama pull llama3.2:3b
```

### Step 5: Create Directory Structure

```bash
mkdir -p uploads database src/templates src/static
```

### Step 6: Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_PATH=database/resume_screener.db
UPLOAD_FOLDER=uploads
USE_GEMINI=False
GEMINI_API_KEY=your-gemini-api-key
OLLAMA_MODEL=llama3.2:3b
HOST=0.0.0.0
PORT=5000
```

### Step 7: Run the Application

```bash
cd src
python app.py
```

Access the application at: `http://localhost:5000`

## Usage Guide

### 1. Register/Login

- Navigate to `http://localhost:5000`
- Register a new account or login with:
  - Username: `admin`
  - Password: `admin123`

### 2. Upload Resumes

1. Click on "Upload Resume" tab
2. Select a PDF or DOCX resume file
3. Click "Upload and Parse"
4. System will extract skills, experience, and contact info

### 3. Add Job Descriptions

1. Click on "Add Job" tab
2. Fill in:
   - Job Title
   - Company Name
   - Required Skills (comma-separated)
   - Experience Required
   - Job Description
3. Click "Add Job Description"

### 4. Match Candidates

1. Click on "Match Candidates" tab
2. Select a job description from dropdown
3. Click "Start Matching"
4. Wait for AI analysis to complete

### 5. View Results

1. Click on "Results" tab
2. Select a job to view matched candidates
3. Review:
   - Match scores (1-10)
   - Justifications
   - Matched skills
   - Missing skills
   - Hiring recommendations

## LLM Prompts Used

### Matching Prompt Structure

```
Compare the following resume with the job description and provide a detailed match analysis.

JOB DETAILS:
Job Title: [title]
Required Skills: [skills]
Experience Required: [experience]
Job Description: [description]

CANDIDATE DETAILS:
Name: [name]
Skills: [skills]
Experience: [experience]

TASK:
Rate the fit between this candidate and the job on a scale of 1-10...

[Provide response in structured format with:]
- MATCH SCORE: [1-10]
- MATCHED SKILLS: [list]
- MISSING SKILLS: [list]
- JUSTIFICATION: [explanation]
- RECOMMENDATION: [Strong Hire/Consider/Pass]
```

## API Endpoints

### Authentication

- `POST /api/register` - Register new user
- `POST /api/login` - Login user
- `POST /api/logout` - Logout user

### Resume Operations

- `POST /api/upload-resume` - Upload and parse resume
- `GET /api/resumes` - Get all resumes
- `GET /api/resume/:id` - Get single resume

### Job Description Operations

- `POST /api/job-description` - Add job description
- `GET /api/jobs` - Get all jobs
- `GET /api/job/:id` - Get single job

### Matching Operations

- `POST /api/match` - Match resumes to job
- `GET /api/matches/:jobId` - Get match results for job
- `GET /api/statistics` - Get system statistics

## Database Schema

### Users Table
```sql
- id (INTEGER PRIMARY KEY)
- username (TEXT UNIQUE)
- password_hash (TEXT)
- email (TEXT)
- role (TEXT)
- created_at (TIMESTAMP)
```

### Resumes Table
```sql
- id (INTEGER PRIMARY KEY)
- candidate_name (TEXT)
- email (TEXT)
- phone (TEXT)
- file_path (TEXT)
- skills (TEXT JSON)
- experience (TEXT JSON)
- education (TEXT JSON)
- uploaded_at (TIMESTAMP)
```

### Job Descriptions Table
```sql
- id (INTEGER PRIMARY KEY)
- job_title (TEXT)
- company_name (TEXT)
- required_skills (TEXT JSON)
- experience_required (TEXT)
- job_description (TEXT)
- created_at (TIMESTAMP)
```

### Match Results Table
```sql
- id (INTEGER PRIMARY KEY)
- resume_id (INTEGER FK)
- job_id (INTEGER FK)
- match_score (REAL)
- justification (TEXT)
- matched_skills (TEXT JSON)
- missing_skills (TEXT JSON)
- created_at (TIMESTAMP)
```

## Testing

### Test LLM Connection

```python
python -c "from src.llm_matcher import LLMMatcher; matcher = LLMMatcher(); print('OK' if matcher.test_connection() else 'FAIL')"
```

### Test Resume Parser

```python
from src.resume_parser import ResumeParser
parser = ResumeParser()
result = parser.parse_resume('path/to/resume.pdf')
print(result)
```

## Troubleshooting

### Ollama Connection Failed

```bash
# Make sure Ollama is running
ollama serve

# Check if model is downloaded
ollama list

# Pull model if needed
ollama pull llama3.2:3b
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database Errors

```bash
# Delete and recreate database
rm database/resume_screener.db
python src/app.py
```

## Future Enhancements

- Multi-language support
- Advanced analytics dashboard
- Email notifications
- ATS integration
- Bulk resume upload
- Export reports to PDF
- Video interview integration
- Mobile application

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is licensed under the MIT License.

## Contact

Project Link: https://github.com/newuserAJ/smart-resume-screener

## Acknowledgments

- Ollama for local LLM capabilities
- Google Gemini for cloud AI services
- Flask community for excellent documentation
