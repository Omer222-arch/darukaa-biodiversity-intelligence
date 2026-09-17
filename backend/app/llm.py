import requests
from .config import GEMINI_API_KEY, GEMINI_MODEL

def synthesize(user_input, state, reasoning, candidates, evidence):
    if not GEMINI_API_KEY:
        return None

    evidence_text = "\n".join(
        f"- {e['title']} | {e['organization']} | {e['excerpt']}"
        for e in evidence
    )
    prompt = f"""
You are an environmental scientist assistant.
Answer ONLY using the supplied user state, reasoning trace and retrieved evidence.
Do not invent quantitative effect sizes, citations, species names, or causal claims.
If the evidence does not support a numerical estimate, explicitly say that a site-specific estimate requires measurement/model calibration.

USER STATE:
{user_input}

ENVIRONMENTAL STATE:
{state}

REASONING:
{reasoning}

CANDIDATE ACTIONS:
{candidates}

RETRIEVED EVIDENCE:
{evidence_text}

Return concise JSON with:
summary
recommendations: [{action, why_it_works, impacted_metrics, time_horizon, confidence}]
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    response = requests.post(
        url,
        params={"key": GEMINI_API_KEY},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
