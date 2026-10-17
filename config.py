import os
from pathlib import Path
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass

class S:
    app_token = os.environ.get("APP_TOKEN", "")
    origin = os.environ.get("ALLOWED_ORIGIN", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    el_key = os.environ.get("ELEVENLABS_API_KEY", "")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "")
    max_upload = int(os.environ.get("MAX_UPLOAD_MB", "20")) * 1024 * 1024
    data = Path(os.environ.get("DATA_DIR", "./data"))

for d in ("audio", "jobs", "videos", "samples"):
    (S.data / d).mkdir(parents=True, exist_ok=True)
