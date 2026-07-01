import json
import os
import re
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

AI_API_KEY = os.environ.get('AI_API_KEY', '')
AI_API_BASE_URL = os.environ.get('AI_API_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta')
AI_MODEL = os.environ.get('AI_MODEL', 'gemini-2.5-flash')

ANALYSIS_PROMPT = """You are an expert career analyst and recruiter. Analyze the following resume or profile description and extract a comprehensive professional profile.

{input_content}

Return a valid JSON object with EXACTLY these fields (no markdown, no code blocks, just raw JSON):

{{
  "full_name": "string or empty",
  "email": "string or empty",
  "phone": "string or empty",
  "location": "string or empty",
  "summary": "2-3 sentence professional summary",
  "skills": ["skill1", "skill2", ...],
  "technologies": ["tech1", "tech2", ...],
  "soft_skills": ["skill1", "skill2", ...],
  "experience_years": 0,
  "experience_level": "junior|mid|senior|lead|executive",
  "education": [
    {{"degree": "string", "field": "string", "institution": "string", "year": "string or empty"}}
  ],
  "job_titles": ["title1", "title2", ...],
  "languages": ["English", ...],
  "certifications": ["cert1", ...],
  "projects": ["project1", ...],
  "inferred_skills": ["skill that can be inferred from the profile but not explicitly mentioned"],
  "recommended_job_categories": ["category1", ...],
  "search_keywords": ["keyword1", ...],
  "career_strengths": ["strength1", ...],
  "areas_for_growth": ["area1", ...]
}}

Rules:
- Extract ALL technical skills and technologies mentioned
- If experience years is not explicitly stated, estimate based on career progression
- Infer additional relevant skills that logically accompany the stated skills
- Generate search keywords that would help find matching jobs
- Be comprehensive but accurate
- If input is a text description rather than a resume, work with whatever information is provided
"""

MATCHING_PROMPT = """You are an expert job matching AI. Analyze the candidate's profile and match them against the available jobs.

CANDIDATE PROFILE:
{candidate_profile}

AVAILABLE JOBS:
{jobs_json}

For EACH job, provide:
1. A compatibility score from 0 to 100
2. Reasons why it matches (specific skills, experience, etc.)
3. Missing skills the candidate would need
4. A brief explanation of the match quality

Return a valid JSON object (no markdown, no code blocks, just raw JSON):
{{
  "matches": [
    {{
      "job_id": 123,
      "job_title": "Job Title",
      "company": "Company Name",
      "match_score": 85,
      "match_reasons": ["Strong Python experience", "Django knowledge matches requirement", ...],
      "missing_skills": ["Docker", "Kubernetes", ...],
      "explanation": "This role is an excellent match because...",
      "recommendation": "strong_match|good_match|potential_match"
    }}
  ],
  "overall_summary": "Based on the analysis...",
  "top_skills": ["most valuable skill 1", ...],
  "suggested_improvements": ["suggestion 1", ...]
}}

Rules:
- Be specific about why each job matches or doesn't match
- Consider skills, technologies, experience level, and job requirements
- Provide actionable missing skills
- Sort matches by score (highest first)
- Only include jobs with score >= 20
- Be honest - not every job will be a good match
"""


def call_ai_api(prompt: str, max_tokens: int = 4000) -> Optional[str]:
    """Call the Google AI Studio (Gemini) API and return the response text."""
    url = f'{AI_API_BASE_URL}/models/{AI_MODEL}:generateContent?key={AI_API_KEY}'

    payload = {
        'contents': [
            {'parts': [{'text': prompt}]}
        ],
        'generationConfig': {
            'temperature': 0.3,
            'maxOutputTokens': max_tokens,
        },
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        content = data['candidates'][0]['content']['parts'][0]['text']
        return content
    except requests.exceptions.Timeout:
        logger.error('AI API request timed out')
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f'AI API request failed: {e}')
        return None
    except (KeyError, IndexError) as e:
        logger.error(f'Unexpected AI API response format: {e}')
        return None


def parse_json_response(text: str) -> Optional[dict]:
    """Extract and parse JSON from AI response, handling markdown code blocks."""
    if not text:
        return None

    cleaned = text.strip()

    patterns = [
        r'```json\s*\n?(.*?)\n?\s*```',
        r'```\s*\n?(.*?)\n?\s*```',
        r'\{.*\}',
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            json_str = match.group(1) if match.lastindex else match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error(f'Failed to parse AI response as JSON: {cleaned[:500]}')
        return None


def analyze_with_ai(text: str, input_type: str = 'text') -> dict:
    """Analyze resume text or profile description using AI."""
    prompt = ANALYSIS_PROMPT.format(
        input_content=f"Input Type: {input_type}\n\nContent:\n{text}"
    )

    ai_response = call_ai_api(prompt)
    if not ai_response:
        return None

    parsed = parse_json_response(ai_response)
    return parsed


def match_jobs_with_ai(candidate_profile: dict, jobs: list) -> dict:
    """Match candidate profile against jobs using AI."""
    jobs_summary = []
    for job in jobs[:50]:
        skills_list = [s.name if hasattr(s, 'name') else str(s) for s in job.skills_required.all()] if hasattr(job, 'skills_required') else []
        jobs_summary.append({
            'id': job.id,
            'title': job.title,
            'company': job.company.company_name if hasattr(job, 'company') and job.company else '',
            'description': job.description[:500] if job.description else '',
            'requirements': job.requirements[:500] if job.requirements else '',
            'skills_required': skills_list,
            'experience_required': job.experience_required,
            'location': job.location,
            'job_type': job.job_type,
            'workplace_type': job.workplace_type,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
        })

    prompt = MATCHING_PROMPT.format(
        candidate_profile=json.dumps(candidate_profile, indent=2),
        jobs_json=json.dumps(jobs_summary, indent=2),
    )

    ai_response = call_ai_api(prompt, max_tokens=8000)
    if not ai_response:
        return None

    parsed = parse_json_response(ai_response)
    return parsed
