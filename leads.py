from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from pydantic import BaseModel

from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL,  # e.g. "https://companydomain.pipedrive.com"
)

router = APIRouter()

def _pd_v1_url(path: str) -> str:
    """
    API v1 base:
      {BASE}/v1/...
    """
    base = (PIPEDRIVE_BASE_URL or "").rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}/v1{path}"

def _pd_v2_url(path: str) -> str:
    """
    API v2 base:
      {BASE}/api/v2/...
    (Only needed for endpoints that are truly v2, e.g. leads search)
    """
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

# 1) GET /get_leads – fetch leads from Pipedrive (Mock, v1)
@router.get("")
async def get_leads():
    """
    Mocked: GET /v1/leads
    Auth: x-api-token header (your demo choice)
    """
    headers = _pd_headers()
    url = _pd_v1_url("/leads")

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
            "headers": _redacted_headers(headers),
        },
        "data": [
            {
                "id": "55ebb4c0-536e-11ea-87d0-d1171b17f6a0",
                "title": "Mock Lead A",
                "value": {"amount": 3000, "currency": "EUR"},
                "owner_id": 1,
                "person_id": 10,
                "organization_id": 100,
                "add_time": "2025-01-01 10:00:00",
            },
            {
                "id": "9e7c8d4b-2222-4b9c-8d8b-bbbbbbbbbbbb",
                "title": "Mock Lead B",
                "value": {"amount": 5000, "currency": "USD"},
                "owner_id": 2,
                "person_id": 11,
                "organization_id": 101,
                "add_time": "2025-01-02 15:30:00",
            },
        ],
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

# GET /get_lead/{lead_id} – fetch a single lead (Mock, v1)
@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    """
    Mocked: GET /v1/leads/{id}
    lead_id: uuid string
    Auth: x-api-token header (your demo choice)
    """
    headers = _pd_headers()
    url = _pd_v1_url(f"/leads/{lead_id}")

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
            "headers": _redacted_headers(headers),
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

# 2) POST /create_lead – create a lead (Mock, v1)
@router.post("")
async def create_lead(body: LeadCreate):
    """
    Mocked: POST /v1/leads
    Auth: x-api-token header (your demo choice)
    """
    headers = _pd_headers()
    url = _pd_v1_url("/leads")

    payload = {
        "title": body.title,
        "value": {
            "amount": body.amount,
            "currency": body.currency,
        } if body.amount is not None and body.currency is not None else None,
        "owner_id": body.owner_id,
        "label_ids": body.label_ids,
        "person_id": body.person_id,
        "organization_id": body.organization_id,
        "expected_close_date": body.expected_close_date,
        "visible_to": body.visible_to,
        "was_seen": body.was_seen,
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
            "headers": _redacted_headers(headers),
            "json_body": payload,
        },
        "data": {
            "id": "8d6b7c3a-1111-4a9b-9c9a-aaaaaaaaaaaa",
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
            "created_from": "python-mock-demo-v1",
        },
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

# PATCH /leads/{lead_id} – update a lead (Mock, v1)
@router.patch("/{lead_id}")
async def update_lead(lead_id: str, body: LeadUpdate):
    """
    Mocked: PATCH /v1/leads/{id}
    Auth: x-api-token header (your demo choice)
    """
    headers = _pd_headers()
    url = _pd_v1_url(f"/leads/{lead_id}")

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
            "headers": _redacted_headers(headers),
            "json_body": payload,
        },
        "data": {
            "id": lead_id,
            **payload,
            "updated_from": "python-mock-demo-v1",
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

# DELETE /leads/{lead_id} – delete a lead (Mock, v1)
@router.delete("/{lead_id}")
async def delete_lead(lead_id: str):
    """
    Mocked: DELETE /v1/leads/{id}
    Auth: x-api-token header (your demo choice)
    """
    headers = _pd_headers()
    url = _pd_v1_url(f"/leads/{lead_id}")

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
            "headers": _redacted_headers(headers),
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