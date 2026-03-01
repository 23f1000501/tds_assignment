import os
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI

# 1. Define the Structured Output Schema
class SentimentResponse(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    rating: int = Field(..., ge=1, le=5)

# 2. Define the Request Schema
class CommentRequest(BaseModel):
    comment: str

app = FastAPI()

# 3. Add CORS Middleware (Fixes the "Failed to fetch" error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Initialize OpenAI Client for AI Pipe
# Replace 'YOUR_AIPIPE_TOKEN' with your token from aipipe.org
client = OpenAI(
    base_url="https://aipipe.org/openai/v1",
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjEwMDA1MDFAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9._Kb1NMjhvk6v7iJXOmRK0Ic83uF3kzF8-ojAyImUjHQ" 
)

@app.post("/comment", response_model=SentimentResponse)
async def analyze_comment(request: CommentRequest):
    try:
        # 5. Call AI Pipe using the structured outputs feature
        completion = client.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Analyze sentiment: positive, negative, or neutral. Provide a rating 1-5."},
                {"role": "user", "content": request.comment},
            ],
            response_format=SentimentResponse,
        )

        return completion.choices[0].message.parsed

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
