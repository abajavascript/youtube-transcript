"""HTTP API wrapping yt-transcript.py for Vercel (FastAPI ASGI).

Endpoints:
  GET  /api/transcript?url=<youtube-url>
  POST /api/transcript  JSON: {"url": "<youtube-url>"}

Optional env (Vercel project settings): TRANSCRIPT_API_TOKEN — if set, clients must send
header ``Authorization: Bearer <token>`` for /api/transcript.

Response shape matches the CLI: ``{"videos": [<TranscriptResult as dict>]}``.

Vercel: increase ``maxDuration`` in vercel.json if requests time out (plan tier caps apply).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Annotated

from dataclasses import asdict
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


def _load_yt_transcript_module():
    root = Path(__file__).resolve().parent
    script_path = root / "yt-transcript.py"
    if not script_path.is_file():
        raise RuntimeError(f"yt-transcript.py not found at {script_path}")
    spec = importlib.util.spec_from_file_location("_yt_transcript_internal", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load yt-transcript.py")
    mod = importlib.util.module_from_spec(spec)
    # Register before exec_module so dataclasses and similar can resolve the module dict (e.g. Python 3.14).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_yt = None


def get_yt_module():
    global _yt
    if _yt is None:
        _yt = _load_yt_transcript_module()
    return _yt


def require_api_token(request: Request) -> None:
    """If TRANSCRIPT_API_TOKEN is set, require Authorization: Bearer <token>."""
    expected = os.environ.get("TRANSCRIPT_API_TOKEN")
    if not expected:
        return
    auth = request.headers.get("Authorization") or ""
    if auth != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="unauthorized")


_auth_dep = [Depends(require_api_token)]

app = FastAPI(title="YouTube transcript API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok"}


class TranscriptBody(BaseModel):
    url: str = Field(..., min_length=1)


def _response_for_url(url: str) -> dict:
    yt = get_yt_module()
    result = yt.process_url(url.strip())
    return {"videos": [asdict(result)]}


@app.get("/api/transcript", dependencies=_auth_dep)
def transcript_get(url: Annotated[str | None, Query()] = None):
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="missing url query parameter")
    return _response_for_url(url)


@app.post("/api/transcript", dependencies=_auth_dep)
def transcript_post(body: TranscriptBody):
    return _response_for_url(body.url)
