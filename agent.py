import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# this is the instruction we give the AI before sending the diff
# it tells the AI what role to play and exactly what format to return
SYSTEM_PROMPT = """You are a senior code reviewer. Analyze the provided git diff and return ONLY a JSON object with exactly these four keys:
- "bugs": list of possible bugs or logic errors introduced
- "risks": list of security, performance, or reliability risks
- "missing_tests": list of cases or scenarios that lack test coverage
- "style_issues": list of code style, naming, or readability problems

Each item in a list should be a short, clear string. Return ONLY valid JSON, no markdown, no explanation."""

def _call_nemotron(diff: str) -> str:
    # send the diff to the AI model via a standard HTTP POST request
    # all config (URL, key, model name) comes from .env
    response = requests.post(
        f"{os.environ['API_BASE']}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['API_KEY']}", "Content-Type": "application/json"},
        json={
            "model": os.environ["MODEL"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},   # sets the AI's behaviour
                {"role": "user", "content": f"Review this diff:\n\n{diff}"},  # the actual diff
            ],
            "temperature": 0.2,  # low temperature = more focused, less creative output
        },
    )
    response.raise_for_status()  # crash early if the API returns an error status

    # some models return content under "text" instead of "content" - handle both
    message = response.json()["choices"][0]["message"]
    raw = message.get("content") or message.get("text") or ""

    return raw

def review_diff(diff: str) -> dict:
    # call the model and get back the raw text response
    raw = _call_nemotron(diff)

    # if the model returned nothing at all, return a clear error instead of crashing
    if not raw:
        return {"error": "Model returned an empty response. Check your API key and model name in .env"}

    # models sometimes wrap JSON in ```json ... ``` markdown fences even when told not to
    # strip those fences so json.loads does not fail
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        # parse the cleaned text into a Python dict
        feedback = json.loads(raw)
    except json.JSONDecodeError:
        # if the model returned something unparseable, do not crash 
        # just hand back the raw text so the user still sees something useful
        feedback = {"raw_response": raw}

    return feedback
