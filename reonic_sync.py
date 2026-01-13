from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from pydantic import BaseModel
from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL,
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
router = APIRouter()

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

    payload = {
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
        "owner_id": body.owner_id,
        "reonic_technical_status": body.technical_status,
        "reonic_project_id": body.reonic_project_id,
    }

    if body.value_amount is not None:
        deal_payload["value"] = int(body.value_amount)
    if body.value_currency is not None:
        deal_payload["currency"] = body.value_currency

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

# 4) POST /pipedrive_push_leads_to_reonic – example: Pipedrive → Reonic sync
@router.post("/pipedrive_push_leads_to_reonic")
async def pipedrive_push_leads_to_reonic():
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

# 5 ) Reonic → This service: project/event webhook (Mock)
@router.post("/reonic_webhook_project_event")
async def reonic_webhook_project_event(body: ReonicWebhookEvent):
    """
    Reonic → This service: project/event webhook (Mock)

    This endpoint represents the REAL entry point in production:
    Reonic pushes events here, then we decide what to sync to Pipedrive.
    """

    # mock: just mock Reonic webhook → internal logic → push to Pipedrive
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
            "received_event": body.dict(),
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

# lookup mapping (reonic_project_id -> pipedrive_deal_id)
@router.get("/lookup_deal_id_by_reonic_project/{reonic_project_id}")
async def lookup_deal_id_by_reonic_project(reonic_project_id: str):
    """
    Demo: given a Reonic project id, return the mapped Pipedrive deal id (mocked).
    This answers: "where does deal_id come from?"
    """
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

# 6 upsert deal by reonic_project_id (lookup -> update or create)
@router.post("/upsert_deal_by_reonic_project_id")
async def upsert_deal_by_reonic_project_id(body: ReonicDealUpsert):
    """
    Demo: upsert a Pipedrive deal using reonic_project_id (mocked).

    Flow:
      1) lookup mapping by reonic_project_id
      2) if found -> PATCH /deals/{deal_id}
      3) if not found -> POST /deals then store mapping
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="Missing Pipedrive token")

    reonic_project_id = body.reonic_project_id
    existing_deal_id = REONIC_PROJECT_TO_PIPEDRIVE_DEAL.get(reonic_project_id)

    mapped_fields: Dict[str, Any] = {
        "reonic_project_id": "pipedrive_custom_field_key: cf_reonic_project_id",
        "technical_status": "pipedrive_custom_field_key: cf_reonic_technical_status (or activity.note)",
    }

    if existing_deal_id is not None:
        url = f"{PIPEDRIVE_BASE_URL}/deals/{existing_deal_id}"
        params = {"api_token": PIPEDRIVE_API_TOKEN}

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

        if body.technical_status is not None:
            payload["reonic_technical_status"] = body.technical_status
        payload["reonic_project_id"] = reonic_project_id

        payload = {k: v for k, v in payload.items() if v is not None}

        mock_body = {
            "success": True,
            "mode": "update",
            "mapping": {
                "reonic_project_id": reonic_project_id,
                "pipedrive_deal_id": existing_deal_id,
                "found": True,
            },
            "mapped_fields": mapped_fields,
            "request": {
                "method": "PATCH",
                "endpoint": url,
                "query_params": params,
                "json_body": payload,
            },
            "data": {
                "id": existing_deal_id,
                **payload,
                "updated_from": "reonic-upsert-mock",
            },
        }

        return JSONResponse(content=mock_body, status_code=200)

    url = f"{PIPEDRIVE_BASE_URL}/deals"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

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

    if body.technical_status is not None:
        create_payload["reonic_technical_status"] = body.technical_status
    create_payload["reonic_project_id"] = reonic_project_id

    create_payload = {k: v for k, v in create_payload.items() if v is not None}

    mock_body = {
        "success": True,
        "mode": "create",
        "mapping": {
            "reonic_project_id": reonic_project_id,
            "pipedrive_deal_id": new_deal_id,
            "found": False,
            "stored": True,
        },
        "mapped_fields": mapped_fields,
        "request": {
            "method": "POST",
            "endpoint": url,
            "query_params": params,
            "json_body": create_payload,
        },
        "data": {
            "id": new_deal_id,
            **create_payload,
            "created_from": "reonic-upsert-mock",
        },
    }

    return JSONResponse(content=mock_body, status_code=201)