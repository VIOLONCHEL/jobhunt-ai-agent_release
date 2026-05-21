import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

from security import OPENAI_API_KEY

router = APIRouter(prefix="/ai", tags=["AI"])


class AIRequest(BaseModel):
    resume_text: str
    job_description: str


@router.post("/insight")
def generate_insight(data: AIRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    if not data.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required")

    if not data.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
You are an AI resume matching assistant.

Analyze the candidate resume against the vacancy.

Return ONLY valid JSON in this exact format:
{{
  "summary": "one short sentence, max 18 words",
  "why_match": ["max 2 short bullet points"],
  "missing": ["max 3 short bullet points"],
  "improve": ["max 3 short bullet points"]
}}

Rules:
- Keep everything concise
- No markdown
- No headings
- No paragraphs
- No numbering
- No extra keys
- Bullet points must be short and practical

Resume:
{data.resume_text}

Job description:
{data.job_description}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert career advisor and resume reviewer."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            temperature=0.3,
        )

        raw = response.choices[0].message.content or "{}"

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse AI response")

        return {
            "summary": parsed.get("summary", ""),
            "why_match": parsed.get("why_match", [])[:2],
            "missing": parsed.get("missing", [])[:3],
            "improve": parsed.get("improve", [])[:3],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {str(e)}")