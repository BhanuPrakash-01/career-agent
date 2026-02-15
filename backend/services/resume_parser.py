# backend/services/resume_parser.py
import os
import json
import pdfplumber
from fastapi import UploadFile
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional

# --- 1. Define Strict Schemas ---

class WorkExperience(BaseModel):
    company: str = Field(description="Name of the company or organization")
    role: str = Field(description="Job Title (e.g., Intern, Junior Engineer)")
    start_date: str
    end_date: str
    description: str = Field(description="Bullet points describing the work")

class Project(BaseModel):
    name: str = Field(description="Name of the project")
    tech_stack: str = Field(description="Tools used (e.g., Python, SolidWorks, React)")
    description: str = Field(description="What was built/achieved")
    link: Optional[str] = Field(description="ONLY include if explicitly present (e.g., github.com/...). Otherwise leave empty.")

class ResumeSchema(BaseModel):
    full_name: str
    email: str
    phone: str
    linkedin: Optional[str]
    summary: str
    skills: List[str]
    work_experience: List[WorkExperience] # Strictly for Jobs/Internships
    projects: List[Project]               # Strictly for Personal/Academic Projects

# --- 2. Initialize Client ---
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def extract_text_from_pdf(file_file) -> str:
    text = ""
    try:
        with pdfplumber.open(file_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
    except Exception as e:
        print(f"PDF Reading Error: {e}")
        return ""
    return text

async def parse_resume_with_gemini(file: UploadFile):
    raw_text = extract_text_from_pdf(file.file)
    if not raw_text.strip():
        return {"error": "Could not read text from PDF."}

    try:
        # We explicitly ask Gemini to categorize Jobs vs Projects
        prompt = f"""
        Extract data from this resume. 
        CRITICAL RULES:
        1. **Separation:** If the item lists a "Company", put it in 'work_experience'. 
           If it is a "Personal Project", "Academic Project", or "Capstone", put it in 'projects'.
        2. **Links:** DO NOT invent links. If a project has no URL in the text, leave 'link' empty.
        3. **Tech Stack:** For Mechanical projects, 'tech_stack' might be 'SolidWorks, AutoCAD'.
        
        RESUME TEXT:
        {raw_text}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': ResumeSchema,
            }
        )
        return json.loads(response.text)

    except Exception as e:
        print(f"Parser Error: {e}")
        return {"error": str(e)}