import os
import json
from typing import List

import requests


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4.1-mini"  


def build_project_summary(title: str, description: str, diagnostic_context: str) -> str:
    parts = []
    if title:
        parts.append(f"Title: {title}")
    if diagnostic_context:
        parts.append(f"Diagnostic context: {diagnostic_context}")
    if description:
        parts.append(f"Description: {description}")
    return "\n".join(parts)


def build_doc_snippets(texts: List[str], max_chars: int = 8000) -> str:
    joined = "\n\n".join(texts)
    if len(joined) > max_chars:
        return joined[:max_chars]
    return joined


def _call_openai_chat(system_message: str, user_message: str) -> str:
    """
    Low level call to OpenAI chat completions.
    Returns the assistant message content as plain text.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please export it in your shell before running the server."
        )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
    }

    response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]


def run_social_risk_analysis(project_summary: str, docs_text: List[str]) -> str:
    """
    Calls the real OpenAI LLM and returns a JSON string with findings.
    """
    doc_snippets = build_doc_snippets(docs_text)

    system_message = (
        "You are an expert in responsible AI and social sustainability in health care. "
        "You receive documentation about an AI diagnostic system. "
        "Your task is to identify social risks and equity issues and to describe them clearly "
        "for clinicians and AI developers. "
        "Focus on how design and deployment choices might affect different patient groups, "
        "especially under served groups such as rural communities, Indigenous peoples, migrants, "
        "and patients with low income. "
        "Answer in valid JSON only."
    )

    user_message = f"""
Project context
{project_summary}

Documentation excerpts
{doc_snippets}

Task
1. Identify potential social risks and biases in this diagnostic AI system.
2. Group findings into categories: equity, representation, access, workflow_impact, documentation_gap.
3. For each finding, give
   a short title
   a clear description linked to the evidence in the text
   a severity rating: low, medium, high
   a confidence score between 0 and 1
4. List any information that appears missing but is necessary to assess social risks, phrased as questions.

Return the answer as valid JSON with the keys:
"findings": list of objects with keys "category", "title", "description", "severity", "confidence"
"missing_information_questions": list of strings.
"""

    content = _call_openai_chat(system_message, user_message)

    
    try:
        parsed = json.loads(content)
        return json.dumps(parsed)
    except Exception:
        # If the model outputs text that is not strict JSON, wrap it so we do not crash the backend
        safe_wrapper = {
            "findings": [],
            "missing_information_questions": [],
            "raw_output": content,
        }
        return json.dumps(safe_wrapper)

