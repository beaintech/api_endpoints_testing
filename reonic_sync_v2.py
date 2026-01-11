from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from pydantic import BaseModel

from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL, # e.g. "https://companydomain.pipedrive.com" 
    REONIC_API_BASE,
)

router = APIRouter()

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

class ReonicWebhookEvent(BaseModel):
    event_type: str
    reonic_project_id: str
    technical_status: Optional[str] = None
    deal_id: Optional[int] = None

#  Reonic → Pipedrive Endpoints (Deals + Activities + Project Update)
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

def _apply_reonic_fields(payload: Dict[str, Any], reonic_project_id: Optional[str], technical_status: Optional[str]) -> Dict[str, Any]:
    out = dict(payload)
    if reonic_project_id is not None:
        out["reonic_project_id"] = reonic_project_id
    if technical_status is not None:
        out["reonic_technical_status"] = technical_status
    return out

# 1) Reonic → Pipedrive: Update Deal (Mock, v2)
@router.post("/reonic_push_status_to_pipedrive")
async def reonic_push_status_to_pipedrive(body: ReonicDealStatusUpdate):
    headers = _pd_headers()
    url = _pd_v2_url(f"/deals/{body.deal_id}")

    payload: Dict[str, Any] = {
        "stage_id": body.stage_id,
        "status": body.status,
        "probability": body.probability,
        "expected_close_date": body.expected_close_date,
    }
    if body.value_amount is not None:
        payload["value"] = int(body.value_amount)
    if body.value_currency is not None:
        payload["currency"] = body.value_currency

    payload = {k: v for k, v in payload.items() if v is not None}
    payload = _apply_reonic_fields(payload, body.reonic_project_id, body.technical_status)

    mock_body = {
        "success": True,
        "request": {
            "method": "PATCH",
            "endpoint": url,
            "headers": _redacted_headers(headers),
            "json_body": payload,
        },
        "data": {"id": body.deal_id, **payload, "updated_from": "reonic-status-mock-v2"},
    }
    return JSONResponse(content=mock_body, status_code=200)

# 2) Reonic → Pipedrive: Create Activity (Mock, v2)
@router.post("/reonic_push_activity_to_pipedrive")
async def reonic_push_activity_to_pipedrive(body: ReonicActivityPayload):
    headers = _pd_headers()
    url = _pd_v2_url("/activities")

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

    if body.reonic_project_id is not None:
        note = payload.get("note") or ""
        tail = f"[reonic_project_id={body.reonic_project_id}]"
        payload["note"] = (note + "\n" + tail).strip() if note else tail

    mock_body = {
        "success": True,
        "request": {
            "method": "POST",
            "endpoint": url,
            "headers": _redacted_headers(headers),
            "json_body": payload,
        },
        "data": {"id": 7001, **payload, "created_from": "reonic-activity-mock-v2"},
    }
    return JSONResponse(content=mock_body, status_code=201)

# 3) Reonic → Pipedrive: Project Update (Deal patch + Activity create) (Mock, v2)
@router.post("/reonic_push_project_update")
async def reonic_push_project_update(body: ReonicProjectUpdate):
    headers = _pd_headers()
    deal_url = _pd_v2_url(f"/deals/{body.deal_id}")
    activity_url = _pd_v2_url("/activities")

    deal_payload: Dict[str, Any] = {
        "stage_id": body.stage_id,
        "expected_close_date": body.expected_go_live,
        "owner_id": body.owner_id,
    }
    if body.value_amount is not None:
        deal_payload["value"] = int(body.value_amount)
    if body.value_currency is not None:
        deal_payload["currency"] = body.value_currency

    deal_payload = {k: v for k, v in deal_payload.items() if v is not None}
    deal_payload = _apply_reonic_fields(deal_payload, body.reonic_project_id, body.technical_status)

    activity_payload: Dict[str, Any] = {
        "subject": f"Reonic project update: {body.technical_status}",
        "type": "task",
        "deal_id": body.deal_id,
        "due_date": body.expected_go_live,
        "note": body.progress_note or f"Technical status updated to {body.technical_status}",
    }
    activity_payload = {k: v for k, v in activity_payload.items() if v is not None}
    if body.reonic_project_id is not None:
        activity_payload["note"] = (activity_payload.get("note", "") + f"\n[reonic_project_id={body.reonic_project_id}]").strip()

    deal_mock = {
        "success": True,
        "request": {
            "method": "PATCH",
            "endpoint": deal_url,
            "headers": _redacted_headers(headers),
            "json_body": deal_payload,
        },
        "data": {"id": body.deal_id, **deal_payload, "updated_from": "reonic-project-update-mock-v2"},
    }

    activity_mock = {
        "success": True,
        "request": {
            "method": "POST",
            "endpoint": activity_url,
            "headers": _redacted_headers(headers),
            "json_body": activity_payload,
        },
        "data": {"id": 7101, **activity_payload, "created_from": "reonic-project-update-mock-v2"},
    }

    return JSONResponse(content={"deal_update": deal_mock, "activity_created": activity_mock}, status_code=200)

# 4) Pipedrive → Reonic: leads search then import (Mock, v2)
@router.post("/pipedrive_push_leads_to_reonic")
async def pipedrive_push_leads_to_reonic(term: str = "demo"):
    headers = _pd_headers()
    pipedrive_url = _pd_v2_url("/leads/search")

    pipedrive_mock_payload = {
        "success": True,
        "request": {
            "method": "GET",
            "endpoint": pipedrive_url,
            "headers": _redacted_headers(headers),
            "query_params": {"term": term, "fields": "title,notes"},
        },
        "data": {
            "items": [
                {
                    "id": "8d6b7c3a-1111-4a9b-9c9a-aaaaaaaaaaaa",
                    "title": "Mock Lead A",
                    "person_id": 10,
                    "owner_id": 1,
                    "add_time": "2025-01-01 10:00:00",
                },
                {
                    "id": "9e7c8d4b-2222-4b9c-8d8b-bbbbbbbbbbbb",
                    "title": "Mock Lead B",
                    "person_id": 11,
                    "owner_id": 2,
                    "add_time": "2025-01-02 15:30:00",
                },
            ]
        },
        "additional_data": {"next_cursor": None},
    }

    data = pipedrive_mock_payload.get("data")
    if isinstance(data, dict):
        leads_items = data.get("items", [])
    else:
        leads_items = []

    transformed_leads = []
    for lead in leads_items:
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

    reonic_url = f"{(REONIC_API_BASE or '').rstrip('/')}/leads/import"

    reonic_mock_payload = {
        "success": True,
        "request": {
            "method": "POST",
            "endpoint": reonic_url,
            "json_body": {"leads": transformed_leads},
        },
        "imported": len(transformed_leads),
        "system": "reonic-mock",
        "note": "Mock import; no real HTTP request was made.",
    }

    return JSONResponse(
        content={
            "pipedrive_search_term": term,
            "pipedrive_leads_found": len(leads_items),
            "sent_to_reonic_count": len(transformed_leads),
            "reonic_status_code": 200,
            "reonic_response": reonic_mock_payload,
        },
        status_code=200,
    )

# 5) Reonic → This service: webhook entry (Mock)
@router.post("/reonic_webhook_project_event")
async def reonic_webhook_project_event(body: ReonicWebhookEvent):
    actions = []
    if body.deal_id and body.technical_status:
        actions.append(
            {
                "would_call": "/reonic_push_project_update",
                "with": {
                    "deal_id": body.deal_id,
                    "technical_status": body.technical_status,
                    "reonic_project_id": body.reonic_project_id,
                },
            }
        )

    return JSONResponse(
        content={
            "received_event": body.model_dump(),
            "actions_planned": actions,
            "note": "Mock webhook handler. No real downstream call executed.",
        },
        status_code=200,
    )

# module-level mock mapping store (in-memory)
REONIC_PROJECT_TO_PIPEDRIVE_DEAL: Dict[str, int] = {
    "reonic_proj_demo_001": 5001,
    "reonic_proj_demo_002": 5002,
}

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
            "note": "Mock mapping lookup (in-memory dict).",
        },
        status_code=200,
    )

# 6) Upsert deal by reonic_project_id (lookup -> update or create) (Mock, v2)
@router.post("/upsert_deal_by_reonic_project_id")
async def upsert_deal_by_reonic_project_id(body: ReonicDealUpsert):
    headers = _pd_headers()

    reonic_project_id = body.reonic_project_id
    existing_deal_id = REONIC_PROJECT_TO_PIPEDRIVE_DEAL.get(reonic_project_id)

    if existing_deal_id is not None:
        url = _pd_v2_url(f"/deals/{existing_deal_id}")

        payload: Dict[str, Any] = {
            "stage_id": body.stage_id,
            "owner_id": body.owner_id,
            "person_id": body.person_id,
            "org_id": body.org_id,
            "expected_close_date": body.expected_close_date,
        }
        if body.value_amount is not None:
            payload["value"] = int(body.value_amount)
        if body.value_currency is not None:
            payload["currency"] = body.value_currency

        payload = {k: v for k, v in payload.items() if v is not None}
        payload = _apply_reonic_fields(payload, reonic_project_id, body.technical_status)

        mock_body = {
            "success": True,
            "mode": "update",
            "mapping": {
                "reonic_project_id": reonic_project_id,
                "pipedrive_deal_id": existing_deal_id,
                "found": True,
            },
            "request": {
                "method": "PATCH",
                "endpoint": url,
                "headers": _redacted_headers(headers),
                "json_body": payload,
            },
            "data": {"id": existing_deal_id, **payload, "updated_from": "reonic-upsert-mock-v2"},
        }
        return JSONResponse(content=mock_body, status_code=200)

    url = _pd_v2_url("/deals")

    new_deal_id = 9000 + len(REONIC_PROJECT_TO_PIPEDRIVE_DEAL) + 1
    REONIC_PROJECT_TO_PIPEDRIVE_DEAL[reonic_project_id] = new_deal_id

    create_payload: Dict[str, Any] = {
        "title": body.title or f"Reonic Project {reonic_project_id}",
        "stage_id": body.stage_id,
        "owner_id": body.owner_id,
        "person_id": body.person_id,
        "org_id": body.org_id,
        "expected_close_date": body.expected_close_date,
    }
    if body.value_amount is not None:
        create_payload["value"] = int(body.value_amount)
    if body.value_currency is not None:
        create_payload["currency"] = body.value_currency

    create_payload = {k: v for k, v in create_payload.items() if v is not None}
    create_payload = _apply_reonic_fields(create_payload, reonic_project_id, body.technical_status)

    mock_body = {
        "success": True,
        "mode": "create",
        "mapping": {
            "reonic_project_id": reonic_project_id,
            "pipedrive_deal_id": new_deal_id,
            "found": False,
            "stored": True,
        },
        "request": {
            "method": "POST",
            "endpoint": url,
            "headers": _redacted_headers(headers),
            "json_body": create_payload,
        },
        "data": {"id": new_deal_id, **create_payload, "created_from": "reonic-upsert-mock-v2"},
    }
    return JSONResponse(content=mock_body, status_code=201)