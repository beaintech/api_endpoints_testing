from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pipedrive_config import (
    PIPEDRIVE_API_TOKEN,
    PIPEDRIVE_BASE_URL,
    REONIC_API_BASE,
)

router = APIRouter()
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


@router.post("/sync_reonic_products")
async def sync_reonic_products():
    """
    Mock flow that syncs products from Reonic into Pipedrive.

    1) Fetch product catalog from Reonic.
    2) Transform each entry into the payload the Pipedrive API expects.
    3) Return the mocked POST calls so you can inspect what would be sent.
    """
    if not PIPEDRIVE_API_TOKEN:
        raise HTTPException(status_code=400, detail="PIPEDRIVE_API_TOKEN is not set.")

    reonic_url = f"{REONIC_API_BASE}/products"

    class MockResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    reonic_mock_payload = {
        "success": True,
        "request": {
            "method": "GET",
            "endpoint": reonic_url,
        },
        "products": [
            {
                "id": "RON-PRD-1",
                "name": "Reonic Solar Panel Set",
                "sku": "SOL-SET-01",
                "unit": "kwp",
                "default_currency": "EUR",
                "list_price": 8990,
                "ownership": {"owner_id": 501},
                "tax_rate": 19,
            },
            {
                "id": "RON-PRD-2",
                "name": "Reonic EV Charger",
                "sku": "EV-CHR-10",
                "unit": "pcs",
                "default_currency": "EUR",
                "list_price": 2300,
                "ownership": {"owner_id": 502},
                "tax_rate": 19,
            },
        ],
    }

    reonic_resp = MockResponse(reonic_mock_payload, status_code=200)

    try:
        reonic_data = reonic_resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid JSON from mock Reonic")

    if reonic_resp.status_code != 200 or not reonic_data.get("success", False):
        raise HTTPException(
            status_code=reonic_resp.status_code,
            detail=reonic_data.get("error") or "Reonic error",
        )

    products = reonic_data.get("products", [])

    pipedrive_url = f"{PIPEDRIVE_BASE_URL}/products"
    pipedrive_params = {"api_token": PIPEDRIVE_API_TOKEN}

    pipedrive_calls = []
    for idx, product in enumerate(products, start=1):
        payload = {
            "name": product.get("name"),
            "code": product.get("sku"),
            "unit": product.get("unit") or "pcs",
            "tax": product.get("tax_rate"),
            "owner_id": product.get("ownership", {}).get("owner_id"),
            "prices": [
                {
                    "currency": product.get("default_currency"),
                    "price": product.get("list_price"),
                }
            ]
            if product.get("default_currency") and product.get("list_price") is not None
            else None,
            "visible_to": "1",
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        mock_created_id = 800 + idx
        pipedrive_calls.append(
            {
                "request": {
                    "method": "POST",
                    "endpoint": pipedrive_url,
                    "query_params": pipedrive_params,
                    "json_body": payload,
                },
                "response": {
                    "success": True,
                    "data": {
                        "id": mock_created_id,
                        "name": payload.get("name"),
                        "code": payload.get("code"),
                        "unit": payload.get("unit"),
                        "owner_id": payload.get("owner_id"),
                        "prices": payload.get("prices") or [],
                        "source": "reonic-mock-sync",
                    },
                },
            }
        )

    return JSONResponse(
        content={
            "reonic_products_count": len(products),
            "pipedrive_create_attempts": len(pipedrive_calls),
            "pipedrive_calls": pipedrive_calls,
        }
    )
