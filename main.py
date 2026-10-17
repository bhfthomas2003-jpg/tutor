from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import S
from .routes.api import r

app = FastAPI(title="Thomas AI Math Studio", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[S.origin] if S.origin else [],
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
app.include_router(r)

@app.get("/health")
def health(): return {"ok": True}
