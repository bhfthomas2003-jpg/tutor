# Thomas AI Math Studio
Your Mathematics. Your Voice. Infinite Lessons.

## Layout
- `frontend/` static HTML/CSS/JS (GitHub Pages). Holds NO secrets. `config.js` = backend URL only.
- `backend/` FastAPI: `routes/api.py` (endpoints, token auth), `services/` (llm, voice, verify, render), `models/schemas.py`, `Dockerfile` (installs FFmpeg).
- `rendering/` renderer notes + future Manim templates.

## Status
**Added:** optional Manim 'steps' template with fallback (untested: Manim is not installed in my sandbox).
**Implemented (needs your credentials to run):** topic -> AI script (Anthropic) -> edit/approve -> voice clone upload (ElevenLabs, consent checkbox) -> intro audio preview -> narration per scene -> MP4 with math text and subtitles -> preview -> download (16:9 or 9:16). Intro on by default, editable, local templates, audio cached by text+voice+settings. SymPy checks of `lhs == rhs` lines; manual-review box before approval.
**Tested:** syntax checks only (Python compiles, JS parses). The full pipeline has NOT been run end to end here (no network in my sandbox). Test it as below and report errors.
**Not built yet:** PDF/document upload, graphs/constructions, template library, Google Drive storage, per-scene regeneration UI (audio cache already makes re-renders cheap), cost figures.
**Limits:** SymPy "pass" verifies only that identity, never a whole proof. Voice cloning needs a provider plan that allows it.

## Test locally (Termux/PC)
```
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt   # also needs ffmpeg + DejaVu fonts installed
cp .env.example .env              # fill APP_TOKEN, ANTHROPIC_API_KEY, ELEVENLABS_API_KEY
uvicorn app.main:app --port 8000
```
Then in `frontend/config.js` set API_BASE=http://localhost:8000 and `python -m http.server 5500` in `frontend/`; set ALLOWED_ORIGIN=http://localhost:5500. Open the page, Settings -> paste APP_TOKEN.
Order: Create -> Script (check, tick review, approve) -> My Voice (upload) -> Intro (preview, confirm it is your voice) -> Video.

## Quick test without AI credit
`samples/sample_lesson.json` has one scene of each type (steps, graph, number line, geometry). In Create Lesson open 'load a script from JSON', paste it, then approve and generate (voice credit is still used). Run once with Simple engine, then with Manim.
