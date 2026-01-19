from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL,
)

from utils.products_types import ProductCreate

router = APIRouter()

@router.post("")
async def add_product(body: ProductCreate):
    """
    Create a (mocked) Pipedrive Product.
    POST https://{company}.pipedrive.com/api/v2/products?api_token=TOKEN
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    url = f"{PIPEDRIVE_BASE_URL}/api/v2/products"
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

    status_code = 201
    if status_code not in (200, 201):
        raise HTTPException(status_code=status_code, detail="Pipedrive error")

    data = {
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
        }
    }

    return JSONResponse(content=data, status_code=status_code)