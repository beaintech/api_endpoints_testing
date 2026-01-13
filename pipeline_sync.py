from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pipedrive_config import PIPEDRIVE_API_TOKEN, PIPEDRIVE_BASE_URL

router = APIRouter()

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


REONIC_PROJECT_TO_PIPEDRIVE_DEAL: Dict[str, int] = {
    "reonic_proj_demo_001": 5001,
    "reonic_proj_demo_002": 5002,
}

def _mock_leads_found(term: str) -> List[Dict[str, Any]]:
    # lead_id is UUID string (v2 search returns leads with UUID ids in your demo contract)
    return [
        {
            "id": "6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3",
            "title": f"{term} Lead A",
            "value": {"amount": 3000, "currency": "EUR"},
            "owner_id": 1,
            "person_id": 10,
            "organization_id": 100,
            "add_time": "2025-01-01 10:00:00",
            "source": "pipedrive",
        },
        {
            "id": "0f3a8d21-1f7b-4a7e-9f77-2df79c0c11aa",
            "title": f"{term} Lead B",
            "value": {"amount": 5000, "currency": "USD"},
            "owner_id": 2,
            "person_id": 11,
            "organization_id": 101,
            "add_time": "2025-01-02 15:30:00",
            "source": "pipedrive",
        },
    ]


class ReonicProjectEvent(BaseModel):
    event_type: str
    reonic_project_id: str
    technical_status: Optional[str] = None
    deal_id: Optional[int] = None


class PushDealStatus(BaseModel):
    deal_id: int
    stage_id: Optional[int] = None
    status: Optional[str] = None
    probability: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    expected_close_date: Optional[str] = None  # YYYY-MM-DD
    technical_status: Optional[str] = None
    reonic_project_id: Optional[str] = None


class PushActivity(BaseModel):
    subject: str
    type: Optional[str] = "task"
    deal_id: Optional[int] = None
    person_id: Optional[int] = None
    organization_id: Optional[int] = None
    due_date: Optional[str] = None  # YYYY-MM-DD
    note: Optional[str] = None
    reonic_project_id: Optional[str] = None


class PushProjectUpdate(BaseModel):
    deal_id: int
    technical_status: Optional[str] = None
    expected_go_live: Optional[str] = None  # YYYY-MM-DD (your business field)
    progress_note: Optional[str] = None
    reonic_project_id: Optional[str] = None
    stage_id: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    owner_id: Optional[int] = None


class UpsertDealByReonicProject(BaseModel):
    reonic_project_id: str
    title: str
    technical_status: Optional[str] = None
    stage_id: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    expected_close_date: Optional[str] = None  # YYYY-MM-DD


def _build_deal_patch_payload(body: PushDealStatus) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if body.stage_id is not None:
        payload["stage_id"] = body.stage_id
    if body.status is not None:
        payload["status"] = body.status
    if body.probability is not None:
        payload["probability"] = body.probability
    if body.expected_close_date is not None:
        payload["expected_close_date"] = body.expected_close_date
    if body.value_amount is not None or body.value_currency is not None:
        value: Dict[str, Any] = {}
        if body.value_amount is not None:
            value["amount"] = body.value_amount
        if body.value_currency is not None:
            value["currency"] = body.value_currency
        payload["value"] = value
    if body.technical_status is not None:
        payload["reonic_technical_status"] = body.technical_status
    if body.reonic_project_id is not None:
        payload["reonic_project_id"] = body.reonic_project_id
    return payload


def _build_activity_create_payload(body: PushActivity) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "subject": body.subject,
    }
    if body.type is not None:
        payload["type"] = body.type
    if body.deal_id is not None:
        payload["deal_id"] = body.deal_id
    if body.person_id is not None:
        payload["person_id"] = body.person_id
    if body.organization_id is not None:
        payload["org_id"] = body.organization_id
    if body.due_date is not None:
        payload["due_date"] = body.due_date

    note = body.note or ""
    if body.reonic_project_id:
        tag = f"[reonic_project_id:{body.reonic_project_id}]"
        note = (note + "\n" + tag).strip() if note else tag
    if note:
        payload["note"] = note

    return payload


@router.post("/sync/pipedrive-to-reonic/leads")
async def sync_leads_pipedrive_to_reonic(
    term: str = Query("solar"),
    limit: int = Query(2, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    match: str = Query("middle"),  # v2 search supports match styles; you expose it in mock
):
    headers = _pd_headers()
    search_url = _pd_v2_url("/leads/search")

    found = _mock_leads_found(term)[:limit]

    reonic_payload = [
        {
            "external_id": lead["id"],
            "title": lead["title"],
            "source": "pipedrive",
            "person_id": lead.get("person_id"),
            "owner_id": lead.get("owner_id"),
            "add_time": lead.get("add_time"),
        }
        for lead in found
    ]

    request_preview = {
        "pipedrive_search": {
            "method": "GET",
            "endpoint": search_url,
            "headers": _redacted_headers(headers),
            "query": {"term": term, "limit": limit, "cursor": cursor, "match": match},
        },
        "reonic_receiver": {
            "method": "POST",
            "endpoint": "{REONIC_API_BASE}/{REONIC_IMPORT_PATH}",
            "json_body": reonic_payload,
        },
    }

    return JSONResponse(
        content={
            "success": True,
            "request": request_preview,
            "data": {
                "pipedrive_found": found,
                "reonic_transformed": reonic_payload,
                "reonic_mock_response": {"imported": len(reonic_payload)},
                "next_cursor": "mock_cursor_1" if cursor is None else None,
            },
        },
        status_code=200,
    )


@router.post("/sync/reonic-to-pipedrive/projects")
async def sync_projects_reonic_to_pipedrive():
    headers = _pd_headers()
    deal_patch_url = lambda deal_id: _pd_v2_url(f"/deals/{deal_id}")

    mocked_reonic_projects = [
        {
            "reonic_project_id": "reonic_proj_demo_001",
            "deal_id": 5001,
            "technical_status": "READY_FOR_INSTALL",
            "stage_id": 12,
            "value_amount": 12000,
            "value_currency": "EUR",
            "expected_close_date": "2026-02-15",
        },
        {
            "reonic_project_id": "reonic_proj_demo_002",
            "deal_id": 5002,
            "technical_status": "IN_PROGRESS",
            "stage_id": 14,
            "value_amount": 15500,
            "value_currency": "EUR",
            "expected_close_date": "2026-03-01",
        },
    ]

    previews = []
    for p in mocked_reonic_projects:
        body = PushDealStatus(
            deal_id=p["deal_id"],
            stage_id=p["stage_id"],
            status="open",
            probability=60,
            value_amount=p["value_amount"],
            value_currency=p["value_currency"],
            expected_close_date=p["expected_close_date"],
            technical_status=p["technical_status"],
            reonic_project_id=p["reonic_project_id"],
        )
        payload = _build_deal_patch_payload(body)
        previews.append(
            {
                "method": "PATCH",
                "endpoint": deal_patch_url(body.deal_id),
                "headers": _redacted_headers(headers),
                "json_body": payload,
            }
        )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "reonic_projects": mocked_reonic_projects,
                "pipedrive_requests_planned": previews,
            },
        },
        status_code=200,
    )


@router.post("/sync/reonic-to-pipedrive/products")
async def sync_products_reonic_to_pipedrive():
    headers = _pd_headers()
    product_create_url = _pd_v2_url("/products")

    mocked_reonic_products = [
        {"sku": "PRD-001", "name": "Solar Panel A", "price": 120, "currency": "EUR"},
        {"sku": "PRD-002", "name": "Inverter B", "price": 560, "currency": "EUR"},
    ]

    pipedrive_payloads = []
    for pr in mocked_reonic_products:
        pipedrive_payloads.append(
            {
                "name": pr["name"],
                "code": pr["sku"],
                "prices": [{"price": pr["price"], "currency": pr["currency"]}],
            }
        )

    return JSONResponse(
        content={
            "success": True,
            "request": {
                "method": "POST",
                "endpoint": product_create_url,
                "headers": _redacted_headers(headers),
                "json_body": pipedrive_payloads,
            },
            "data": {
                "reonic_products": mocked_reonic_products,
                "pipedrive_products_payload": pipedrive_payloads,
            },
        },
        status_code=200,
    )


@router.post("/reonic_push_status_to_pipedrive")
async def reonic_push_status_to_pipedrive(body: PushDealStatus):
    headers = _pd_headers()
    url = _pd_v2_url(f"/deals/{body.deal_id}")
    payload = _build_deal_patch_payload(body)

    return JSONResponse(
        content={
            "success": True,
            "request": {
                "method": "PATCH",
                "endpoint": url,
                "headers": _redacted_headers(headers),
                "json_body": payload,
            },
            "data": {"deal_id": body.deal_id, **payload, "updated_from": "python-mock-demo-v2"},
        },
        status_code=200,
    )


@router.post("/reonic_push_activity_to_pipedrive")
async def reonic_push_activity_to_pipedrive(body: PushActivity):
    headers = _pd_headers()
    url = _pd_v2_url("/activities")
    payload = _build_activity_create_payload(body)

    return JSONResponse(
        content={
            "success": True,
            "request": {
                "method": "POST",
                "endpoint": url,
                "headers": _redacted_headers(headers),
                "json_body": payload,
            },
            "data": {
                "id": 90001,
                **payload,
                "created_from": "python-mock-demo-v2",
            },
        },
        status_code=201,
    )


@router.post("/reonic_push_project_update")
async def reonic_push_project_update(body: PushProjectUpdate):
    headers = _pd_headers()

    deal_url = _pd_v2_url(f"/deals/{body.deal_id}")
    activity_url = _pd_v2_url("/activities")

    deal_patch = PushDealStatus(
        deal_id=body.deal_id,
        stage_id=body.stage_id,
        status="open",
        probability=60,
        value_amount=body.value_amount,
        value_currency=body.value_currency,
        expected_close_date=body.expected_go_live,  # if you want; or keep separate
        technical_status=body.technical_status,
        reonic_project_id=body.reonic_project_id,
    )
    deal_payload = _build_deal_patch_payload(deal_patch)

    act = PushActivity(
        subject="Project update",
        type="task",
        deal_id=body.deal_id,
        due_date=body.expected_go_live,
        note=body.progress_note or "",
        reonic_project_id=body.reonic_project_id,
    )
    act_payload = _build_activity_create_payload(act)

    return JSONResponse(
        content={
            "success": True,
            "deal_update": {
                "request": {
                    "method": "PATCH",
                    "endpoint": deal_url,
                    "headers": _redacted_headers(headers),
                    "json_body": deal_payload,
                },
                "data": {"deal_id": body.deal_id, **deal_payload},
            },
            "activity_created": {
                "request": {
                    "method": "POST",
                    "endpoint": activity_url,
                    "headers": _redacted_headers(headers),
                    "json_body": act_payload,
                },
                "data": {"id": 90002, **act_payload},
            },
        },
        status_code=200,
    )


@router.post("/pipedrive_push_leads_to_reonic")
async def pipedrive_push_leads_to_reonic(
    term: str = Query(...),
    limit: int = Query(2, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    match: str = Query("middle"),
):
    headers = _pd_headers()
    url = _pd_v2_url("/leads/search")

    found = _mock_leads_found(term)[:limit]

    reonic_import = [
        {
            "external_id": lead["id"],
            "title": lead["title"],
            "source": "pipedrive",
            "person_id": lead.get("person_id"),
            "owner_id": lead.get("owner_id"),
            "add_time": lead.get("add_time"),
        }
        for lead in found
    ]

    return JSONResponse(
        content={
            "success": True,
            "request": {
                "pipedrive_search": {
                    "method": "GET",
                    "endpoint": url,
                    "headers": _redacted_headers(headers),
                    "query": {"term": term, "limit": limit, "cursor": cursor, "match": match},
                },
                "reonic_receiver": {
                    "method": "POST",
                    "endpoint": "{REONIC_API_BASE}/{REONIC_IMPORT_PATH}",
                    "json_body": reonic_import,
                },
            },
            "data": {
                "pipedrive_found": found,
                "reonic_transformed": reonic_import,
                "reonic_mock_response": {"imported": len(reonic_import)},
                "next_cursor": "mock_cursor_1" if cursor is None else None,
            },
        },
        status_code=200,
    )


@router.post("/reonic_webhook_project_event")
async def reonic_webhook_project_event(body: ReonicProjectEvent):
    planned = []

    deal_id = body.deal_id
    if deal_id is None and body.reonic_project_id in REONIC_PROJECT_TO_PIPEDRIVE_DEAL:
        deal_id = REONIC_PROJECT_TO_PIPEDRIVE_DEAL[body.reonic_project_id]

    if deal_id is not None and body.technical_status is not None:
        planned.append(
            {
                "local_endpoint": "/reonic_push_status_to_pipedrive",
                "body": {
                    "deal_id": deal_id,
                    "technical_status": body.technical_status,
                    "reonic_project_id": body.reonic_project_id,
                },
            }
        )
        planned.append(
            {
                "local_endpoint": "/reonic_push_activity_to_pipedrive",
                "body": {
                    "subject": f"Reonic event: {body.event_type}",
                    "deal_id": deal_id,
                    "note": f"technical_status={body.technical_status}",
                    "reonic_project_id": body.reonic_project_id,
                },
            }
        )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "received": body.model_dump(),
                "deal_id_resolved": deal_id,
                "actions_planned": planned,
            },
        },
        status_code=200,
    )


@router.get("/lookup_deal_id_by_reonic_project/{reonic_project_id}")
async def lookup_deal_id_by_reonic_project(reonic_project_id: str):
    deal_id = REONIC_PROJECT_TO_PIPEDRIVE_DEAL.get(reonic_project_id)
    return JSONResponse(
        content={"success": True, "data": {"reonic_project_id": reonic_project_id, "deal_id": deal_id}},
        status_code=200,
    )


@router.post("/upsert_deal_by_reonic_project_id")
async def upsert_deal_by_reonic_project_id(body: UpsertDealByReonicProject):
    headers = _pd_headers()

    existing = REONIC_PROJECT_TO_PIPEDRIVE_DEAL.get(body.reonic_project_id)
    if existing is not None:
        url = _pd_v2_url(f"/deals/{existing}")
        payload = {
            "title": body.title,
            "stage_id": body.stage_id,
            "expected_close_date": body.expected_close_date,
            "reonic_project_id": body.reonic_project_id,
            "reonic_technical_status": body.technical_status,
            "value": {"amount": body.value_amount, "currency": body.value_currency}
            if body.value_amount is not None or body.value_currency is not None
            else None,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        return JSONResponse(
            content={
                "success": True,
                "path": "update",
                "request": {
                    "method": "PATCH",
                    "endpoint": url,
                    "headers": _redacted_headers(headers),
                    "json_body": payload,
                },
                "data": {"deal_id": existing, **payload},
            },
            status_code=200,
        )

    new_deal_id = max(REONIC_PROJECT_TO_PIPEDRIVE_DEAL.values(), default=5000) + 1
    REONIC_PROJECT_TO_PIPEDRIVE_DEAL[body.reonic_project_id] = new_deal_id

    url = _pd_v2_url("/deals")
    payload = {
        "title": body.title,
        "stage_id": body.stage_id,
        "expected_close_date": body.expected_close_date,
        "reonic_project_id": body.reonic_project_id,
        "reonic_technical_status": body.technical_status,
        "value": {"amount": body.value_amount, "currency": body.value_currency}
        if body.value_amount is not None or body.value_currency is not None
        else None,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    return JSONResponse(
        content={
            "success": True,
            "path": "create",
            "request": {
                "method": "POST",
                "endpoint": url,
                "headers": _redacted_headers(headers),
                "json_body": payload,
            },
            "data": {"deal_id": new_deal_id, **payload},
        },
        status_code=201,
    )
