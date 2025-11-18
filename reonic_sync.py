import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from pydantic import BaseModel

router = APIRouter()

# Basic config for Pipedrive & Reonic
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN", "YOUR_API_TOKEN_HERE")
PIPEDRIVE_COMPANY_DOMAIN = os.getenv("PIPEDRIVE_COMPANY_DOMAIN", "yourcompany")  
REONIC_API_BASE = os.getenv("REONIC_API_BASE", "http://localhost:8000") 

PIPEDRIVE_BASE_URL = f"https://{PIPEDRIVE_COMPANY_DOMAIN}.pipedrive.com/v1"

#  Reonic → Pipedrive Endpoints (Deals + Activities + Project Update)
class ReonicDealStatusUpdate(BaseModel):
    deal_id: int
    stage_id: int | None = None
    status: str | None = None
    probability: int | None = None
    value_amount: float | None = None
    value_currency: str | None = None
    expected_close_date: str | None = None
    technical_status: str | None = None
    reonic_project_id: str | None = None


class ReonicActivityPayload(BaseModel):
    subject: str
    type: str = "task"
    deal_id: int | None = None
    person_id: int | None = None
    org_id: int | None = None
    due_date: str | None = None
    due_time: str | None = None
    duration: str | None = None
    note: str | None = None
    reonic_project_id: str | None = None


class ReonicProjectUpdate(BaseModel):
    deal_id: int
    technical_status: str
    expected_go_live: str | None = None
    progress_note: str | None = None
    reonic_project_id: str | None = None
    stage_id: int | None = None
    value_amount: float | None = None
    value_currency: str | None = None
    owner_id: int | None = None

# 1) Reonic → Pipedrive: Update Deal Status
@router.post("/reonic_push_status_to_pipedrive")
async def reonic_push_status_to_pipedrive(body: ReonicDealStatusUpdate):
    """
    Reonic → Pipedrive: Update an existing deal (Mock).
    Pipedrive: PATCH /deals/{id}
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="Missing Pipedrive token")

    url = f"{PIPEDRIVE_BASE_URL}/deals/{body.deal_id}"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    value_block = None
    if body.value_amount is not None and body.value_currency is not None:
        value_block = {
            "amount": body.value_amount,
            "currency": body.value_currency,
        }

    payload = {
        "stage_id": body.stage_id,
        "status": body.status,
        "probability": body.probability,
        "value": value_block,
        "expected_close_date": body.expected_close_date,
        "reonic_technical_status": body.technical_status,
        "reonic_project_id": body.reonic_project_id,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    class MockResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    mock_body = {
        "success": True,
        "request": {"method": "PATCH", "endpoint": url, "query_params": params, "json_body": payload},
        "data": {"id": body.deal_id, **payload, "updated_from": "reonic-status-mock"},
    }

    resp = MockResponse(mock_body, status_code=200)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)

# 2) Reonic → Pipedrive: Create Activity
@router.post("/reonic_push_activity_to_pipedrive")
async def reonic_push_activity_to_pipedrive(body: ReonicActivityPayload):
    """
    Reonic → Pipedrive: Create an Activity (Mock)
    Pipedrive: POST /activities
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="Missing Pipedrive token")

    url = f"{PIPEDRIVE_BASE_URL}/activities"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    payload = {
        "subject": body.subject,
        "type": body.type,
        "deal_id": body.deal_id,
        "person_id": body.person_id,
        "org_id": body.org_id,
        "due_date": body.due_date,
        "due_time": body.due_time,
        "duration": body.duration,
        "note": body.note,
        "reonic_project_id": body.reonic_project_id,
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
        "request": {"method": "POST", "endpoint": url, "query_params": params, "json_body": payload},
        "data": {"id": 7001, **payload, "created_from": "reonic-activity-mock"},
    }

    resp = MockResponse(mock_body, status_code=201)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)

# 3) Reonic → Pipedrive: Combined Project Deal + Create Activity
@router.post("/reonic_push_project_update")
async def reonic_push_project_update(body: ReonicProjectUpdate):
    """
    Reonic → Pipedrive: Project Update (Mock)
    1) Update Deal technical status / stage / value
    2) Create an Activity for the update
    """

    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="Missing Pipedrive token")

    deal_url = f"{PIPEDRIVE_BASE_URL}/deals/{body.deal_id}"
    activity_url = f"{PIPEDRIVE_BASE_URL}/activities"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    # Deal update payload
    deal_payload = {
        "stage_id": body.stage_id,
        "expected_close_date": body.expected_go_live,
        "value": (
            {"amount": body.value_amount, "currency": body.value_currency}
            if body.value_amount is not None and body.value_currency is not None
            else None
        ),
        "owner_id": body.owner_id,
        "reonic_technical_status": body.technical_status,
        "reonic_project_id": body.reonic_project_id,
    }
    deal_payload = {k: v for k, v in deal_payload.items() if v is not None}

    # Activity payload
    activity_payload = {
        "subject": f"Reonic project update: {body.technical_status}",
        "type": "task",
        "deal_id": body.deal_id,
        "due_date": body.expected_go_live,
        "note": body.progress_note or f"Technical status updated to {body.technical_status}",
        "reonic_project_id": body.reonic_project_id,
    }
    activity_payload = {k: v for k, v in activity_payload.items() if v is not None}

    class MockResponse:
        def __init__(self, payload, status_code):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    deal_mock = {
        "success": True,
        "request": {"method": "PATCH", "endpoint": deal_url, "query_params": params, "json_body": deal_payload},
        "data": {"id": body.deal_id, **deal_payload, "updated_from": "reonic-project-update-mock"},
    }

    activity_mock = {
        "success": True,
        "request": {"method": "POST", "endpoint": activity_url, "query_params": params, "json_body": activity_payload},
        "data": {"id": 7101, **activity_payload, "created_from": "reonic-project-update-mock"},
    }

    return JSONResponse(
        content={"deal_update": deal_mock, "activity_created": activity_mock},
        status_code=200,
    )
