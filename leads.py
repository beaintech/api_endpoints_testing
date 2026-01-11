from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from pydantic import BaseModel
from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL,
)

router = APIRouter()

class LeadCreate(BaseModel):
    title: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    owner_id: Optional[int] = None
    label_ids: Optional[list[str]] = None
    person_id: Optional[int] = None
    organization_id: Optional[int] = None
    expected_close_date: Optional[str] = None  # YYYY-MM-DD
    visible_to: Optional[str] = None
    was_seen: Optional[bool] = None

class LeadUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    owner_id: Optional[int] = None
    label_ids: Optional[list[str]] = None
    person_id: Optional[int] = None
    organization_id: Optional[int] = None
    expected_close_date: Optional[str] = None
    visible_to: Optional[str] = None
    was_seen: Optional[bool] = None

# 1) GET /get_leads – fetch leads from Pipedrive
@router.get("")
async def get_leads():
    """
    Fetch leads from Pipedrive using api_token authentication (mocked).
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

# GET /get_lead/{lead_id} – fetch a single lead
@router.get("/{lead_id}")
async def get_lead(lead_id: int):
    """
    Fetch a single lead from Pipedrive by ID (mocked).
    GET https://{COMPANYDOMAIN}.pipedrive.com/v1/leads/{id}?api_token=APITOKEN
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    url = f"{PIPEDRIVE_BASE_URL}/leads/{lead_id}"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    class MockResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    mock_payload = {
        "success": True,
        "request": {
            "method": "GET",
            "endpoint": url,
            "query_params": params,
        },
        "data": {
            "id": lead_id,
            "title": f"Mock Lead {lead_id}",
            "value": {"amount": 1234, "currency": "EUR"},
            "owner_id": 1,
            "person_id": 10,
            "organization_id": 100,
            "add_time": "2025-01-01 10:00:00",
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

    return JSONResponse(content=data, status_code=resp.status_code)

# 2) POST /create_lead – create a lead in Pipedrive
@router.post("")
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

# PATCH /leads/{lead_id} – update a lead
@router.patch("/{lead_id}")
async def update_lead(lead_id: int, body: LeadUpdate):
    """
    Update an existing lead in Pipedrive (mocked).

    Real-world:
      PATCH https://{COMPANYDOMAIN}.pipedrive.com/v1/leads/{id}?api_token=APITOKEN
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    url = f"{PIPEDRIVE_BASE_URL}/leads/{lead_id}"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    payload: Dict[str, Any] = {}

    if body.title is not None:
        payload["title"] = body.title
    if body.owner_id is not None:
        payload["owner_id"] = body.owner_id
    if body.label_ids is not None:
        payload["label_ids"] = body.label_ids
    if body.person_id is not None:
        payload["person_id"] = body.person_id
    if body.organization_id is not None:
        payload["organization_id"] = body.organization_id
    if body.expected_close_date is not None:
        payload["expected_close_date"] = body.expected_close_date
    if body.visible_to is not None:
        payload["visible_to"] = body.visible_to
    if body.was_seen is not None:
        payload["was_seen"] = body.was_seen

    if body.amount is not None or body.currency is not None:
        value: Dict[str, Any] = {}
        if body.amount is not None:
            value["amount"] = body.amount
        if body.currency is not None:
            value["currency"] = body.currency
        payload["value"] = value

    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update.")

    class MockResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    mock_body = {
        "success": True,
        "request": {
            "method": "PATCH",
            "endpoint": url,
            "query_params": params,
            "json_body": payload,
        },
        "data": {
            "id": lead_id,
            **payload,
            "updated_from": "python-mock-demo"
        }
    }

    resp = MockResponse(mock_body, status_code=200)

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid JSON from mock Pipedrive")

    if resp.status_code != 200 or not data.get("success", False):
        raise HTTPException(
            status_code=resp.status_code,
            detail=data.get("error") or data.get("message") or "Pipedrive error",
        )

    return JSONResponse(content=data, status_code=resp.status_code)

# DELETE /leads/{lead_id} – delete a lead
@router.delete("/{lead_id}")
async def delete_lead(lead_id: int):
    """
    Delete a lead in Pipedrive by ID (mocked).

    Real-world:
      DELETE https://{COMPANYDOMAIN}.pipedrive.com/v1/leads/{id}?api_token=APITOKEN
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    url = f"{PIPEDRIVE_BASE_URL}/leads/{lead_id}"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    class MockResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    mock_body = {
        "success": True,
        "request": {
            "method": "DELETE",
            "endpoint": url,
            "query_params": params,
        },
        "data": {
            "id": lead_id,
            "deleted": True,
        },
    }

    resp = MockResponse(mock_body, status_code=200)

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid JSON from mock Pipedrive")

    if resp.status_code != 200 or not data.get("success", False):
        raise HTTPException(
            status_code=resp.status_code,
            detail=data.get("error") or data.get("message") or "Pipedrive error",
        )

    return JSONResponse(content=data, status_code=resp.status_code)