from fastapi import HTTPException
from typing import Any, Dict
from pipedrive_config import PIPEDRIVE_API_TOKEN, PIPEDRIVE_BASE_URL

def _pd_v1_url(path: str) -> str:
    base = (PIPEDRIVE_BASE_URL or "").rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}/v1{path}"

def _pd_v2_url(path: str) -> str:
    base = (PIPEDRIVE_BASE_URL or "").rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}/api/v2{path}"

def _pd_headers() -> Dict[str, str]:
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="Missing Pipedrive token")
    return {"x-api-token": PIPEDRIVE_API_TOKEN}

def _redacted_headers(headers: Dict[str, str]) -> Dict[str, str]:
    out = dict(headers)
    if "x-api-token" in out:
        out["x-api-token"] = "[REDACTED]"
    return out
    