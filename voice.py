import hashlib, json, httpx
from fastapi import HTTPException
from ..config import S

API = "https://api.elevenlabs.io/v1"
_F = S.data / "voice.json"

def voice_id():
    if _F.exists():
        return json.loads(_F.read_text()).get("voice_id") or None
    return S.voice_id or None

def clone(name, files):
    if not S.el_key:
        raise HTTPException(503, "Voice provider not configured: set ELEVENLABS_API_KEY on the backend.")
    r = httpx.post(f"{API}/voices/add", headers={"xi-api-key": S.el_key}, timeout=180,
                   data={"name": name}, files=[("files", f) for f in files])
    if r.status_code != 200:
        raise HTTPException(502, f"Voice provider refused the samples (HTTP {r.status_code}). Instant cloning needs a plan that includes it.")
    vid = r.json().get("voice_id")
    _F.write_text(json.dumps({"voice_id": vid, "name": name}))
    return vid

def tts(text, vs):
    """Returns path to mp3. Cached by (text, voice, settings): unchanged text is never re-billed."""
    vid = voice_id()
    if not vid:
        raise HTTPException(409, "Voice not set up. Upload your own recordings in 'My AI Voice' first. No other voice is ever substituted.")
    if not S.el_key:
        raise HTTPException(503, "Voice provider not configured.")
    key = hashlib.sha256(json.dumps([text, vid, vs.model_dump()]).encode()).hexdigest()[:32]
    p = S.data / "audio" / f"{key}.mp3"
    if p.exists():
        return p
    r = httpx.post(f"{API}/text-to-speech/{vid}", timeout=180, headers={"xi-api-key": S.el_key},
        json={"text": text, "model_id": "eleven_multilingual_v2",
              "voice_settings": {"stability": vs.stability, "similarity_boost": vs.similarity, "speed": vs.speed}})
    if r.status_code != 200:
        raise HTTPException(502, f"Narration failed (HTTP {r.status_code}). Check voice ID and provider credit.")
    p.write_bytes(r.content)
    return p
