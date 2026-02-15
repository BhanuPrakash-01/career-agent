# backend/agent/nodes.py
import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from .state import ResumeGraphState

# 1. Initialize the LLM
# We use a low temperature (0.1) for the Analyst/Critic to be strict/factual.
# We use a slightly higher temperature (0.4) for the Writer to be creative but grounded.
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    temperature=0.2,
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

# --- ANALYST AGENT ---

class AnalystOutput(BaseModel):
    hard_skills: list[str] = Field(description="List of top 5 technical skills required")
    soft_skills: list[str] = Field(description="List of top 3 soft skills or culture fit traits")
    key_responsibilities: list[str] = Field(description="Summary of main tasks in 3 bullet points")

def analyst_node(state: ResumeGraphState) -> Dict[str, Any]:
    print("--- ANALYST: Dissecting Job Description ---")
    
    parser = JsonOutputParser(pydantic_object=AnalystOutput)
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert Technical Recruiter. Analyze the following Job Description (JD).
        Extract the critical 'Hard Requirements' that a candidate MUST have to pass the ATS (Applicant Tracking System).
        
        JOB DESCRIPTION:
        {jd}
        
        {format_instructions}
        """
    )
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "jd": state["job_description"],
            "format_instructions": parser.get_format_instructions()
        })
        return {"extracted_requirements": result}
    except Exception as e:
        print(f"Analyst Error: {e}")
        return {"extracted_requirements": {}}




import ast  # We need this to parse the dictionary string safely


def clean_ai_response(content):
    """
    Universal Cleaner: Handles Strings, Dictionaries, and Lists 
    to extract ONLY the resume text.
    """
    # Case A: It's a string that LOOKS like a dictionary "{'type': 'text'...}"
    # (This is exactly what you are seeing in your error)
    if isinstance(content, str):
        content = content.strip()
        if content.startswith("{") and "text" in content:
            try:
                # We interpret the string as a Python Dictionary
                data = ast.literal_eval(content)
                if isinstance(data, dict) and "text" in data:
                    return data["text"]
            except:
                pass # If it fails, we assume it's just a normal string
    
    # Case B: It is ALREADY a Dictionary object
    if isinstance(content, dict):
        if "text" in content:
            return content["text"]
            
    # Case C: It is a List (LangChain often returns a list of blocks)
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
        return "\n".join(text_parts)
        
    # Case D: It's just a normal string
    return str(content)

# --- WRITER NODE ---


def writer_node(state: ResumeGraphState) -> Dict[str, Any]:
    revision = state.get("revision_count", 0) + 1
    print(f"--- WRITER: Drafting 'MTeck' Style Resume (Revision {revision}) ---")
    
    requirements = state.get("extracted_requirements", {})
    feedback = state.get("critic_feedback", "None")
    user_profile = state.get("user_profile", "")
    history_str = str(state.get("retrieved_experience", "No history found."))
    
    # We embed the EXACT Preamble from your template to ensure the style matches 100%
    template_structure = r"""
    \documentclass[letterpaper,10pt]{article}
    \usepackage[empty]{fullpage}
    \usepackage{titlesec}
    \usepackage{enumitem}
    \usepackage[hidelinks]{hyperref}
    \usepackage{fancyhdr}
    \usepackage{fontawesome5}
    \usepackage{multicol}
    \usepackage{bookmark}
    \usepackage{lastpage}
    \usepackage{CormorantGaramond}
    \usepackage{charter}
    \usepackage{xcolor}
    
    % COLORS
    \definecolor{accentTitle}{HTML}{003366}
    \definecolor{accentLine}{HTML}{003366}
    \definecolor{accentText}{HTML}{000000}

    % MARGINS
    \addtolength{\oddsidemargin}{-0.7in}
    \addtolength{\evensidemargin}{-0.5in}
    \addtolength{\textwidth}{1.19in}
    \addtolength{\topmargin}{-0.7in}
    \addtolength{\textheight}{1.4in}
    \setlength{\multicolsep}{-3.0pt}
    \setlength{\columnsep}{-1pt}
    \setlength{\tabcolsep}{0pt}
    \setlength{\footskip}{3.7pt}
    \raggedbottom
    \raggedright
    \input{glyphtounicode}
    \pdfgentounicode=1

    % CUSTOM COMMANDS
    \newcommand{\documentTitle}[2]{
      \begin{center}
        {\Huge\color{accentTitle} #1}
        \vspace{10pt}
        {\color{accentLine} \hrule}
        \vspace{2pt}
        \footnotesize{#2}
        \vspace{2pt}
        {\color{accentLine} \hrule}
      \end{center}
    }
    \newcommand{\tinysection}[1]{
      \phantomsection
      \addcontentsline{toc}{section}{#1}
      {\large{\bfseries\color{accentText}#1} {\color{accentLine} |}}
    }
    \titleformat{\section}{
      \vspace{-5pt}
      \color{accentText}
      \raggedright\large\bfseries
    }{}{0em}{}[\color{accentLine}\titlerule]
    
    \newcommand{\heading}[2]{
      \hspace{10pt}#1\hfill#2\\
    }
    \newcommand{\headingBf}[2]{
      \heading{\textbf{#1}}{\textbf{#2}}
    }
    \newcommand{\headingIt}[2]{
      \heading{\textit{#1}}{\textit{#2}}
    }
    \newenvironment{resume_list}{
      \vspace{-7pt}
      \begin{itemize}[itemsep=-2px, parsep=1pt, leftmargin=30pt]
    }{
      \end{itemize}
    }
    """

    prompt = ChatPromptTemplate.from_template(
        """
        You are an elite Resume Architect. You MUST use the specific LaTeX template provided below.
        
        GOAL:
        Create a high-impact, ATS-optimized resume tailored to the JOB DESCRIPTION.
        
        CRITICAL RULES FOR CONTENT:
        1. **Separation of Concerns:** - IF the user worked at a Company or was an Intern -> Put it in `\\section{{Experience}}`.
           - IF it was a Personal Project or Academic Project -> Put it in `\\section{{Projects}}`.
           - DO NOT mix these up.
        2. **Hyperlinks:** - You MUST use `\\href{{URL}}{{DisplayText}}` for all links (GitHub, LinkedIn, Live Demos).
           - Example: `\\href{{https://github.com/...}}{{\\small GitHub}}`
        3. **Formatting:**
           - Use `\\headingBf{{Role}}{{Company | Date}}` for Experience.
           - Use `\\headingBf{{Project Name}}{{\\href{{link}}{{GitHub}} | \\href{{link}}{{Demo}}}}` for Projects.
           - Use `\\begin{{resume_list}} ... \\item ... \\end{{resume_list}}` for bullet points.
           - MAX 3-4 bullet points per item. Be concise.
        
        INPUT DATA:
        - Job Description: {requirements}
        - User Profile: {user_profile}
        - User History: {history}
        - Feedback: {feedback}
        
        TEMPLATE PREAMBLE (Use this EXACTLY at the start):
        {template}
        
        OUTPUT INSTRUCTIONS:
        - Start with the Preamble provided.
        - Fill in `\\begin{{document}}`...`\\end{{document}}`.
        - Add a Summary section using `\\tinysection{{Summary}}`.
        - Add Skills section at the bottom.
        - Return ONLY the raw LaTeX code. No Markdown blocks.
        """
    )
    
    chain = prompt | llm
    
    result = chain.invoke({
        "requirements": str(requirements),
        "user_profile": user_profile,
        "history": history_str,
        "feedback": feedback,
        "template": template_structure # We inject the template code here
    })
    
    # Use our universal cleaner
    final_text = clean_ai_response(result.content)
    
    return {
        "draft_resume": final_text,
        "revision_count": revision
    }


# --- CRITIC AGENT ---

class CriticOutput(BaseModel):
    is_approved: bool = Field(description="True if the resume is excellent, False if it needs work")
    feedback: str = Field(description="Specific instructions on what to fix. If approved, say 'Good job'.")
    score: int = Field(description="Score out of 10")

def critic_node(state: ResumeGraphState) -> Dict[str, Any]:
    print("--- CRITIC: Reviewing Draft ---")
    
    parser = JsonOutputParser(pydantic_object=CriticOutput)
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are a ruthless Hiring Manager. Review this draft resume section.
        
        CRITERIA FOR APPROVAL:
        1. Quantified Results: Does it have numbers? (%, $, X times). If not, REJECT IT.
        2. Relevance: Does it mention the hard skills from the requirements?
        3. Clarity: Is it concise?
        
        DRAFT RESUME:
        {draft}
        
        TARGET REQUIREMENTS:
        {requirements}
        
        {format_instructions}
        """
    )
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "draft": state["draft_resume"],
            "requirements": str(state.get("extracted_requirements", "")),
            "format_instructions": parser.get_format_instructions()
        })
        
        return {
            "is_approved": result["is_approved"],
            "critic_feedback": result["feedback"]
        }
    except Exception as e:
        print(f"Critic Error: {e}")
        # Default to approval to avoid infinite error loops if parsing fails
        return {"is_approved": True, "critic_feedback": "Error parsing critique."}