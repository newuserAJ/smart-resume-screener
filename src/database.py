# src/database.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class Database:
    def __init__(self, db_path='database/resume_screener.db'):
        self.db_path = db_path
        self.create_tables()
    
    def get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_tables(self):
        """Create necessary database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Resumes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                file_path TEXT NOT NULL,
                raw_text TEXT,
                skills TEXT,
                experience TEXT,
                education TEXT,
                parsed_data TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by INTEGER,
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        ''')
        
        # Job Descriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company_name TEXT,
                required_skills TEXT NOT NULL,
                experience_required TEXT,
                education_required TEXT,
                job_description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Match Results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                match_score REAL NOT NULL,
                justification TEXT,
                matched_skills TEXT,
                missing_skills TEXT,
                overall_assessment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id),
                FOREIGN KEY (job_id) REFERENCES job_descriptions(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # User operations
    def create_user(self, username: str, password_hash: str, email: str = None, role: str = 'user'):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, email, role))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    # Resume operations
    def save_resume(self, resume_data: Dict, user_id: int = None) -> int:
        """Save parsed resume to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO resumes (
                candidate_name, email, phone, file_path, raw_text,
                skills, experience, education, parsed_data, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            resume_data.get('candidate_name'),
            resume_data.get('email'),
            resume_data.get('phone'),
            resume_data.get('file_path'),
            resume_data.get('raw_text'),
            json.dumps(resume_data.get('skills', [])),
            json.dumps(resume_data.get('experience', [])),
            json.dumps(resume_data.get('education', [])),
            json.dumps(resume_data.get('parsed_data', {})),
            user_id
        ))
        
        conn.commit()
        resume_id = cursor.lastrowid
        conn.close()
        return resume_id
    
    def get_resume(self, resume_id: int) -> Optional[Dict]:
        """Get resume by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM resumes WHERE id = ?', (resume_id,))
        resume = cursor.fetchone()
        conn.close()
        
        if resume:
            resume_dict = dict(resume)
            # Parse JSON fields
            resume_dict['skills'] = json.loads(resume_dict['skills']) if resume_dict['skills'] else []
            resume_dict['experience'] = json.loads(resume_dict['experience']) if resume_dict['experience'] else []
            resume_dict['education'] = json.loads(resume_dict['education']) if resume_dict['education'] else []
            return resume_dict
        return None
    
    def get_all_resumes(self, limit: int = 100) -> List[Dict]:
        """Get all resumes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM resumes ORDER BY uploaded_at DESC LIMIT ?', (limit,))
        resumes = cursor.fetchall()
        conn.close()
        
        result = []
        for resume in resumes:
            resume_dict = dict(resume)
            resume_dict['skills'] = json.loads(resume_dict['skills']) if resume_dict['skills'] else []
            result.append(resume_dict)
        return result
    
    # Job Description operations
    def save_job_description(self, job_data: Dict, user_id: int = None) -> int:
        """Save job description to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO job_descriptions (
                job_title, company_name, required_skills, experience_required,
                education_required, job_description, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_data.get('job_title'),
            job_data.get('company_name'),
            json.dumps(job_data.get('required_skills', [])),
            job_data.get('experience_required'),
            job_data.get('education_required'),
            job_data.get('job_description'),
            user_id
        ))
        
        conn.commit()
        job_id = cursor.lastrowid
        conn.close()
        return job_id
    
    def get_job_description(self, job_id: int) -> Optional[Dict]:
        """Get job description by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM job_descriptions WHERE id = ?', (job_id,))
        job = cursor.fetchone()
        conn.close()
        
        if job:
            job_dict = dict(job)
            job_dict['required_skills'] = json.loads(job_dict['required_skills']) if job_dict['required_skills'] else []
            return job_dict
        return None
    
    def get_all_jobs(self, limit: int = 50) -> List[Dict]:
        """Get all job descriptions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM job_descriptions ORDER BY created_at DESC LIMIT ?', (limit,))
        jobs = cursor.fetchall()
        conn.close()
        
        result = []
        for job in jobs:
            job_dict = dict(job)
            job_dict['required_skills'] = json.loads(job_dict['required_skills']) if job_dict['required_skills'] else []
            result.append(job_dict)
        return result
    
    # Match Results operations
    def save_match_result(self, match_data: Dict) -> int:
        """Save matching result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO match_results (
                resume_id, job_id, match_score, justification,
                matched_skills, missing_skills, overall_assessment
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_data.get('resume_id'),
            match_data.get('job_id'),
            match_data.get('match_score'),
            match_data.get('justification'),
            json.dumps(match_data.get('matched_skills', [])),
            json.dumps(match_data.get('missing_skills', [])),
            match_data.get('overall_assessment')
        ))
        
        conn.commit()
        match_id = cursor.lastrowid
        conn.close()
        return match_id
    
    def get_matches_for_job(self, job_id: int) -> List[Dict]:
        """Get all match results for a specific job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT mr.*, r.candidate_name, r.email, r.phone
            FROM match_results mr
            JOIN resumes r ON mr.resume_id = r.id
            WHERE mr.job_id = ?
            ORDER BY mr.match_score DESC
        ''', (job_id,))
        matches = cursor.fetchall()
        conn.close()
        
        result = []
        for match in matches:
            match_dict = dict(match)
            match_dict['matched_skills'] = json.loads(match_dict['matched_skills']) if match_dict['matched_skills'] else []
            match_dict['missing_skills'] = json.loads(match_dict['missing_skills']) if match_dict['missing_skills'] else []
            result.append(match_dict)
        return result
    
    def get_match_statistics(self) -> Dict:
        """Get overall statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total resumes
        cursor.execute('SELECT COUNT(*) as count FROM resumes')
        stats['total_resumes'] = cursor.fetchone()['count']
        
        # Total jobs
        cursor.execute('SELECT COUNT(*) as count FROM job_descriptions')
        stats['total_jobs'] = cursor.fetchone()['count']
        
        # Total matches
        cursor.execute('SELECT COUNT(*) as count FROM match_results')
        stats['total_matches'] = cursor.fetchone()['count']
        
        # Average match score
        cursor.execute('SELECT AVG(match_score) as avg_score FROM match_results')
        avg = cursor.fetchone()['avg_score']
        stats['average_match_score'] = round(avg, 2) if avg else 0
        
        conn.close()
        return stats