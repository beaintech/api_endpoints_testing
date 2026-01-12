# Pipedrive Local Playground (FastAPI)

A fully local sandbox for simulating Pipedrive API calls using mocked data.  
This playground is designed for demonstrating how Pipedrive <-> Reonic integrations work **without requiring real credentials**.

To connect it to a real Pipedrive account, you mainly switch the mocked calls to real HTTP calls and align URLs per endpoint:
- Many core entities exist in v2 under `/api/v2/...` (e.g. deals/products/organizations and leads search).
- Leads search exists in v2: `GET /api/v2/leads/search`.
- Lead create/update in the official docs are still shown as v1 endpoints (`POST /v1/leads`, `PATCH /v1/leads/{id}`), so do not assume “everything is /api/v2” for leads CRUD.

If you want the playground to feel “v2-realistic”, keep the ID formats consistent with Pipedrive:
- `lead_id` (lead `id`) is a **UUID string** (e.g. `6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3`)
- `person_id` is an **integer**
- `organization_id` is an **integer**
- `deaö_id` is an **integer ID**

---

## Installation
python -m pip install fastapi "uvicorn[standard]" python-dotenv

---

## Run Locally
uvicorn main:app --reload --port 8000

Server starts at:

http://localhost:8000

---

### Swagger UI

[http://localhost:8000/docs](http://localhost:8000/docs)

---

## Endpoint Rename Cheatsheet (Local Playground)

These are your LOCAL FastAPI routes (mock playground), not official Pipedrive routes:

/get_leads → /leads
/get_lead/{id} → /leads/{id}
/create_lead → /leads
/update_lead/{id} → /leads/{id}
/delete_lead/{id} → /leads/{id}

/sync_leads → /sync/pipedrive-to-reonic/leads
/sync_reonic_to_pipedrive → /sync/reonic-to-pipedrive/projects
/sync_reonic_products → /sync/reonic-to-pipedrive/products

/add_product → /products
/add_organization → /organizations

/reonic_push_status_to_pipedrive → /reonic_push_status_to_pipedrive
/reonic_push_activity_to_pipedrive → /reonic_push_activity_to_pipedrive
/reonic_push_project_update → /reonic_push_project_update

/reonic_webhook_project_event → /reonic_webhook_project_event
/lookup_deal_id_by_reonic_project/{reonic_project_id} → /lookup_deal_id_by_reonic_project/{reonic_project_id}
/upsert_deal_by_reonic_project_id → /upsert_deal_by_reonic_project_id

---

## Test Endpoints

### OAuth Callback Test

[http://localhost:8000/callback?code=test](http://localhost:8000/callback?code=test)

### Mock Data Endpoints

[http://localhost:8000/mock/pipedrive](http://localhost:8000/mock/pipedrive)
[http://localhost:8000/mock/saas](http://localhost:8000/mock/saas)

### Pipedrive Mock Endpoints (Local)

GET    /leads
GET    /leads/{lead_id}
POST   /leads
PATCH  /leads/{lead_id}
DELETE /leads/{lead_id}

POST   /sync/pipedrive-to-reonic/leads
POST   /sync/reonic-to-pipedrive/projects

POST   /products
POST   /sync/reonic-to-pipedrive/products

POST   /organizations

GET    /lookup_deal_id_by_reonic_project/{reonic_project_id}
POST   /upsert_deal_by_reonic_project_id


## POST Examples (Leads)

### Create a Lead (POST /leads)

POST → `/leads` → “Try it out” → paste:

{
  "title": "Lead 158",
  "value": { "amount": 3000, "currency": "USD" },
  "owner_id": 13293848,
  "label_ids": ["f981d20f-cd00-4e30-a406-06576a92058b"],
  "person_id": 1,
  "organization_id": 1,
  "expected_close_date": "2025-07-12",
  "visible_to": "1",
  "was_seen": true
}

Notes:

* `person_id` and `organization_id` are integers.
* Lead value is shown as a single `value` object here to match the official Leads payload shape (`{ "amount": ..., "currency": ... }`).

---

## Update a Lead (PATCH /leads/{lead_id})

Example URL (UUID lead id):

[http://localhost:8000/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3](http://localhost:8000/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3)

Example body:

```json
{
  "title": "Updated Lead Title",
  "value": { "amount": 5000, "currency": "EUR" }
}
```

All fields are optional.

---

## Delete a Lead (DELETE /leads/{lead_id})

Example URL:

[http://localhost:8000/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3](http://localhost:8000/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3)

Returns:

```json
{
  "success": true,
  "data": { "id": "6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3", "deleted": true }
}
```

---

## Fetch a Single Lead (GET /leads/{lead_id})

Example URL:

[http://localhost:8000/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3](http://localhost:8000/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3)

---

## Sync Leads (Pipedrive → Reonic)

Trigger the sync:

[http://localhost:8000/sync/pipedrive-to-reonic/leads](http://localhost:8000/sync/pipedrive-to-reonic/leads)

This endpoint does **not** require a request body.

---

## Sync Projects (Reonic → Pipedrive)

Trigger the reverse sync:

[http://localhost:8000/sync/reonic-to-pipedrive/projects](http://localhost:8000/sync/reonic-to-pipedrive/projects)

This fetches mocked Reonic projects, transforms them, and shows the POST payloads that would be sent to the next step (your mock CRM layer).

---

## Sync Products (Reonic → Pipedrive)

Trigger the product sync:

[http://localhost:8000/sync/reonic-to-pipedrive/products](http://localhost:8000/sync/reonic-to-pipedrive/products)

It loads a mocked catalog from Reonic, converts them to Pipedrive product JSON, and returns the mocked POST bodies.

---

# Reonic → Pipedrive (Deals & Activities)

Reonic does **not** create Leads, but it can push updates to existing CRM Deals and Activities.

These endpoints simulate project → CRM sync flows (LOCAL playground endpoints):

### 1) POST `/reonic_push_status_to_pipedrive`

Use when a Reonic status change should update an existing Pipedrive deal.

What it simulates:

* Pipedrive v2 deal patch: `PATCH /api/v2/deals/{deal_id}`
* `deal_id` is an integer in Pipedrive.
* Updates standard deal fields (stage/status/probability/value/currency/expected_close_date)
* Also attaches `reonic_project_id` and `reonic_technical_status` (playground fields)

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/reonic_push_status_to_pipedrive" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": 5001,
    "stage_id": 12,
    "status": "open",
    "probability": 60,
    "value_amount": 12000,
    "value_currency": "EUR",
    "expected_close_date": "2026-02-15",
    "technical_status": "READY_FOR_INSTALL",
    "reonic_project_id": "reonic_proj_demo_001"
  }'

What you get back:

* `request.endpoint` shows the v2-style URL that would be called
* `request.headers` shows `x-api-token` but redacted
* `request.json_body` is the payload you would send
* `data` mirrors the updated deal shape in mock form

---

### 2) POST `/reonic_push_activity_to_pipedrive`

Use when Reonic needs to create a task/log entry in Pipedrive, optionally linked to a deal/person/org.

What it simulates:

* Pipedrive v2 activity create: `POST /api/v2/activities`

Example request:

curl -X POST "http://127.0.0.1:8000/reonic_push_activity_to_pipedrive" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Call customer about installation slot",
    "type": "task",
    "deal_id": 5001,
    "due_date": "2026-01-20",
    "note": "Customer asked for afternoon appointment.",
    "reonic_project_id": "reonic_proj_demo_001"
  }'

Design choice:

* `reonic_project_id` is added into `note` as a trace tag (because activities don’t have your custom fields in this playground).

---

### 3) POST `/reonic_push_project_update`

Use when a single Reonic “project update event” should produce two effects in Pipedrive:

* update the deal fields
* create an activity describing the update

What it simulates:

* Deal patch: `PATCH /api/v2/deals/{deal_id}`
* Activity create: `POST /api/v2/activities`

Example request:

curl -X POST "http://127.0.0.1:8000/reonic_push_project_update" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": 5001,
    "technical_status": "IN_PROGRESS",
    "expected_go_live": "2026-02-01",
    "progress_note": "Panels delivered; installer booked.",
    "reonic_project_id": "reonic_proj_demo_001",
    "stage_id": 14,
    "value_amount": 15500,
    "value_currency": "EUR",
    "owner_id": 1
  }'

Response structure:

* `deal_update` block shows the mocked patch call + payload
* `activity_created` block shows the mocked create call + payload

---

4) GET /api/v2/leads/search

Use when you want to demonstrate the Search API for leads.

What it simulates:

Pipedrive Search API endpoint: GET /leads/search (v2 base: /api/v2/leads/search).

Type notes:

Lead IDs are strings (UUID).

Example request:

curl "http://127.0.0.1:8000/api/v2/leads/search?term=solar&fields=title,notes"


What happens in mock:

It returns example leads as if they were found by search

Each lead id is a UUI D string          

---

### 5) POST `/reonic_webhook_project_event`

Use as the demo “entry point” for events coming from Reonic into your integration service.

What it represents:

* In production, Reonic (or any upstream trigger) would POST an event here.
* Your service decides what downstream actions should run.

What it does in mock:

* It does not call any downstream endpoint.
* It only returns `actions_planned` describing what it would call next.

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/reonic_webhook_project_event" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "project_status_changed",
    "reonic_project_id": "reonic_proj_demo_001",
    "technical_status": "IN_PROGRESS",
    "deal_id": 5001
  }'
```

---

### 6) GET `/lookup_deal_id_by_reonic_project/{reonic_project_id}`

Use to show “where deal_id comes from”.
This answers: given a Reonic project id, which Pipedrive deal id is linked?

What it uses:

* `REONIC_PROJECT_TO_PIPEDRIVE_DEAL` in-memory dict

Example:

```bash
curl "http://127.0.0.1:8000/lookup_deal_id_by_reonic_project/reonic_proj_demo_001"
```

---

### 7) POST `/upsert_deal_by_reonic_project_id`

Use when you want an idempotent sync behavior:

* if mapping exists → update that deal
* if mapping not found → create a deal and store mapping

What it simulates:

* Update path: `PATCH /api/v2/deals/{deal_id}`
* Create path: `POST /api/v2/deals`

Example request (create if not exists):

```bash
curl -X POST "http://127.0.0.1:8000/upsert_deal_by_reonic_project_id" \
  -H "Content-Type: application/json" \
  -d '{
    "reonic_project_id": "reonic_proj_demo_003",
    "title": "Reonic Project reonic_proj_demo_003",
    "technical_status": "NEW",
    "stage_id": 10,
    "value_amount": 8000,
    "value_currency": "EUR",
    "expected_close_date": "2026-03-01"
  }'
```

Run it a second time with the same `reonic_project_id`:

* It will go through the update path because the mapping was stored in memory.

## Notes and limitations

* All responses are mocked. No `requests/httpx` calls exist here.
* Mapping is in-memory. Restarting the server resets mappings.
* `x-api-token` is always redacted in the returned request preview.
* `deal_id` is integer; `lead_id` is UUID string.

---

# Product Endpoints

## Add a Product (POST /products)

[http://localhost:8000/products](http://localhost:8000/products)

You can send the full Pipedrive-style JSON body, including price entries.

Example JSON:

```json
{
  "name": "Test Product",
  "code": "PRD-001",
  "unit": "pcs",
  "tax": 19,
  "active_flag": 1,
  "selectable": 1,
  "visible_to": "1",
  "owner_id": 999,
  "prices": [
    {
      "price": 120,
      "currency": "EUR",
      "cost": 60,
      "overhead_cost": 10
    }
  ]
}
```

---

# Organization Endpoint

## Add an Organization (POST /organizations)

[http://localhost:8000/organizations](http://localhost:8000/organizations)

Minimal example JSON:

```json
{
  "name": "Org Inc test"
}
```

Optional fields example:

```json
{
  "name": "Org Inc test",
  "owner_id": 12345,
  "visible_to": "3",
  "address": "Main Street 1, 40210 Düsseldorf"
}
```

---

## Notes

* All responses are fully mocked – no real requests are sent to Pipedrive.
* URLs and payload shapes aim to mirror Pipedrive behavior (especially ID formats).
* Safe for demos, onboarding, teaching API flows, and integration planning.

```

::contentReference[oaicite:4]{index=4}
```

[1]: https://developers.pipedrive.com/docs/api/v1/Leads "Pipedrive API v1 Dev References (Leads) - View Lead API Get, Post & More - Learn - Test - Try Now"
[2]: https://developers.pipedrive.com/docs/api/v1/Organizations "Pipedrive API v1–v2 Dev References (Organizations) - Learn - Test - Try Now"
