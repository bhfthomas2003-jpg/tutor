import json, re, httpx
from fastapi import HTTPException
from ..config import S

SYS = """You write mathematics teaching scripts. Reply with ONLY valid JSON:
{"title":str,"scenes":[{"title":str,"math":[str],"narration":str,"checks":[str]}]}
Scenes in order: learning objectives, definitions, worked example(s) step by step, common mistakes (if relevant), practice questions, summary.
"math": 1-6 short plain-text lines shown on screen (use unicode like x², √, ≤). "narration": natural spoken words, no LaTeX, no markdown.
"checks": only simple verifiable identities written as 'lhs == rhs' using * / ^ ( ) (e.g. '(x+1)^2 == x^2+2*x+1'); otherwise [].
Optional per scene: "kind":"graph"|"numberline"|"geometry" (default "steps") with "visual": graph {"functions":["x^2-4"],"x_range":[-5,5],"y_range":[-6,6],"points":[[2,0]]}; numberline {"range":[-5,5],"intervals":[{"a":-1,"b":3,"closed":[true,false]}],"points":[{"v":2,"label":"x=2"}]}; geometry {"points":{"A":[0,0],"B":[4,0],"C":[1,3]},"segments":["AB","BC","CA"],"circles":[{"center":"A","through":"B"}]}. Use only when it helps.\nFor proofs give every logical step with its justification. Never invent credentials. Do not claim anything is verified."""

def make_script(req):
    if not S.anthropic_key:
        raise HTTPException(503, "AI provider not configured: set ANTHROPIC_API_KEY on the backend.")
    prompt = (f"Topic/problem: {req.topic}\nLevel: {req.level}\nObjective: {req.objective or 'n/a'}\n"
              f"Target length: about {req.minutes} minutes of narration (~{req.minutes*130} words)\n"
              f"Difficulty: {req.difficulty}\nStyle: {req.style}\nLanguage: {req.language}")
    try:
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=180,
            headers={"x-api-key": S.anthropic_key, "anthropic-version": "2023-06-01"},
            json={"model": S.model, "max_tokens": 6000, "system": SYS,
                  "messages": [{"role": "user", "content": prompt}]})
    except httpx.HTTPError:
        raise HTTPException(502, "Could not reach the AI provider.")
    if r.status_code != 200:
        raise HTTPException(502, f"AI provider error (HTTP {r.status_code}). Check key, model name and credit.")
    text = "".join(b.get("text", "") for b in r.json().get("content", []))
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0))
    except Exception:
        raise HTTPException(502, "AI returned unreadable output. Please try again.")
