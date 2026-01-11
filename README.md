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

---

## Installation

```bash
python -m pip install fastapi "uvicorn[standard]" python-dotenv
````

---

## Run Locally

```bash
uvicorn main:app --reload --port 8000
```

Server starts at:

```text
http://localhost:8000
```

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

### Swagger UI

[http://localhost:8000/docs](http://localhost:8000/docs)

---

## About ID Types (Important)

In Pipedrive:

* `lead_id` is a UUID string. If you want your local fixtures to mirror Pipedrive, do NOT use numeric IDs like `101` for leads.
* `person_id` is an integer.
* `organization_id` is an integer.

So in this README we will use example lead IDs like:

`6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3`

If your local mock fixtures still use numeric IDs internally, you can keep them for now, but the “v2-realistic” version should migrate them to UUID strings.

---

## POST Examples (Leads)

### Create a Lead (POST /leads)

POST → `/leads` → “Try it out” → paste:

```json
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
```

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

## Update Deal Status (POST /reonic_push_status_to_pipedrive)

[http://localhost:8000/reonic_push_status_to_pipedrive](http://localhost:8000/reonic_push_status_to_pipedrive)

This endpoint simulates sending project progress from Reonic to an existing Pipedrive Deal.

Typical updated fields:

* `stage_id`
* `status`
* `probability`
* `value_amount` / `value_currency`
* `expected_close_date`
* `technical_status`
* `reonic_project_id`

`technical_status` and `reonic_project_id` represent integration-level fields
that are typically mapped to Pipedrive custom fields or activity notes.

---

## Create Activity (POST /reonic_push_activity_to_pipedrive)

[http://localhost:8000/reonic_push_activity_to_pipedrive](http://localhost:8000/reonic_push_activity_to_pipedrive)

This simulates Reonic logging an activity into Pipedrive.

Typical fields:

* `subject`
* `type` (task, call, meeting, installation)
* `deal_id`
* `person_id`
* `due_date`
* `note`
* `reonic_project_id`

---

## Combined Project Update (POST /reonic_push_project_update)

[http://localhost:8000/reonic_push_project_update](http://localhost:8000/reonic_push_project_update)

This endpoint performs two mock actions:

1. Updates a Deal (stage/value/date/status)
2. Creates an Activity (log an event about the update)

---

# Webhook Entry (Reonic → This service)

## Project/Event Webhook (POST /reonic_webhook_project_event)

[http://localhost:8000/reonic_webhook_project_event](http://localhost:8000/reonic_webhook_project_event)

This endpoint represents the REAL entry point in production:
Reonic pushes events here, then the service decides what to sync to Pipedrive.

In the playground it only returns “planned actions” and does not call downstream endpoints.

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
