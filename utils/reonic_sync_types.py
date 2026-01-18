from typing import Optional
from pydantic import BaseModel

# Incoming webhook event from Reonic (or your mock webhook)
class ReonicWebhookEvent(BaseModel):
    event_type: str
    reonic_project_id: str
    technical_status: Optional[str] = None
    deal_id: Optional[int] = None


# Reonic -> Pipedrive: patch a deal (v2 /deals/{id})
class ReonicDealStatusUpdate(BaseModel):
    deal_id: int
    stage_id: Optional[int] = None
    status: Optional[str] = None
    probability: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    expected_close_date: Optional[str] = None  # YYYY-MM-DD
    technical_status: Optional[str] = None
    reonic_project_id: Optional[str] = None


# Reonic -> Pipedrive: create an activity (v2 /activities)
class ReonicActivityPayload(BaseModel):
    subject: str
    type: Optional[str] = "task"
    deal_id: Optional[int] = None
    person_id: Optional[int] = None
    org_id: Optional[int] = None
    due_date: Optional[str] = None  # YYYY-MM-DD
    note: Optional[str] = None
    reonic_project_id: Optional[str] = None


# Combined "project update" input used by your local endpoint
# (this endpoint may trigger both deal patch + activity create)
class ReonicProjectUpdate(BaseModel):
    deal_id: int
    technical_status: Optional[str] = None
    expected_go_live: Optional[str] = None  # YYYY-MM-DD
    progress_note: Optional[str] = None
    reonic_project_id: Optional[str] = None
    stage_id: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    owner_id: Optional[int] = None


# Upsert a deal by Reonic project id (local convenience endpoint)
class ReonicDealUpsert(BaseModel):
    reonic_project_id: str
    title: Optional[str] = None
    technical_status: Optional[str] = None
    stage_id: Optional[int] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    owner_id: Optional[int] = None
    person_id: Optional[int] = None
    org_id: Optional[int] = None
    expected_close_date: Optional[str] = None  # YYYY-MM-DD

class ReonicWebhookSubscribePayload(BaseModel):
    hookUrl: str

class ReonicZapierWebhookIn(BaseModel):
    id: str                 # Reonic offer/request UUID
    client_id: str          # Reonic clientId (needed for REST GET)