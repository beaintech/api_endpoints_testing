from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict
from utils.helper import (
    REONIC_PROJECT_TO_PIPEDRIVE_DEAL
)

from reonic_config import (
    REONIC_WEBHOOK_SUBSCRIBE_PATH_TMPL,
    _reonic_webhook_subscribe_url,
    build_reonic_headers
)

from utils.reonic_sync_types import (
    ReonicWebhookEvent,
    ReonicDealStatusUpdate,
    ReonicActivityPayload,
    ReonicProjectUpdate,
    ReonicDealUpsert,
    ReonicWebhookSubscribePayload
) 

from utils.helper import (
    _pd_v2_url,
    _pd_headers,
    _redacted_headers,
)

from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL,
)

router = APIRouter()

# 1) Reonic → Pipedrive: Update Deal Status
@router.patch("/api/v2/deals/{deal_id}")
async def update_deal_v2_mock(
    deal_id: int = Path(..., ge=1),
    body: ReonicDealStatusUpdate = None,
):
    pd_headers = _pd_headers()

    # Remote preview URL (where you'd call Pipedrive in real HTTP mode)
    url = _pd_v2_url(f"/deals/{deal_id}")

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

    return JSONResponse(
        content={
            "success": True,
            "request": {
                "method": "PATCH",
                "endpoint": url,
                "headers": _redacted_headers(pd_headers),
                "json_body": payload,
            },
            "data": {"id": deal_id, **payload, "updated_from": "reonic-status-mock"},
            "note": "Mock preview only: no real HTTP executed.",
        },
        status_code=200,
    )

# 2) Reonic → Pipedrive: Create Activity
@router.post("/api/v2/activities")
async def reonic_push_activity_to_pipedrive(body: ReonicActivityPayload):
    pd_headers = _pd_headers()
    url = _pd_v2_url("/activities")

    payload: Dict[str, Any] = {
        "subject": body.subject,
        "type": body.type,
        "deal_id": body.deal_id,
        "person_id": body.person_id,
        "org_id": body.org_id,
        "due_date": body.due_date,
        "note": body.note,
        "reonic_project_id": body.reonic_project_id,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    mock_body = {
        "success": True,
        "request": {
            "method": "POST",
            "endpoint": url,
            "headers": _redacted_headers(pd_headers),
            "json_body": payload,
        },
        "data": {"id": 7001, **payload, "created_from": "reonic-activity-mock"},
        "note": "Mock preview only: no real HTTP executed.",
    }

    return JSONResponse(content=jsonable_encoder(mock_body), status_code=201)

# 3 ) Reonic → This service: Subscribe to webhook (Mock)
@router.post("/integrations/zapier/webhooks/{event}/subscribe")
async def subscribe_reonic_webhook(event: str, body: Dict[str, Any]):
    hook_url = body.get("hookUrl")
    return JSONResponse(
        content={
            "success": True,
            "event": event,
            "hookUrl": hook_url,
            "note": "Mock subscribe preview only.",
        },
        status_code=200,
    )

# 4) Reonic -> This service: project/event webhook (Mock)
@router.post("/api/reonic/webhook/{event}")
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
                "would_call": "/reonic/webhook/{event}",
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


# 5) lookup mapping (reonic_project_id -> pipedrive_deal_id)
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

# 7) upsert deal by reonic_project_id (lookup -> update or create)
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