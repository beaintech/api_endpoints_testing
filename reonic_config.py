import os
from typing import Any, Dict, List

# IMPORTANT:
# docs.reonic.de is documentation. The real API base should come from your Reonic integration setup.
REONIC_API_BASE = os.getenv("REONIC_API_BASE", "http://localhost:8000")

# Keep client id in config (may be used by other Reonic REST endpoints),
# but it is NOT required for the Zapier create-request endpoint below.
REONIC_CLIENT_ID = os.getenv("REONIC_CLIENT_ID", "YOUR_CLIENT_ID_HERE")

# Reonic auth header:
# Option A: store the full header value in REONIC_AUTH_HEADER, e.g. "Basic <token>"
# Option B: store only the token part in REONIC_API_KEY and we will build "Basic <token>"
REONIC_API_KEY = os.getenv("REONIC_API_KEY", "YOUR_REONIC_API_KEY_HERE")
REONIC_AUTH_HEADER = os.getenv("REONIC_AUTH_HEADER", "")

# Reonic create-request endpoint (as per docs)
# NOTE: This endpoint does NOT use clientId in the path.
REONIC_REQUEST_CREATE_PATH = os.getenv(
    "REONIC_REQUEST_CREATE_PATH",
    "/integrations/zapier/h360/requests",
)

REONIC_WEBHOOK_SUBSCRIBE_PATH_TMPL = os.getenv(
    "REONIC_WEBHOOK_SUBSCRIBE_PATH_TMPL",
    "/integrations/zapier/webhooks/{event}/subscribe",
)

def _reonic_request_create_url() -> str:
    """Build the full URL for creating a Reonic request."""
    base = (REONIC_API_BASE or "").rstrip("/")
    path = REONIC_REQUEST_CREATE_PATH if REONIC_REQUEST_CREATE_PATH.startswith("/") else f"/{REONIC_REQUEST_CREATE_PATH}"
    return f"{base}{path}"

def _reonic_webhook_subscribe_url(event: str) -> str:
    base = (REONIC_API_BASE or "").rstrip("/")
    path = REONIC_WEBHOOK_SUBSCRIBE_PATH_TMPL.format(event=event)
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}{path}"

def build_reonic_headers() -> Dict[str, str]:
    """Build Reonic HTTP headers for API requests (redact on logging elsewhere)."""
    header_name = "X-Authorization"  # keep exact header casing

    if REONIC_AUTH_HEADER:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            header_name: REONIC_AUTH_HEADER,
        }

    if not REONIC_API_KEY or REONIC_API_KEY == "YOUR_REONIC_API_KEY_HERE":
        raise ValueError("Missing Reonic auth (set REONIC_AUTH_HEADER or REONIC_API_KEY)")

    return {
        "accept": "application/json",
        "content-type": "application/json",
        header_name: f"Basic {REONIC_API_KEY}",
    }

def _transform_found_leads_to_reonic_create_requests(found: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform Pipedrive leads -> Reonic create-request bodies.
    Reonic requires: firstName, lastName, AND (latLng OR addressToGeocode).
    """
    out: List[Dict[str, Any]] = []
    for lead in found:
        out.append(
            {
                "firstName": "Pipedrive",
                "lastName": "Lead",
                "message": lead.get("title") or "Imported from Pipedrive",
                "note": (
                    f"pipedrive_lead_id={lead.get('id')} "
                    f"person_id={lead.get('person_id')} "
                    f"owner_id={lead.get('owner_id')}"
                ),
                "addressToGeocode": {
                    "country": "Germany",
                    "postcode": "10115",
                    "city": "Berlin",
                    "street": "Hauptstraße",
                    "streetNumber": "1",
                },
                "leadSourceName": "Pipedrive",
            }
        )
    return out
