import json
import requests
from typing import List

# Use the generate endpoint and the phi3 model you pulled
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3"


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


def _call_ollama(prompt: str) -> str:
    """
    Call Ollama using the /api/generate endpoint with the phi3 model.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        # /api/generate returns {"response": "...", ...}
        return data.get("response", "")
    except Exception as e:
        # Return a JSON string that our caller can wrap safely
        return json.dumps({
            "findings": [],
            "missing_information_questions": [],
            "error": f"Ollama call failed: {str(e)}"
        })


def run_social_risk_analysis(project_summary: str, docs_text: List[str]) -> str:
    """
    Generate structured social risk findings using phi3.
    Ensures valid JSON output is returned.
    """

    doc_snippets = build_doc_snippets(docs_text)

    prompt = f"""
You are an expert in responsible AI and social sustainability in health care.
You analyze documentation about an AI diagnostic system and identify social risks and fairness issues.

Project context:
{project_summary}

Documentation excerpts:
{doc_snippets}

Task:
1. Identify potential social risks and fairness issues in this diagnostic AI system.
2. Group findings into categories. Use only these values:
   - equity
   - representation
   - access
   - workflow_impact
   - documentation_gap
3. For each finding, provide:
   - category
   - title
   - description with evidence from the text
   - severity: low, medium, or high
   - confidence: a number between 0 and 1
4. Provide a list of questions for missing information needed to assess social risks.

Return only a valid JSON object with this exact shape:

{{
  "findings": [
    {{
      "category": "equity",
      "title": "short title",
      "description": "clear explanation",
      "severity": "low",
      "confidence": 0.7
    }}
  ],
  "missing_information_questions": [
    "question one",
    "question two"
  ]
}}

Do not include any extra text before or after the JSON.
"""

    raw_output = _call_ollama(prompt)

    # Try to parse JSON
    try:
        parsed = json.loads(raw_output)
        return json.dumps(parsed)
    except Exception:
        # Wrap non JSON outputs safely so the backend does not crash
        return json.dumps({
            "findings": [],
            "missing_information_questions": [],
            "raw_output": raw_output
        })
