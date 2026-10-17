import json, secrets, uuid, threading
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from ..config import S
from ..models.schemas import ScriptReq, RenderReq, Intro, VoiceSettings
from ..services import llm, voice, verify, render

def auth(authorization: str = Header(default="")):
    if not S.app_token:
        raise HTTPException(503, "Server APP_TOKEN is not set.")
    if not secrets.compare_digest(authorization.removeprefix("Bearer ").strip(), S.app_token):
        raise HTTPException(401, "Invalid access token.")

r = APIRouter(prefix="/api", dependencies=[Depends(auth)])

@r.get("/status")
def status():
    return {"ai": bool(S.anthropic_key), "voice_provider": bool(S.el_key), "voice_ready": bool(voice.voice_id()),
            "manim": render.manim_ok(), "ffmpeg": bool(__import__("shutil").which("ffmpeg"))}

@r.post("/script")
def script(req: ScriptReq):
    return llm.make_script(req)

@r.post("/verify")
def check(body: dict):
    from ..models.schemas import Scene
    scenes = [Scene(**s) for s in body.get("scenes", [])]
    return {"results": verify.run(scenes),
            "note": "A 'pass' verifies only that one identity. It does not prove the lesson or any proof correct; review proofs manually."}

@r.post("/voice/clone")
async def clone(name: str = Form(...), consent: bool = Form(...), files: list[UploadFile] = File(...)):
    if not consent:
        raise HTTPException(400, "You must confirm these are your own recordings (or you are authorized to use them).")
    if not (1 <= len(files) <= 5):
        raise HTTPException(400, "Upload 1 to 5 recordings.")
    out = []
    for f in files:
        data = await f.read()
        if len(data) > S.max_upload: raise HTTPException(413, "File too large.")
        if not (f.content_type or "").startswith("audio/"): raise HTTPException(415, "Audio files only.")
        out.append((f.filename or "sample", data, f.content_type))
    vid = voice.clone(name[:60], out)
    return {"voice_id_set": True, "message": "Voice submitted. Generate the intro preview and listen before trusting it."}

@r.post("/intro")
def intro(i: Intro, v: VoiceSettings = VoiceSettings()):
    p = voice.tts(i.script, v)
    return FileResponse(p, media_type="audio/mpeg")

def _set(jid):
    f = S.data / "jobs" / f"{jid}.json"
    def s(state, msg, prog): f.write_text(json.dumps({"state": state, "message": msg, "progress": prog}))
    return s

@r.post("/render")
def start(req: RenderReq):
    if not req.approved: raise HTTPException(400, "Script must be approved before rendering.")
    if req.intro.enabled and not req.intro.script.strip(): raise HTTPException(400, "Introduction script is empty.")
    for sc in req.scenes:
        if len(json.dumps(sc.visual)) > 4000: raise HTTPException(400, "Visual settings too large.")
        try:
            for f in (sc.visual.get("functions", []) if sc.kind == "graph" else [])[:4]: verify._p(str(f))
        except Exception:
            raise HTTPException(400, "A graph function could not be read. Use forms like x^2 - 4 or 2*x + 1.")
    jid = uuid.uuid4().hex[:16]; s = _set(jid); s("running", "Queued", 0)
    threading.Thread(target=render.run, args=(jid, req, s), daemon=True).start()
    return {"job": jid}

@r.get("/jobs/{jid}")
def job(jid: str):
    f = S.data / "jobs" / f"{jid}.json"
    if not jid.isalnum() or not f.exists(): raise HTTPException(404, "Unknown job.")
    return json.loads(f.read_text())

@r.get("/videos/{jid}")
def video(jid: str):
    p = S.data / "videos" / f"{jid}.mp4"
    if not jid.isalnum() or not p.exists(): raise HTTPException(404, "Video not found.")
    return FileResponse(p, media_type="video/mp4", filename="lesson.mp4")
