# src/app.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime

from database import Database
from resume_parser import ResumeParser
from llm_matcher import LLMMatcher

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('database', exist_ok=True)

# Initialize components
db = Database()
resume_parser = ResumeParser()
llm_matcher = LLMMatcher()  # Use Ollama by default

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return render_template('dashboard.html', username=session.get('username'))
    return render_template('login.html')

@app.route('/database')
@login_required
def database_dashboard():
    """Database Dashboard page"""
    return render_template('database_dashboard.html', username=session.get('username'))

# ==================== AUTH ROUTES ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Hash password
    password_hash = generate_password_hash(password)
    
    # Create user
    user_id = db.create_user(username, password_hash, email)
    
    if user_id:
        return jsonify({'message': 'Registration successful', 'user_id': user_id}), 201
    else:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Get user
    user = db.get_user_by_username(username)
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

# ==================== RESUME ROUTES ====================

@app.route('/api/upload-resume', methods=['POST'])
@login_required
def upload_resume():
    """Upload and parse resume"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF and DOCX allowed'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse resume
        parsed_data = resume_parser.parse_resume(filepath)
        
        # Save to database
        resume_id = db.save_resume(parsed_data, session.get('user_id'))
        parsed_data['id'] = resume_id
        
        return jsonify({
            'message': 'Resume uploaded and parsed successfully',
            'resume_id': resume_id,
            'data': {
                'candidate_name': parsed_data.get('candidate_name'),
                'email': parsed_data.get('email'),
                'phone': parsed_data.get('phone'),
                'skills': parsed_data.get('skills', []),
                'experience_years': parsed_data.get('experience_years'),
                'total_skills': len(parsed_data.get('skills', []))
            }
        }), 201
        
    except Exception as e:
        print(f"Error uploading resume: {str(e)}")
        return jsonify({'error': f'Failed to process resume: {str(e)}'}), 500

@app.route('/api/resumes', methods=['GET'])
@login_required
def get_resumes():
    """Get all resumes - only from current user's session"""
    try:
        user_id = session.get('user_id')
        
        # Get only resumes uploaded by current user
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM resumes 
            WHERE uploaded_by = ? 
            ORDER BY uploaded_at DESC 
            LIMIT 100
        ''', (user_id,))
        resumes = cursor.fetchall()
        conn.close()
        
        result = []
        for resume in resumes:
            resume_dict = dict(resume)
            resume_dict['skills'] = json.loads(resume_dict['skills']) if resume_dict['skills'] else []
            resume_dict['experience'] = json.loads(resume_dict['experience']) if resume_dict['experience'] else []
            resume_dict['education'] = json.loads(resume_dict['education']) if resume_dict['education'] else []
            result.append(resume_dict)
        
        # Check if request is from database dashboard (expects plain array)
        if request.args.get('format') == 'simple':
            simplified_resumes = []
            for resume in result:
                simplified_resumes.append({
                    'id': resume['id'],
                    'candidate_name': resume['candidate_name'] or 'N/A',
                    'email': resume['email'] or 'N/A',
                    'phone': resume['phone'] or 'N/A',
                    'skills': resume['skills'][:10] if resume['skills'] else [],
                    'uploaded_at': resume['uploaded_at']
                })
            return jsonify(simplified_resumes), 200
        
        # Original format for main dashboard
        simplified_resumes = []
        for resume in result:
            simplified_resumes.append({
                'id': resume['id'],
                'candidate_name': resume['candidate_name'],
                'email': resume['email'],
                'phone': resume['phone'],
                'skills': resume['skills'][:10] if resume['skills'] else [],
                'uploaded_at': resume['uploaded_at']
            })
        
        return jsonify({'resumes': simplified_resumes}), 200
        
    except Exception as e:
        print(f"Error fetching resumes: {str(e)}")
        return jsonify({'error': f'Failed to fetch resumes: {str(e)}'}), 500

@app.route('/api/resume/<int:resume_id>', methods=['GET'])
@login_required
def get_resume(resume_id):
    """Get single resume details"""
    try:
        resume = db.get_resume(resume_id)
        
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        return jsonify({'resume': resume}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch resume: {str(e)}'}), 500

@app.route('/api/resume/<int:resume_id>', methods=['DELETE'])
@login_required
def delete_resume(resume_id):
    """Delete a resume"""
    try:
        resume = db.get_resume(resume_id)
        
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Delete from database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM resumes WHERE id = ?', (resume_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Resume deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete resume: {str(e)}'}), 500

# ==================== JOB DESCRIPTION ROUTES ====================

@app.route('/api/job-description', methods=['POST'])
@login_required
def add_job_description():
    """Add new job description"""
    data = request.get_json()
    
    job_title = data.get('job_title')
    company_name = data.get('company_name', '')
    required_skills = data.get('required_skills', [])
    experience_required = data.get('experience_required', '')
    education_required = data.get('education_required', '')
    job_description = data.get('job_description', '')
    
    if not job_title or not job_description:
        return jsonify({'error': 'Job title and description are required'}), 400
    
    try:
        job_data = {
            'job_title': job_title,
            'company_name': company_name,
            'required_skills': required_skills if isinstance(required_skills, list) else required_skills.split(','),
            'experience_required': experience_required,
            'education_required': education_required,
            'job_description': job_description
        }
        
        job_id = db.save_job_description(job_data, session.get('user_id'))
        
        return jsonify({
            'message': 'Job description added successfully',
            'job_id': job_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to add job description: {str(e)}'}), 500

@app.route('/api/jobs', methods=['GET'])
@login_required
def get_jobs():
    """Get all job descriptions"""
    try:
        jobs = db.get_all_jobs()
        
        # Check if request is from database dashboard (expects plain array)
        if request.args.get('format') == 'simple':
            simplified_jobs = []
            for job in jobs:
                simplified_jobs.append({
                    'id': job['id'],
                    'job_title': job['job_title'],
                    'company_name': job['company_name'] or 'N/A',
                    'required_skills': job['required_skills'][:10] if job['required_skills'] else [],
                    'experience_required': job['experience_required'] or 'N/A',
                    'created_at': job['created_at']
                })
            return jsonify(simplified_jobs), 200
        
        # Original format for main dashboard
        return jsonify({'jobs': jobs}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch jobs: {str(e)}'}), 500

@app.route('/api/job/<int:job_id>', methods=['GET'])
@login_required
def get_job(job_id):
    """Get single job description"""
    try:
        job = db.get_job_description(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({'job': job}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch job: {str(e)}'}), 500

@app.route('/api/job/<int:job_id>', methods=['DELETE'])
@login_required
def delete_job(job_id):
    """Delete a job description"""
    try:
        job = db.get_job_description(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Delete from database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM job_descriptions WHERE id = ?', (job_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Job deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete job: {str(e)}'}), 500

# ==================== MATCHING ROUTES ====================

@app.route('/api/match', methods=['POST'])
@login_required
def match_candidates():
    """Match resumes with job description"""
    data = request.get_json()
    
    job_id = data.get('job_id')
    resume_ids = data.get('resume_ids', [])  # Optional: specific resumes
    
    if not job_id:
        return jsonify({'error': 'Job ID required'}), 400
    
    try:
        # Get job description
        job = db.get_job_description(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Get resumes to match
        if resume_ids:
            resumes = [db.get_resume(rid) for rid in resume_ids]
            resumes = [r for r in resumes if r]  # Filter None values
        else:
            resumes = db.get_all_resumes()
        
        if not resumes:
            return jsonify({'error': 'No resumes found'}), 404
        
        # Perform matching
        match_results = llm_matcher.batch_match_resumes(resumes, job)
        
        # Save match results to database
        for match in match_results:
            match_data = {
                'resume_id': match['resume_id'],
                'job_id': job_id,
                'match_score': match['match_score'],
                'justification': match['justification'],
                'matched_skills': match['matched_skills'],
                'missing_skills': match['missing_skills'],
                'overall_assessment': match['overall_assessment']
            }
            db.save_match_result(match_data)
        
        return jsonify({
            'message': 'Matching completed successfully',
            'total_candidates': len(match_results),
            'results': match_results
        }), 200
        
    except Exception as e:
        print(f"Matching error: {str(e)}")
        return jsonify({'error': f'Matching failed: {str(e)}'}), 500

@app.route('/api/matches/<int:job_id>', methods=['GET'])
@login_required
def get_matches(job_id):
    """Get match results for a job"""
    try:
        matches = db.get_matches_for_job(job_id)
        return jsonify({'matches': matches}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch matches: {str(e)}'}), 500

@app.route('/api/matches', methods=['GET'])
@login_required
def get_all_matches():
    """Get all match results"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT mr.*, r.candidate_name, r.email, r.phone
            FROM match_results mr
            JOIN resumes r ON mr.resume_id = r.id
            ORDER BY mr.created_at DESC
            LIMIT 100
        ''')
        matches = cursor.fetchall()
        conn.close()
        
        result = []
        for match in matches:
            match_dict = dict(match)
            match_dict['matched_skills'] = json.loads(match_dict['matched_skills']) if match_dict['matched_skills'] else []
            match_dict['missing_skills'] = json.loads(match_dict['missing_skills']) if match_dict['missing_skills'] else []
            result.append(match_dict)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch matches: {str(e)}'}), 500

# ==================== STATISTICS ROUTES ====================

@app.route('/api/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get overall statistics"""
    try:
        stats = db.get_match_statistics()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch statistics: {str(e)}'}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("Starting Smart Resume Screener...")
    print("Make sure Ollama is running: ollama serve")
    print("\nAvailable routes:")
    print("- Login: http://localhost:5000/")
    print("- Database Dashboard: http://localhost:5000/database")
    app.run(debug=True, host='0.0.0.0', port=5000)