from typing import Optional
from pydantic import BaseModel

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
    org_id: Optional[int] = None
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

class ReonicProjectEvent(BaseModel):
    event_type: str
    reonic_project_id: str
    technical_status: Optional[str] = None
    deal_id: Optional[int] = None