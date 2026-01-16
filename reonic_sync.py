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

# 4) Reonic -> This service: project/event webhook (Mock)  + CLOSED LOOP PREVIEW
@router.post("/api/reonic/webhook/{event}")
async def reonic_webhook_project_event(event: str, body: ReonicWebhookEvent):
    """
    Reonic -> This service (inbound webhook)
    Then -> Pipedrive (outbound preview): PATCH deal + POST activity
    """

    pd_headers = _pd_headers()

    # If webhook doesn't contain the minimum linking fields, just echo it back.
    if not body.deal_id or not body.technical_status:
        return JSONResponse(
            content={
                "success": True,
                "event": event,
                "received_event": body.dict(),
                "pipedrive_actions": [],
                "note": "Webhook received, but no deal_id/technical_status provided, so no downstream preview built.",
            },
            status_code=200,
        )

    deal_id = body.deal_id

    # Build deal patch preview (Pipedrive v2)
    deal_url = _pd_v2_url(f"/deals/{deal_id}")
    deal_payload: Dict[str, Any] = {
        "reonic_technical_status": body.technical_status,
        "reonic_project_id": body.reonic_project_id,
    }

    for k in ["stage_id", "status", "probability", "expected_close_date", "value", "currency"]:
        v = getattr(body, k, None)
        if v is not None:
            deal_payload[k] = v

    deal_preview = {
        "method": "PATCH",
        "endpoint": deal_url,
        "headers": _redacted_headers(pd_headers),
        "json_body": deal_payload,
    }

    # Build activity create preview (Pipedrive v2)
    activity_url = _pd_v2_url("/activities")
    activity_payload: Dict[str, Any] = {
        "subject": f"Reonic webhook: {event}",
        "type": "task",
        "deal_id": deal_id,
        "note": f"technical_status={body.technical_status}",
        "reonic_project_id": body.reonic_project_id,
    }
    activity_preview = {
        "method": "POST",
        "endpoint": activity_url,
        "headers": _redacted_headers(pd_headers),
        "json_body": activity_payload,
    }

    return JSONResponse(
        content={
            "success": True,
            "event": event,
            "received_event": body.dict(),
            "pipedrive_actions": [deal_preview, activity_preview],
            "note": "Closed-loop mock: inbound Reonic webhook -> outbound Pipedrive request previews (no real HTTP).",
        },
        status_code=200,
    )