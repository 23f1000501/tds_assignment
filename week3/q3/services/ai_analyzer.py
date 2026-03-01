import os
from typing import List
from google import genai
from google.genai import types
from models.schemas import ErrorAnalysis


def analyze_error_with_ai(code: str, traceback_text: str) -> List[int]:
    """
    Use Gemini with structured output to identify error line numbers.
    """

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    prompt = f"""
You are a Python debugging expert.

Analyze the following Python code and traceback.
Return ONLY the line number(s) in the user's code where the error occurred.

CODE:
{code}

TRACEBACK:
{traceback_text}
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "error_lines": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.INTEGER),
                    )
                },
                required=["error_lines"],
            ),
        ),
    )

    result = ErrorAnalysis.model_validate_json(response.text)
    return result.error_lines
