# src/resume_parser.py
import PyPDF2
import pdfplumber
import docx
import re
from typing import Dict, List
import json

class ResumeParser:
    def __init__(self):
        self.common_skills = [
            # Programming Languages
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin',
            'go', 'rust', 'typescript', 'scala', 'r', 'matlab', 'perl',
            
            # Web Technologies
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django',
            'flask', 'spring boot', 'asp.net', 'jquery', 'bootstrap', 'tailwind',
            
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite',
            'cassandra', 'dynamodb', 'firebase',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github',
            'gitlab', 'ci/cd', 'terraform', 'ansible',
            
            # Data Science & ML
            'machine learning', 'deep learning', 'ai', 'data science', 'tensorflow',
            'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'nlp',
            
            # Mobile Development
            'android', 'ios', 'react native', 'flutter', 'xamarin',
            
            # Other Tools & Frameworks
            'linux', 'unix', 'agile', 'scrum', 'jira', 'rest api', 'graphql',
            'microservices', 'oauth', 'jwt', 'websocket'
        ]
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            # Try pdfplumber first (better formatting)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e2:
                print(f"PyPDF2 also failed: {e2}")
                raise Exception("Failed to extract text from PDF")
        
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
            raise Exception("Failed to extract text from DOCX")
    
    def extract_contact_info(self, text: str) -> Dict:
        """Extract contact information from text"""
        contact_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['email'] = emails[0] if emails else None
        
        # Extract phone (multiple formats)
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\d{10}',  # 10 digit number
            r'\+?\d{2}[-.\s]?\d{10}'  # International format
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                contact_info['phone'] = phones[0]
                break
        
        if 'phone' not in contact_info:
            contact_info['phone'] = None
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text.lower())
        contact_info['linkedin'] = f"https://{linkedin[0]}" if linkedin else None
        
        # Extract GitHub
        github_pattern = r'github\.com/[\w-]+'
        github = re.findall(github_pattern, text.lower())
        contact_info['github'] = f"https://{github[0]}" if github else None
        
        # Extract name (heuristic: first line or first few words)
        lines = text.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            # Skip lines with email or phone
            if '@' in line or re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', line):
                continue
            # Check if line looks like a name (2-4 words, mostly alphabetic)
            words = line.split()
            if 2 <= len(words) <= 4 and all(word.replace('.', '').isalpha() for word in words):
                contact_info['name'] = line
                break
        
        if 'name' not in contact_info:
            contact_info['name'] = "Unknown"
        
        return contact_info
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        text_lower = text.lower()
        found_skills = []
        
        # Search for skills in text
        for skill in self.common_skills:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill.title())
        
        # Remove duplicates and sort
        found_skills = sorted(list(set(found_skills)))
        
        return found_skills
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience from text"""
        experiences = []
        
        # Look for experience section
        exp_pattern = r'(work experience|experience|employment|professional experience)(.*?)(education|skills|projects|certifications|$)'
        match = re.search(exp_pattern, text.lower(), re.DOTALL)
        
        if match:
            exp_section = match.group(2)
            
            # Split by common delimiters
            exp_entries = re.split(r'\n\s*\n', exp_section)
            
            for entry in exp_entries:
                entry = entry.strip()
                if len(entry) > 20:  # Filter out very short entries
                    # Try to extract company, role, duration
                    exp_dict = {
                        'description': entry[:200],  # First 200 chars
                        'full_text': entry
                    }
                    experiences.append(exp_dict)
        
        return experiences[:5]  # Return top 5 experiences
    
    def extract_education(self, text: str) -> List[Dict]:
        """Extract education information from text"""
        education = []
        
        # Look for education section
        edu_pattern = r'(education|academic|qualifications)(.*?)(experience|skills|projects|certifications|$)'
        match = re.search(edu_pattern, text.lower(), re.DOTALL)
        
        if match:
            edu_section = match.group(2)
            
            # Common degree patterns
            degree_patterns = [
                r'(bachelor|master|phd|diploma|b\.?tech|m\.?tech|b\.?e|m\.?e|b\.?s|m\.?s|b\.?a|m\.?a)',
                r'(undergraduate|graduate|post[- ]graduate)'
            ]
            
            edu_entries = re.split(r'\n\s*\n', edu_section)
            
            for entry in edu_entries:
                entry = entry.strip()
                # Check if entry contains degree-related keywords
                for pattern in degree_patterns:
                    if re.search(pattern, entry.lower()) and len(entry) > 10:
                        edu_dict = {
                            'description': entry[:200],
                            'full_text': entry
                        }
                        education.append(edu_dict)
                        break
        
        return education[:3]  # Return top 3 education entries
    
    def calculate_experience_years(self, text: str) -> str:
        """Estimate years of experience"""
        # Look for patterns like "X years", "X+ years"
        exp_pattern = r'(\d+)\+?\s*years?\s*(of)?\s*(experience)?'
        matches = re.findall(exp_pattern, text.lower())
        
        if matches:
            years = [int(match[0]) for match in matches]
            return f"{max(years)} years"
        
        # Count experiences as rough estimate
        experiences = self.extract_experience(text)
        if len(experiences) > 0:
            return f"~{len(experiences)} positions"
        
        return "Not specified"
    
    def parse_resume(self, file_path: str) -> Dict:
        """Main method to parse resume and extract all information"""
        try:
            # Determine file type and extract text
            if file_path.lower().endswith('.pdf'):
                raw_text = self.extract_text_from_pdf(file_path)
            elif file_path.lower().endswith('.docx'):
                raw_text = self.extract_text_from_docx(file_path)
            else:
                raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")
            
            # Extract structured information
            contact_info = self.extract_contact_info(raw_text)
            skills = self.extract_skills(raw_text)
            experience = self.extract_experience(raw_text)
            education = self.extract_education(raw_text)
            exp_years = self.calculate_experience_years(raw_text)
            
            # Combine all extracted data
            parsed_data = {
                'file_path': file_path,
                'raw_text': raw_text,
                'candidate_name': contact_info.get('name', 'Unknown'),
                'email': contact_info.get('email'),
                'phone': contact_info.get('phone'),
                'linkedin': contact_info.get('linkedin'),
                'github': contact_info.get('github'),
                'skills': skills,
                'experience': experience,
                'education': education,
                'experience_years': exp_years,
                'parsed_data': {
                    'total_skills': len(skills),
                    'total_experiences': len(experience),
                    'total_education': len(education)
                }
            }
            
            return parsed_data
            
        except Exception as e:
            print(f"Error parsing resume: {e}")
            raise Exception(f"Failed to parse resume: {str(e)}")
    
    def get_resume_summary(self, parsed_data: Dict) -> str:
        """Generate a summary of the parsed resume"""
        summary_parts = []
        
        summary_parts.append(f"Candidate: {parsed_data.get('candidate_name', 'Unknown')}")
        
        if parsed_data.get('email'):
            summary_parts.append(f"Email: {parsed_data['email']}")
        
        if parsed_data.get('skills'):
            skills_str = ", ".join(parsed_data['skills'][:10])
            summary_parts.append(f"Skills: {skills_str}")
        
        if parsed_data.get('experience_years'):
            summary_parts.append(f"Experience: {parsed_data['experience_years']}")
        
        return " | ".join(summary_parts)

# Test function
if __name__ == "__main__":
    parser = ResumeParser()
    # Test with a resume file
    # result = parser.parse_resume("path/to/resume.pdf")
    # print(json.dumps(result, indent=2))