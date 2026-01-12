from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
import httpx

from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL,   # e.g. "https://yourcompany.pipedrive.com"
    REONIC_API_BASE,      # e.g. "https://reonic.example.com"
)

router = APIRouter()

# ----------------------------
# Models
# ----------------------------
class ReonicWebhookEvent(BaseModel):
    event_type: str
    reonic_project_id: str
    technical_status: Optional[str] = None
    deal_id: Optional[int] = None


class ReonicDealStatusUpdate(BaseModel):
    deal_id: int
    stage_id: Optional[int] = None
    status: Optional[str] = None
    probability: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    expected_close_date: Optional[str] = None
    technical_status: Optional[str] = None
    reonic_project_id: Optional[str] = None


class ReonicActivityPayload(BaseModel):
    subject: str
    type: str = "task"
    deal_id: Optional[int] = None
    person_id: Optional[int] = None
    org_id: Optional[int] = None
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    duration: Optional[str] = None
    note: Optional[str] = None
    reonic_project_id: Optional[str] = None


class ReonicProjectUpdate(BaseModel):
    deal_id: int
    technical_status: str
    expected_go_live: Optional[str] = None
    progress_note: Optional[str] = None
    reonic_project_id: Optional[str] = None
    stage_id: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    owner_id: Optional[int] = None


class ReonicDealUpsert(BaseModel):
    reonic_project_id: str
    title: Optional[str] = None
    technical_status: Optional[str] = None
    stage_id: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    owner_id: Optional[int] = None
    person_id: Optional[int] = None
    org_id: Optional[int] = None
    expected_close_date: Optional[str] = None

# HTTP helpers
def _base(url: str) -> str:
    return url.rstrip("/")

def _mask_token(t: str) -> str:
    if not t:
        return ""
    if len(t) <= 8:
        return "***"
    return t[:4] + "..." + t[-4:]

def _require_pipedrive_token():
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="Missing Pipedrive token")

def pipedrive_v2_base() -> str:
    # We force v2 base here so callers only pass path like "/deals/123"
    return f"{_base(PIPEDRIVE_BASE_URL)}/api/v2"


def pipedrive_headers() -> Dict[str, str]:
    return {
        "x-api-token": PIPEDRIVE_API_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

async def http_call(
    *,
    method: str,
    base_url: str,
    path: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: float = 20.0,
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout, headers=headers) as client:
            resp = await client.request(method, path, params=params, json=json)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"HTTP request failed: {str(e)}")

    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text}

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=body)

    return {
        "status_code": resp.status_code,
        "body": body,
        "request_preview": {
            "method": method,
            "url": f"{_base(base_url)}{path}",
            "params": params,
            "json_body": json,
            "headers": ({"x-api-token": _mask_token(PIPEDRIVE_API_TOKEN)} if headers and "x-api-token" in headers else headers),
        },
    }

async def pipedrive_call(method: str, path: str, *, params=None, json=None) -> Dict[str, Any]:
    _require_pipedrive_token()
    return await http_call(
        method=method,
        base_url=pipedrive_v2_base(),
        path=path,
        headers=pipedrive_headers(),
        params=params,
        json=json,
    )

async def reonic_call(method: str, path: str, *, params=None, json=None) -> Dict[str, Any]:
    return await http_call(
        method=method,
        base_url=_base(REONIC_API_BASE),
        path=path,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        params=params,
        json=json,
    )

# In-memory mapping (still local)
REONIC_PROJECT_TO_PIPEDRIVE_DEAL: Dict[str, int] = {
    "reonic_proj_demo_001": 5001,
    "reonic_proj_demo_002": 5002,
}

# 1) Reonic → Pipedrive: Update Deal Status (REAL HTTP)
@router.post("/reonic_push_status_to_pipedrive")
async def reonic_push_status_to_pipedrive(body: ReonicDealStatusUpdate):
    payload: Dict[str, Any] = {
        "stage_id": body.stage_id,
        "status": body.status,
        "probability": body.probability,
        "expected_close_date": body.expected_close_date,
        "reonic_technical_status": body.technical_status,
        "reonic_project_id": body.reonic_project_id,
    }
    if body.value_amount is not None:
        payload["value"] = int(body.value_amount)
    if body.value_currency is not None:
        payload["currency"] = body.value_currency
    payload = {k: v for k, v in payload.items() if v is not None}

    pd = await pipedrive_call("PATCH", f"/deals/{body.deal_id}", json=payload)

    return JSONResponse(
        content={
            "success": True,
            "request": pd["request_preview"],
            "pipedrive_status_code": pd["status_code"],
            "pipedrive_response": pd["body"],
        },
        status_code=200,
    )

# 2) Reonic → Pipedrive: Create Activity (HTTP)
@router.post("/reonic_push_activity_to_pipedrive")
async def reonic_push_activity_to_pipedrive(body: ReonicActivityPayload):
    payload: Dict[str, Any] = {
        "subject": body.subject,
        "type": body.type,
        "deal_id": body.deal_id,
        "person_id": body.person_id,
        "org_id": body.org_id,
        "due_date": body.due_date,
        "due_time": body.due_time,
        "duration": body.duration,
        "note": body.note,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    pd = await pipedrive_call("POST", "/activities", json=payload)

    return JSONResponse(
        content={
            "success": True,
            "request": pd["request_preview"],
            "pipedrive_status_code": pd["status_code"],
            "pipedrive_response": pd["body"],
        },
        status_code=200,
    )

# 3) Reonic → Pipedrive: Combined Project Update (HTTP)
@router.post("/reonic_push_project_update")
async def reonic_push_project_update(body: ReonicProjectUpdate):
    deal_payload: Dict[str, Any] = {
        "stage_id": body.stage_id,
        "expected_close_date": body.expected_go_live,
        "owner_id": body.owner_id,
        "reonic_technical_status": body.technical_status,
        "reonic_project_id": body.reonic_project_id,
    }
    if body.value_amount is not None:
        deal_payload["value"] = int(body.value_amount)
    if body.value_currency is not None:
        deal_payload["currency"] = body.value_currency
    deal_payload = {k: v for k, v in deal_payload.items() if v is not None}

    activity_payload: Dict[str, Any] = {
        "subject": f"Reonic project update: {body.technical_status}",
        "type": "task",
        "deal_id": body.deal_id,
        "due_date": body.expected_go_live,
        "note": body.progress_note or f"Technical status updated to {body.technical_status}",
    }
    activity_payload = {k: v for k, v in activity_payload.items() if v is not None}

    deal_resp = await pipedrive_call("PATCH", f"/deals/{body.deal_id}", json=deal_payload)
    act_resp = await pipedrive_call("POST", "/activities", json=activity_payload)

    return JSONResponse(
        content={
            "deal_update": {
                "request": deal_resp["request_preview"],
                "status_code": deal_resp["status_code"],
                "response": deal_resp["body"],
            },
            "activity_created": {
                "request": act_resp["request_preview"],
                "status_code": act_resp["status_code"],
                "response": act_resp["body"],
            },
        },
        status_code=200,
    )

# 4) Pipedrive → Reonic leads sync (REAL HTTP)
# Uses v2 leads search: GET /api/v2/leads/search?term=...
@router.post("/pipedrive_push_leads_to_reonic")
async def pipedrive_push_leads_to_reonic(term: str = Query(..., min_length=1)):
    pd = await pipedrive_call("GET", "/leads/search", params={"term": term})

    # Real payload shape depends on Pipedrive response.
    # Keep this tolerant: if "data" is list, use it; else if nested, adapt later.
    raw = pd["body"].get("data") or []
    if not isinstance(raw, list):
        raw = []

    transformed = []
    for lead in raw:
        transformed.append(
            {
                "external_id": lead.get("id"),      # v2 lead id tends to be uuid string
                "title": lead.get("title"),
                "source": "pipedrive",
                "person_id": lead.get("person_id"),
                "owner_id": lead.get("owner_id"),
                "add_time": lead.get("add_time"),
            }
        )

    re = await reonic_call("POST", "/leads/import", json={"leads": transformed})

    return JSONResponse(
        content={
            "pipedrive_request": pd["request_preview"],
            "pipedrive_status_code": pd["status_code"],
            "pipedrive_response": pd["body"],
            "sent_to_reonic_count": len(transformed),
            "reonic_request": re["request_preview"],
            "reonic_status_code": re["status_code"],
            "reonic_response": re["body"],
        },
        status_code=200,
    )

# 5) Reonic → This service: webhook (REAL downstream call)
# Instead of returning "would_call", it actually triggers your internal logic
# by directly calling the same code path (no HTTP loopback needed).

@router.post("/reonic_webhook_project_event")
async def reonic_webhook_project_event(body: ReonicWebhookEvent):
    actions = []
    executed = None

    if body.deal_id and body.technical_status:
        actions.append(
            {
                "will_execute": "reonic_push_project_update",
                "with": {
                    "deal_id": body.deal_id,
                    "technical_status": body.technical_status,
                    "reonic_project_id": body.reonic_project_id,
                },
            }
        )

        # Execute directly (no local HTTP call)
        executed = await reonic_push_project_update(
            ReonicProjectUpdate(
                deal_id=body.deal_id,
                technical_status=body.technical_status,
                reonic_project_id=body.reonic_project_id,
            )
        )

    return JSONResponse(
        content={
            "received_event": body.dict(),
            "actions_planned": actions,
            "executed": (executed.body.decode("utf-8") if executed else None),
        },
        status_code=200,
    )

# lookup mapping (still local)
@router.get("/lookup_deal_id_by_reonic_project/{reonic_project_id}")
async def lookup_deal_id_by_reonic_project(reonic_project_id: str):
    deal_id = REONIC_PROJECT_TO_PIPEDRIVE_DEAL.get(reonic_project_id)
    return JSONResponse(
        content={
            "success": True,
            "data": {
                "reonic_project_id": reonic_project_id,
                "pipedrive_deal_id": deal_id,
                "found": deal_id is not None,
            },
        },
        status_code=200,
    )

# 6) Upsert deal by reonic_project_id (REAL HTTP)
# update -> PATCH /api/v2/deals/{id}
# create -> POST /api/v2/deals
# mapping store stays in-memory for demo
@router.post("/upsert_deal_by_reonic_project_id")
async def upsert_deal_by_reonic_project_id(body: ReonicDealUpsert):
    _require_pipedrive_token()

    reonic_project_id = body.reonic_project_id
    existing_deal_id = REONIC_PROJECT_TO_PIPEDRIVE_DEAL.get(reonic_project_id)

    if existing_deal_id is not None:
        payload: Dict[str, Any] = {
            "stage_id": body.stage_id,
            "owner_id": body.owner_id,
            "person_id": body.person_id,
            "org_id": body.org_id,
            "expected_close_date": body.expected_close_date,
            "reonic_project_id": reonic_project_id,
        }
        if body.value_amount is not None:
            payload["value"] = int(body.value_amount)
        if body.value_currency is not None:
            payload["currency"] = body.value_currency
        if body.technical_status is not None:
            payload["reonic_technical_status"] = body.technical_status

        payload = {k: v for k, v in payload.items() if v is not None}

        pd = await pipedrive_call("PATCH", f"/deals/{existing_deal_id}", json=payload)

        return JSONResponse(
            content={
                "success": True,
                "mode": "update",
                "mapping": {
                    "reonic_project_id": reonic_project_id,
                    "pipedrive_deal_id": existing_deal_id,
                    "found": True,
                },
                "request": pd["request_preview"],
                "pipedrive_status_code": pd["status_code"],
                "pipedrive_response": pd["body"],
            },
            status_code=200,
        )

    create_payload: Dict[str, Any] = {
        "title": body.title or f"Reonic Project {reonic_project_id}",
        "stage_id": body.stage_id,
        "owner_id": body.owner_id,
        "person_id": body.person_id,
        "org_id": body.org_id,
        "expected_close_date": body.expected_close_date,
        "reonic_project_id": reonic_project_id,
    }
    if body.value_amount is not None:
        create_payload["value"] = int(body.value_amount)
    if body.value_currency is not None:
        create_payload["currency"] = body.value_currency
    if body.technical_status is not None:
        create_payload["reonic_technical_status"] = body.technical_status

    create_payload = {k: v for k, v in create_payload.items() if v is not None}

    pd = await pipedrive_call("POST", "/deals", json=create_payload)

    # store mapping (demo)
    # Real world: you'd store this in DB (e.g. SQLite, etc.)
    new_id = None
    if isinstance(pd["body"], dict):
        # if pd["body"]["data"]["id"] exists, take it
        data = pd["body"].get("data") if isinstance(pd["body"].get("data"), dict) else None
        if data and "id" in data:
            new_id = data["id"]
    if isinstance(new_id, int):
        REONIC_PROJECT_TO_PIPEDRIVE_DEAL[reonic_project_id] = new_id

    return JSONResponse(
        content={
            "success": True,
            "mode": "create",
            "mapping": {
                "reonic_project_id": reonic_project_id,
                "pipedrive_deal_id": new_id,
                "found": False,
                "stored": isinstance(new_id, int),
            },
            "request": pd["request_preview"],
            "pipedrive_status_code": pd["status_code"],
            "pipedrive_response": pd["body"],
        },
        status_code=201,
    )
