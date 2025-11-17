import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

# Basic config for Pipedrive & Reonic
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN", "YOUR_API_TOKEN_HERE")
PIPEDRIVE_COMPANY_DOMAIN = os.getenv("PIPEDRIVE_COMPANY_DOMAIN", "yourcompany")  
REONIC_API_BASE = os.getenv("REONIC_API_BASE", "http://localhost:8000") 

PIPEDRIVE_BASE_URL = f"https://{PIPEDRIVE_COMPANY_DOMAIN}.pipedrive.com/v1"
class ProductPrice(BaseModel):
    price: float | None = None
    currency: str | None = None
    cost: float | None = None
    overhead_cost: float | None = None

class ProductCreate(BaseModel):
    name: str
    code: str | None = None
    unit: str | None = None
    tax: float | None = None
    active_flag: int | None = None
    selectable: int | None = None
    visible_to: str | None = None
    owner_id: int | None = None
    prices: list[ProductPrice] | None = None

@router.post("/add_product")
async def add_product(body: ProductCreate):
    """
    Create a (mocked) Pipedrive Product.
    
    Real-world API endpoint:
      POST https://{company}.pipedrive.com/v1/products?api_token=TOKEN
    """

    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    url = f"{PIPEDRIVE_BASE_URL}/products"
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    payload = {
        "name": body.name,
        "code": body.code,
        "unit": body.unit,
        "tax": body.tax,
        "active_flag": body.active_flag,
        "selectable": body.selectable,
        "visible_to": body.visible_to,
        "owner_id": body.owner_id,
        "prices": [price.dict(exclude_none=True) for price in body.prices] if body.prices else None,
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
            "json_body": payload
        },
        "data": {
            "id": 501,
            "name": payload.get("name"),
            "code": payload.get("code"),
            "unit": payload.get("unit"),
            "tax": payload.get("tax"),
            "active_flag": payload.get("active_flag"),
            "selectable": payload.get("selectable"),
            "visible_to": payload.get("visible_to"),
            "owner_id": payload.get("owner_id"),
            "prices": payload.get("prices") or [],
            "created_from": "python-mock-demo"
        }
    }

    resp = MockResponse(mock_body)

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid JSON in mock Pipedrive response")

    if resp.status_code not in (200, 201) or not data.get("success"):
        raise HTTPException(
            status_code=resp.status_code,
            detail=data.get("error") or "Pipedrive error"
        )

    return JSONResponse(content=data, status_code=resp.status_code)