from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import httpx

router = APIRouter()

# Basic config for Pipedrive & Reonic
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN", "YOUR_API_TOKEN_HERE")
PIPEDRIVE_COMPANY_DOMAIN = os.getenv("PIPEDRIVE_COMPANY_DOMAIN", "yourcompany")  
REONIC_API_BASE = os.getenv("REONIC_API_BASE", "http://localhost:8000") 

PIPEDRIVE_BASE_URL = f"https://{PIPEDRIVE_COMPANY_DOMAIN}.pipedrive.com/v1"

class LeadCreate(BaseModel):
    title: str
    amount: float | None = None
    currency: str | None = None
    owner_id: int | None = None
    label_ids: list[str] | None = None
    person_id: int | None = None
    organization_id: int | None = None
    expected_close_date: str | None = None  # YYYY-MM-DD
    visible_to: str | None = None
    was_seen: bool | None = None


# 1) GET /get_leads – fetch leads from Pipedrive
@router.get("/get_leads")
async def get_leads():
    """
    Fetch leads from Pipedrive using api_token authentication (mocked).

    Real-world format would be:
      GET https://{COMPANYDOMAIN}.pipedrive.com/v1/leads?api_token=APITOKEN
    """

    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    url = f"{PIPEDRIVE_BASE_URL}/leads"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    class MockResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    mock_payload = {
        "success": True,
        "data": [
            {
                "id": 101,
                "title": "Mock Lead A",
                "value": {"amount": 3000, "currency": "EUR"},
                "owner_id": 1,
                "person_id": 10,
                "organization_id": 100,
                "add_time": "2025-01-01 10:00:00",
            },
            {
                "id": 102,
                "title": "Mock Lead B",
                "value": {"amount": 5000, "currency": "USD"},
                "owner_id": 2,
                "person_id": 11,
                "organization_id": 101,
                "add_time": "2025-01-02 15:30:00",
            }
        ],
        "mock_info": {
            "would_have_called_url": url,
            "would_have_sent_params": params,
        },
    }

    resp = MockResponse(mock_payload, status_code=200)

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid JSON from mock Pipedrive")

    if resp.status_code != 200 or not data.get("success", False):
        raise HTTPException(
            status_code=resp.status_code,
            detail=data.get("error") or data.get("message") or "Pipedrive error",
        )

    return JSONResponse(content=data)

# 2) POST /create_deal – create a deal in Pipedrive
@router.post("/create_lead")
async def create_lead(body: LeadCreate):
    """
    Create a Pipedrive Lead using official Pipedrive fields (mocked).

    Real-world behavior:
      POST https://{COMPANYDOMAIN}.pipedrive.com/v1/leads?api_token=APITOKEN

    This version:
      - keeps url, params, payload structure exactly like production
      - uses a local MockResponse instead of a real HTTP call
      - keeps try/except and status_code checks
    """

    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    url = f"{PIPEDRIVE_BASE_URL}/leads"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    payload = {
        "title": body.title,
        "value": {
            "amount": body.amount,
            "currency": body.currency
        } if body.amount is not None and body.currency is not None else None,
        "owner_id": body.owner_id,
        "label_ids": body.label_ids,
        "person_id": body.person_id,
        "organization_id": body.organization_id,
        "expected_close_date": body.expected_close_date,
        "visible_to": body.visible_to,
        "was_seen": body.was_seen
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    class MockResponse:
        def __init__(self, payload, status_code=201):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    mock_body = {
        "success": True,
        "request": {
            "method": "POST",
            "endpoint": url,
            "query_params": params,
            "json_body": payload,
        },
        "data": {
            "id": 999,
            "title": payload.get("title"),
            "value": payload.get("value"),
            "owner_id": payload.get("owner_id"),
            "label_ids": payload.get("label_ids") or [],
            "person_id": payload.get("person_id"),
            "organization_id": payload.get("organization_id"),
            "expected_close_date": payload.get("expected_close_date"),
            "visible_to": payload.get("visible_to"),
            "was_seen": payload.get("was_seen"),
            "status": "new",
            "created_from": "python-mock-demo"
        }
    }

    resp = MockResponse(mock_body, status_code=201)

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid JSON from mock Pipedrive")

    if resp.status_code not in (200, 201) or not data.get("success", False):
        raise HTTPException(
            status_code=resp.status_code,
            detail=data.get("error") or data.get("message") or "Pipedrive error",
        )

    return JSONResponse(content=data, status_code=resp.status_code)


# 3) POST /sync_leads – example: Pipedrive → Reonic sync
@router.post("/sync_leads")
async def sync_leads():
    """
    Simple example of a sync flow: Pipedrive → Reonic.

    1) Fetch leads from Pipedrive.
    2) Transform to a simpler structure.
    3) POST them to a Reonic endpoint: {REONIC_API_BASE}/leads/import
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    pipedrive_url = f"{PIPEDRIVE_BASE_URL}/leads"
    pipedrive_params = {"api_token": PIPEDRIVE_API_TOKEN}

    class MockResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    pipedrive_mock_payload = {
        "success": True,
        "request": {
            "method": "GET",
            "endpoint": pipedrive_url,
            "query_params": pipedrive_params,
        },
        "data": [
            {
                "id": 101,
                "title": "Mock Lead A",
                "person_id": 10,
                "owner_id": 1,
                "add_time": "2025-01-01 10:00:00",
            },
            {
                "id": 102,
                "title": "Mock Lead B",
                "person_id": 11,
                "owner_id": 2,
                "add_time": "2025-01-02 15:30:00",
            }
        ]
    }

    pd_resp = MockResponse(pipedrive_mock_payload, status_code=200)

    try:
        leads_data = pd_resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid JSON from mock Pipedrive")

    if pd_resp.status_code != 200 or not leads_data.get("success", False):
        raise HTTPException(
            status_code=pd_resp.status_code,
            detail=leads_data.get("error") or leads_data.get("message") or "Pipedrive error",
        )

    raw_leads = leads_data.get("data", [])

    transformed_leads = []
    for lead in raw_leads:
        transformed_leads.append(
            {
                "external_id": lead.get("id"),
                "title": lead.get("title"),
                "source": "pipedrive",
                "person_id": lead.get("person_id"),
                "owner_id": lead.get("owner_id"),
                "add_time": lead.get("add_time"),
            }
        )

    reonic_url = f"{REONIC_API_BASE}/leads/import"

    reonic_mock_payload = {
        "success": True,
        "request": {
            "method": "POST",
            "endpoint": reonic_url,
            "json_body": {"leads": transformed_leads},
        },
        "imported": len(transformed_leads),
        "system": "reonic-mock",
        "note": "This is a mock import; no real HTTP request was made.",
    }

    reonic_status = 200
    reonic_body = reonic_mock_payload

    return JSONResponse(
        content={
            "pipedrive_leads_count": len(raw_leads),
            "sent_to_reonic_count": len(transformed_leads),
            "reonic_status_code": reonic_status,
            "reonic_response": reonic_body,
        }
    )
