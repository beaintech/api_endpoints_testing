from pydantic import BaseModel
from typing import Optional, List

class ProductPrice(BaseModel):
    price: Optional[float] = None
    currency: Optional[str] = None
    cost: Optional[float] = None
    overhead_cost: Optional[float] = None

class ProductCreate(BaseModel):
    name: str
    code: Optional[str] = None
    unit: Optional[str] = None
    tax: Optional[float] = None
    active_flag: Optional[int] = None
    selectable: Optional[int] = None
    visible_to: Optional[str] = None
    owner_id: Optional[int] = None
    prices: Optional[List[ProductPrice]] = None