# main.py
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from services.embedding import get_embedding
from services.search import search_similar_experience
from agent.graph import resume_builder_app
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form

# Import the new service we just wrote
from services.resume_parser import parse_resume_with_gemini

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase credentials missing.")

supabase: Client = create_client(url, key)

app = FastAPI(title="Truthful Career Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Next.js runs here by default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SCHEMAS ---
class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = "Present"
    description: str

class MasterProfile(BaseModel):
    full_name: str
    summary: str
    skills: List[str]
    experiences: List[WorkExperience]

class SearchQuery(BaseModel):
    query_text: str
    limit: int = 3

class GenerateRequest(BaseModel):
    job_description: str
    user_id: str = "demo-user-123"
# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "Career Agent Backend is Running"}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...),user_id: str = Form(...)):
    """
    1. Takes a PDF file upload.
    2. Uses Gemini to parse it into JSON.
    3. Saves the parsed data to Supabase.
    """
    # 1. Parse PDF using Gemini
    parsed_data = await parse_resume_with_gemini(file)
    
    if "error" in parsed_data:
        raise HTTPException(status_code=500, detail=parsed_data["error"])

    # 2. Save to Supabase (The Truth Store)
    try:
        # 2. Save Profile (Name, Contact)
        # We first check if a user exists, if so update, else insert.
        # For now, we just insert a new one for simplicity.
        # 2. Check if Profile exists, or Create New
    # We use upsert logic or simple check
        existing = supabase.table("master_profiles").select("id").eq("user_id", user_id).execute()

        if existing.data:
            profile_id = existing.data[0]['id']
            # Optional: Update the summary/skills if needed
            supabase.table("master_profiles").update({
                "full_name": parsed_data.get("full_name"),
                "summary": parsed_data.get("summary"),
                "skills": parsed_data.get("skills")
            }).eq("id", profile_id).execute()
        else:
            # Create new
            res = supabase.table("master_profiles").insert({
                "user_id": user_id,
                "full_name": parsed_data.get("full_name"),
                "summary": parsed_data.get("summary"),
                "skills": parsed_data.get("skills")
            }).execute()
            profile_id = res.data[0]['id']

        # 3. Save Work Experience (Clear old ones first to avoid duplicates on re-upload)
        supabase.table("experience_items").delete().eq("profile_id", profile_id).execute()

        jobs = parsed_data.get("work_experience", [])
        for job in jobs:
            text_blob = f"{job.get('role')} at {job.get('company')}: {job.get('description')}"
            vector = get_embedding(text_blob)

            supabase.table("experience_items").insert({
                "profile_id": profile_id,
                "type": "job",
                "company": job.get("company"),
                "title": job.get("role"),
                "start_date": job.get("start_date"),
                "end_date": job.get("end_date"),
                "description": job.get("description"),
                "embedding": vector
            }).execute()

        # 4. Save Projects (Clear old ones first)
        supabase.table("project_items").delete().eq("profile_id", profile_id).execute()

        projects = parsed_data.get("projects", [])
        for proj in projects:
            text_blob = f"Project {proj.get('name')} using {proj.get('tech_stack')}: {proj.get('description')}"
            vector = get_embedding(text_blob)

            supabase.table("project_items").insert({
                "profile_id": profile_id,
                "name": proj.get("name"),
                "tech_stack": proj.get("tech_stack"),
                "description": proj.get("description"),
                "link": proj.get("link"),
                "embedding": vector
            }).execute()

        return {"status": "success", "message": "Profile Updated", "data": parsed_data}
    except Exception as e:
        # If DB fails, tell us why
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-experience")
async def search_experience(search: SearchQuery):
    """
    Simulates the RAG Retrieval step.
    Send a Job Description requirement (e.g. 'Must know React')
    and see if the system finds it in your resume.
    """
    results = await search_similar_experience(
        query=search.query_text,
        supabase_client=supabase,
        limit=search.limit
    )
    
    if not results:
        return {"message": "No relevant experience found.", "results": []}
        
    return {
        "query": search.query_text,
        "matches_found": len(results),
        "results": results
    }

@app.post("/generate-resume")
async def generate_resume(request: GenerateRequest):
    # 1. Fetch the Master Profile (Education, Skills, Name)
    # We assume the user has ID "demo-user-123" for this tutorial
    profile_res = supabase.table("master_profiles").select("*").eq("user_id", request.user_id).execute()
    
    if not profile_res.data:
        # Fallback if no profile exists yet
        user_context = "User Name: Candidate\nEducation: Bachelor of Technology"
    else:
        p = profile_res.data[0]
        # Format the profile data as a string for the LLM
        user_context = f"""
        Name: {p.get('full_name')}
        Existing Summary: {p.get('summary')}
        Base Skills: {', '.join(p.get('skills', []))}
        """

    # 2. RAG Step: Search for relevant experience
    rag_results = await search_similar_experience(
        query=request.job_description,
        supabase_client=supabase,
        limit=5
    )
    
    context_str = ""
    for item in rag_results:
        context_str += f"- Role: {item['title']} at {item['company']} ({item.get('start_date','N/A')} - {item.get('end_date','N/A')})\n  Details: {item['description']}\n\n"

    # 3. Initialize Graph State with EVERYTHING
    initial_state = {
        "job_description": request.job_description,
        "retrieved_experience": context_str,
        "user_profile": user_context, # <--- Passing the full profile now
        "revision_count": 0,
        "is_approved": False,
        "critic_feedback": "",
        "draft_resume": "",
        "extracted_requirements": {}
    }

    # 4. Run the Agent Graph
    final_state = resume_builder_app.invoke(initial_state)
    
    return {
        "status": "success",
        "final_resume": final_state["draft_resume"], # This will now be the full clean text
        "critic_feedback": final_state["critic_feedback"],
        "revisions": final_state["revision_count"]
    }