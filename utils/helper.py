from fastapi import HTTPException
from typing import Any, Dict, List
from pipedrive_config import PIPEDRIVE_API_TOKEN, PIPEDRIVE_BASE_URL

# Data store / mock mapping
REONIC_PROJECT_TO_PIPEDRIVE_DEAL: Dict[str, int] = {
    "reonic_proj_demo_001": 5001,
    "reonic_proj_demo_002": 5002,
}

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

def _pd_v1_params() -> Dict[str, str]:
    # v1 commonly uses api_token query param for authentication
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="Missing Pipedrive token")
    return {"api_token": PIPEDRIVE_API_TOKEN}

def _redacted_headers(headers: Dict[str, str]) -> Dict[str, str]:
    out = dict(headers)
    if "x-api-token" in out:
        out["x-api-token"] = "[REDACTED]"
    return out

def _mock_leads_found(term: str) -> List[Dict[str, Any]]:
    return [
        {
            "id": "6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3",
            "title": f"{term} Lead A",
            "value": {"amount": 3000, "currency": "EUR"},
            "owner_id": 1,
            "person_id": 10,
            "org_id": 100,
            "add_time": "2025-01-01 10:00:00",
            "source": "pipedrive",
        },
        {
            "id": "0f3a8d21-1f7b-4a7e-9f77-2df79c0c11aa",
            "title": f"{term} Lead B",
            "value": {"amount": 5000, "currency": "USD"},
            "owner_id": 2,
            "person_id": 11,
            "org_id": 101,
            "add_time": "2025-01-02 15:30:00",
            "source": "pipedrive",
        },
    ]

def _mock_reonic_create_response(lead_id: str) -> Dict[str, Any]:
    # simulate Reonic returning a created request id
    return {"id": f"reonic_req_{lead_id}"}