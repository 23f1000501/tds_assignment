import os
import sys
import traceback
from io import StringIO
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai

app = FastAPI()

# ✅ CORS Enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Structured Output Schema ---

class ErrorAnalysis(BaseModel):
    # Field description helps the Gemini 3 model understand the task better
    error_lines: List[int] = Field(description="List of line numbers where the error occurred.")

class CodeRequest(BaseModel):
    code: str

class CodeResponse(BaseModel):
    error: List[int]
    result: str

# --- Tool Function ---

def execute_python_code(code: str) -> dict:
    old_stdout = sys.stdout
    redirected_output = StringIO()
    sys.stdout = redirected_output
    try:
        # Execute the code in a clean global/local dict
        exec(code, {})
        output = redirected_output.getvalue()
        return {"success": True, "output": output}
    except Exception:
        # If it fails, capture the exact traceback
        return {"success": False, "output": traceback.format_exc()}
    finally:
        sys.stdout = old_stdout

# --- AI Agent ---

def analyze_error_with_ai(code: str, tb: str) -> List[int]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return []

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Analyze this Python code and its error traceback.
    Identify the line number(s) where the root cause of the error is located.
    
    CODE:
    {code}
    
    TRACEBACK:
    {tb}
    """

    # Using the Gemini 3 Flash model with Structured Output config
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": ErrorAnalysis.model_json_schema(),
        },
    )

    # Validate and return the structured data
    try:
        analysis = ErrorAnalysis.model_validate_json(response.text)
        return analysis.error_lines
    except Exception as e:
        print(f"Parsing Error: {e}")
        return []

# --- FastAPI Endpoint ---

@app.post("/code-interpreter", response_model=CodeResponse)
async def code_interpreter(request: CodeRequest):
    # 1. Run the code
    execution = execute_python_code(request.code)
    
    # 2. If success, return result with empty error list
    if execution["success"]:
        return CodeResponse(error=[], result=execution["output"])
    
    # 3. If failure, use AI to find the bad lines
    error_lines = analyze_error_with_ai(request.code, execution["output"])
    
    return CodeResponse(
        error=error_lines,
        result=execution["output"]
    )
