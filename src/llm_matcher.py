# src/llm_matcher.py
import ollama
import json
import re
from typing import Dict, List
import os

# Optional: Google Gemini API as fallback
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class LLMMatcher:
    def __init__(self, use_gemini=False, gemini_api_key=None):
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        
        if self.use_gemini and gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            print("✅ Using Google Gemini API")
        elif not use_gemini:
            # Test Ollama connection
            try:
                ollama.list()
                print("✅ Using Ollama (Local LLM)")
            except Exception as e:
                print(f"⚠️ Ollama connection failed: {e}")
                print("Make sure Ollama is running: ollama serve")
    
    def generate_llm_response(self, prompt: str, model: str = "llama3.2:3b") -> str:
        """Generate response using LLM"""
        try:
            if self.use_gemini:
                response = self.gemini_model.generate_content(prompt)
                return response.text
            else:
                # Use Ollama
                response = ollama.chat(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert HR recruiter and resume screener."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response['message']['content']
        except Exception as e:
            print(f"❌ LLM generation error: {e}")
            return None
    
    def match_resume_to_job(self, resume_data: Dict, job_data: Dict) -> Dict:
        """
        Match resume to job description and provide scoring with justification
        
        Returns:
            Dict with match_score, justification, matched_skills, missing_skills
        """
        
        # Build the matching prompt
        prompt = self._build_matching_prompt(resume_data, job_data)
        
        # Get LLM response
        llm_response = self.generate_llm_response(prompt)
        
        if not llm_response:
            return self._fallback_matching(resume_data, job_data)
        
        # Parse the LLM response
        match_result = self._parse_llm_response(llm_response, resume_data, job_data)
        
        return match_result
    
    def _build_matching_prompt(self, resume_data: Dict, job_data: Dict) -> str:
        """Build the prompt for LLM matching"""
        
        # Extract key information
        candidate_name = resume_data.get('candidate_name', 'Unknown')
        candidate_skills = resume_data.get('skills', [])
        candidate_exp = resume_data.get('experience_years', 'Not specified')
        
        job_title = job_data.get('job_title', 'Position')
        required_skills = job_data.get('required_skills', [])
        job_description = job_data.get('job_description', '')
        experience_required = job_data.get('experience_required', 'Not specified')
        
        prompt = f"""Compare the following resume with the job description and provide a detailed match analysis.

JOB DETAILS:
Job Title: {job_title}
Required Skills: {', '.join(required_skills) if isinstance(required_skills, list) else required_skills}
Experience Required: {experience_required}
Job Description: {job_description[:500]}

CANDIDATE DETAILS:
Name: {candidate_name}
Skills: {', '.join(candidate_skills[:20]) if candidate_skills else 'None specified'}
Experience: {candidate_exp}

TASK:
Rate the fit between this candidate and the job on a scale of 1-10, where:
- 1-3: Poor fit (major gaps in requirements)
- 4-6: Moderate fit (some relevant skills but significant gaps)
- 7-8: Good fit (most requirements met)
- 9-10: Excellent fit (all or nearly all requirements met with strong alignment)

Provide your response in the following format:

MATCH SCORE: [score from 1-10]

MATCHED SKILLS:
- [list skills that match between candidate and job requirements]

MISSING SKILLS:
- [list required skills that candidate doesn't have]

JUSTIFICATION:
[Provide 2-3 sentences explaining the score, highlighting strengths and gaps]

RECOMMENDATION:
[Provide a hiring recommendation: "Strong Hire", "Consider", "Maybe", or "Pass"]
"""
        
        return prompt
    
    def _parse_llm_response(self, llm_response: str, resume_data: Dict, job_data: Dict) -> Dict:
        """Parse the LLM response into structured data"""
        
        result = {
            'match_score': 5.0,
            'justification': '',
            'matched_skills': [],
            'missing_skills': [],
            'overall_assessment': '',
            'recommendation': 'Consider'
        }
        
        # Extract match score
        score_match = re.search(r'MATCH SCORE:?\s*(\d+(?:\.\d+)?)', llm_response, re.IGNORECASE)
        if score_match:
            try:
                score = float(score_match.group(1))
                result['match_score'] = min(10.0, max(1.0, score))
            except:
                pass
        
        # Extract matched skills
        matched_section = re.search(r'MATCHED SKILLS:?(.*?)(?:MISSING SKILLS:|JUSTIFICATION:|$)', 
                                   llm_response, re.IGNORECASE | re.DOTALL)
        if matched_section:
            matched_text = matched_section.group(1)
            # Extract bullet points or comma-separated items
            matched_items = re.findall(r'[-•]\s*(.+?)(?:\n|$)', matched_text)
            if not matched_items:
                matched_items = [s.strip() for s in matched_text.split(',') if s.strip()]
            result['matched_skills'] = [item.strip() for item in matched_items if item.strip()][:10]
        
        # Extract missing skills
        missing_section = re.search(r'MISSING SKILLS:?(.*?)(?:JUSTIFICATION:|RECOMMENDATION:|$)', 
                                   llm_response, re.IGNORECASE | re.DOTALL)
        if missing_section:
            missing_text = missing_section.group(1)
            missing_items = re.findall(r'[-•]\s*(.+?)(?:\n|$)', missing_text)
            if not missing_items:
                missing_items = [s.strip() for s in missing_text.split(',') if s.strip()]
            result['missing_skills'] = [item.strip() for item in missing_items if item.strip()][:10]
        
        # Extract justification
        justification_section = re.search(r'JUSTIFICATION:?(.*?)(?:RECOMMENDATION:|$)', 
                                         llm_response, re.IGNORECASE | re.DOTALL)
        if justification_section:
            result['justification'] = justification_section.group(1).strip()
        
        # Extract recommendation
        recommendation_section = re.search(r'RECOMMENDATION:?\s*(.+?)(?:\n|$)', 
                                          llm_response, re.IGNORECASE)
        if recommendation_section:
            result['recommendation'] = recommendation_section.group(1).strip()
        
        # Overall assessment
        result['overall_assessment'] = f"Match Score: {result['match_score']}/10 - {result['recommendation']}"
        
        return result
    
    def _fallback_matching(self, resume_data: Dict, job_data: Dict) -> Dict:
        """Fallback matching algorithm if LLM fails"""
        
        candidate_skills = set([s.lower() for s in resume_data.get('skills', [])])
        
        # Handle both list and string formats for required skills
        required_skills_raw = job_data.get('required_skills', [])
        if isinstance(required_skills_raw, str):
            required_skills = set([s.strip().lower() for s in required_skills_raw.split(',')])
        else:
            required_skills = set([s.lower() for s in required_skills_raw])
        
        # Calculate matches
        matched = candidate_skills.intersection(required_skills)
        missing = required_skills - candidate_skills
        
        # Calculate score
        if len(required_skills) > 0:
            match_percentage = len(matched) / len(required_skills)
            score = round(1 + (match_percentage * 9), 1)  # Scale 1-10
        else:
            score = 5.0
        
        # Generate justification
        if score >= 7:
            justification = f"Strong candidate with {len(matched)} out of {len(required_skills)} required skills."
        elif score >= 4:
            justification = f"Moderate fit with {len(matched)} matching skills, but missing {len(missing)} key requirements."
        else:
            justification = f"Limited fit with only {len(matched)} matching skills out of {len(required_skills)} required."
        
        return {
            'match_score': score,
            'justification': justification,
            'matched_skills': list(matched),
            'missing_skills': list(missing),
            'overall_assessment': f"Automated Score: {score}/10",
            'recommendation': 'Strong Hire' if score >= 8 else 'Consider' if score >= 5 else 'Pass'
        }
    
    def batch_match_resumes(self, resumes: List[Dict], job_data: Dict) -> List[Dict]:
        """
        Match multiple resumes against a single job description
        
        Returns:
            List of match results sorted by score (highest first)
        """
        results = []
        
        for resume in resumes:
            match_result = self.match_resume_to_job(resume, job_data)
            match_result['resume_id'] = resume.get('id')
            match_result['candidate_name'] = resume.get('candidate_name', 'Unknown')
            match_result['email'] = resume.get('email')
            results.append(match_result)
        
        # Sort by match score (descending)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return results
    
    def test_connection(self) -> bool:
        """Test LLM connection"""
        try:
            test_prompt = "Say 'Connection successful' if you can read this."
            response = self.generate_llm_response(test_prompt)
            return response is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

# Test function
if __name__ == "__main__":
    matcher = LLMMatcher()
    
    if matcher.test_connection():
        print("✅ LLM Matcher initialized successfully")
        
        # Test matching
        test_resume = {
            'candidate_name': 'John Doe',
            'skills': ['Python', 'Flask', 'SQL', 'Docker'],
            'experience_years': '3 years'
        }
        
        test_job = {
            'job_title': 'Backend Developer',
            'required_skills': ['Python', 'Flask', 'PostgreSQL', 'Docker', 'AWS'],
            'experience_required': '2-4 years',
            'job_description': 'Looking for a backend developer with Python and Flask experience.'
        }
        
        result = matcher.match_resume_to_job(test_resume, test_job)
        print(json.dumps(result, indent=2))
    else:
        print("❌ LLM Matcher initialization failed")