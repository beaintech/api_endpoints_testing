from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from utils.helper import (
    _pd_v1_url,
    _pd_v2_url,
    _pd_v1_params,
    _pd_headers,
    _redacted_headers,
    _mock_leads_found,
    _mock_reonic_create_response,
)
from pipedrive_config import CF_REONIC_REQUEST_ID_KEY
from reonic_config import (
    _reonic_request_create_url,
    _transform_found_leads_to_reonic_create_requests,
)

router = APIRouter()

@router.post("/sync/pipedrive-to-reonic/leads")
async def sync_leads_pipedrive_to_reonic(
    term: str = Query("solar"),
    limit: int = Query(2, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    match: str = Query("middle"),
):
    pd_headers = _pd_headers()

    # Pipedrive v2 search 
    search_url = _pd_v2_url("/leads/search")

    found = _mock_leads_found(term)[:limit]

    # Reonic create-request (per docs endpoint; preview only)
    reonic_url = _reonic_request_create_url()
    reonic_payloads = _transform_found_leads_to_reonic_create_requests(found)

    mappings: List[Dict[str, str]] = []
    reonic_create_previews: List[Dict[str, Any]] = []
    pipedrive_writeback_previews: List[Dict[str, Any]] = []

    for lead, payload in zip(found, reonic_payloads):
        lead_id = lead["id"]

        # planned Reonic create
        reonic_create_previews.append(
            {"method": "POST", "endpoint": reonic_url, "json_body": payload}
        )

        # mock: pretend Reonic returned a request id
        reonic_resp = _mock_reonic_create_response(lead_id)
        reonic_request_id = reonic_resp["id"]

        mappings.append({"pipedrive_lead_id": lead_id, "reonic_request_id": reonic_request_id})

        # planned Pipedrive write-back to the SAME lead (update lead is v1)
        pipedrive_writeback_previews.append(
            {
                "method": "PATCH",
                "endpoint": _pd_v1_url(f"/leads/{lead_id}"),
                "query": _pd_v1_params(), 
                "headers": _redacted_headers(pd_headers),
                "json_body": {CF_REONIC_REQUEST_ID_KEY: reonic_request_id},
            }
        )

    request_preview = {
        "pipedrive_search": {
            "method": "GET",
            "endpoint": search_url,
            "headers": _redacted_headers(pd_headers),
            "query": {"term": term, "limit": limit, "cursor": cursor, "match": match},
        },
        "reonic_create_requests": reonic_create_previews,
        "pipedrive_writebacks": pipedrive_writeback_previews,
    }

    return JSONResponse(
        content={
            "success": True,
            "request": request_preview,
            "data": {
                "pipedrive_found": found,
                "mappings_built": mappings,
                "next_cursor": "mock_cursor_1" if cursor is None else None,
                "note": "Mock demo only: no real HTTP executed.",
            },
        },
        status_code=200,
    )