# Pipedrive Local Playground (FastAPI)

A fully local sandbox for simulating Pipedrive API calls using mocked data.  
This playground is designed for demonstrating how Pipedrive <-> Reonic integrations work **without requiring real credentials**.

## How “real HTTP” would look later (v1 vs v2, only when you switch to real calls)

When you eventually replace mocks with real HTTP calls, **don’t assume everything is `/api/v2`**.

- Many core entities are v2 under `/api/v2/...` (e.g. deals/products/organizations, activities).
- **Leads search is v2**: `GET /api/v2/leads/search`
- **Leads CRUD is v1** (create/read/update/delete):  
  `GET /v1/leads/{id}`  
  `POST /v1/leads`  
  `PATCH /v1/leads/{id}`  
  `DELETE /v1/leads/{id}`

If you want the playground to feel “realistic”, keep ID formats consistent with Pipedrive:
- `lead_id` (lead `id`) is a **UUID string** (e.g. `6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3`)
- `person_id` is an **integer**
- `org_id` is an **integer**
- `deal_id` is an **integer**

---

## Installation

python -m pip install fastapi "uvicorn[standard]" python-dotenv

---

## Run Locally

uvicorn main:app --reload --port 8000

Server starts at:

http://localhost:8000

Swagger UI:
http://localhost:8000/docs

---

## Endpoint Rename Cheatsheet (Local Playground)


---

## Test Endpoints

OAuth callback test:

/callback?code=test

---

## Pipedrive Mock Endpoints (Local)

GET     /leads
GET     /leads/{lead_id}
POST    /leads
PATCH   /leads/{lead_id}
DELETE  /leads/{lead_id}
POST    /products
POST    /organizations

---

# Leads (Local Mock)

## Create a Lead (POST /leads)

Swagger → `POST /leads` → “Try it out” → paste:

{
  "title": "Lead 158",
  "value": { "amount": 3000, "currency": "USD" },
  "owner_id": 13293848,
  "label_ids": ["f981d20f-cd00-4e30-a406-06576a92058b"],
  "person_id": 1,
  "org_id": 1,
  "expected_close_date": "2025-07-12",
  "visible_to": "1",
  "was_seen": true
}

Notes:

* `person_id` and `org_id` are integers.
* Lead value is shown as a single `value` object to match the common Leads payload shape: `{ "amount": ..., "currency": ... }`.

---

## Update a Lead (PATCH /leads/{lead_id})

Example URL (UUID lead id):

/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3

Example body:

{
  "title": "Updated Lead Title",
  "value": { "amount": 5000, "currency": "EUR" }
}

All fields are optional.

---

## Delete a Lead (DELETE /leads/{lead_id})

Example URL:

/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3

Returns:

{
  "success": true,
  "data": { "id": "6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3", "deleted": true }
}

---

## Fetch a Single Lead (GET /leads/{lead_id})

Example URL:

/leads/6b2f2dd0-5c3e-4f87-9a29-2f70e3f6f1a3

---

# Sync (Pipedrive → Reonic)

## Sync Leads (Local)

This endpoint is **POST** and does **not** require a request body.

curl -X POST "http://127.0.0.1:8000/api/sync/pipedrive-to-reonic/leads?term=solar&limit=2"

It returns mocked leads, transforms them, and shows the payload that would be sent to the next step.

---

# Sync (Reonic → Pipedrive)

## Sync Projects (Local)

POST "http://127.0.0.1:8000/sync/reonic-to-pipedrive/projects"

This fetches mocked Reonic projects, transforms them, and returns the mocked request previews that would be sent downstream.

---

# Reonic → Pipedrive (Deals & Activities)

Reonic does **not** create Pipedrive Leads. This section focuses on updating Deals / creating Activities.

## 1) PATCH `/api/v2/deals/{deal_id}`

Use when a Reonic status change should update an existing Pipedrive deal.

What it simulates:

* Pipedrive v2 deal patch: `PATCH /api/v2/deals/{deal_id}`
* `deal_id` is an integer in Pipedrive.
* Updates standard deal fields (stage/status/probability/value/currency/expected_close_date)
* Also attaches `reonic_project_id` and `reonic_technical_status` (playground fields)

Example request:
```bash
DEAL_ID=5001

curl -X PATCH "http://127.0.0.1:8000/api/v2/deals/${DEAL_ID}" \
  -H "Content-Type: application/json" \
  -d "{
    \"deal_id\": ${DEAL_ID},
    \"stage_id\": 3,
    \"status\": \"open\",
    \"technical_status\": \"h360_ready\",
    \"reonic_project_id\": \"reonic_proj_demo_001\"
  }"

```
---

## 2) POST `/api/v2/activities`

Use when Reonic needs to create a task/log entry in Pipedrive, optionally linked to a deal/person/org.

What it simulates:

* Pipedrive v2 activity create: `POST /api/v2/activities`

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/activities" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Call customer about installation slot",
    "type": "task",
    "deal_id": 5001,
    "org_id": 100,
    "due_date": "2026-01-20",
    "note": "Customer asked for afternoon appointment.",
    "reonic_project_id": "reonic_proj_demo_001"
  }'
```

Design choice:

* `reonic_project_id` is added into `note` as a trace tag (because activities don’t have your custom fields in this playground).

---

## 3) POST `/integrations/zapier/webhooks/{event}/subscribe`

Use to register a webhook subscription in Reonic (Zapier API).

What it represents:
* In production, your service calls Reonic to subscribe to an event.
* Reonic will later POST real event payloads to your hookUrl.

What it does in this playground:
* Returns a request preview only (no real HTTP executed).
* Shows the exact Reonic endpoint + headers + JSON body that would be sent.

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/integrations/zapier/webhooks/request-created/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"hookUrl":"https://your-domain.com/reonic/webhook"}'

```

---

## 4) POST `/reonic/webhook/{event}`

Use as the demo webhook receiver endpoint for events coming from Reonic into your integration service.

What it represents:

* In production, Reonic will POST an event payload to this endpoint (your inbound webhook).
* Your service parses the event and decides which downstream actions to run (update deal, create activity, etc.).

What it does in mock:

* Does not execute any real downstream HTTP calls.
* Only returns `actions_planned` describing what it would call next.

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/api/reonic/webhook/{event}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "project_status_changed",
    "reonic_project_id": "reonic_proj_demo_001",
    "technical_status": "IN_PROGRESS",
    "deal_id": 5001
  }'
```

or

```bash
curl -X POST "http://127.0.0.1:8000/api/reonic/webhook/request-created" \
  -H "Content-Type: application/json" \
  -d '{"reonic_project_id":"reonic_proj_demo_001","technical_status":"h360_ready"}'

```

---

## 3) POST `/api/v2/leads/search`

Use when you want to demonstrate the reverse direction:

* Read leads from Pipedrive (search)
* Transform them
* Push them into a Reonic “receiver endpoint” (mock placeholder)

What it simulates:

* Pipedrive leads search: `GET /api/v2/leads/search`
* Lead IDs are UUID strings in Pipedrive.

Reonic receiver (mock placeholder):

* `POST {REONIC_API_BASE}/{REONIC_IMPORT_PATH}`

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/leads/search?term=solar"
```

What happens in mock:

* Returns example leads as if found by search
* Transforms them to a simplified Reonic import schema:

  * `external_id`, `title`, `source`, `person_id`, `owner_id`, `add_time`
* Returns a mocked “Reonic import response” with `imported: N`

---

## Notes and limitations

* All responses are mocked. No `requests/httpx` calls exist here.
* Mapping is in-memory. Restarting the server resets mappings.
* `x-api-token` is always redacted in the returned request preview.
* `deal_id` is integer; `lead_id` is UUID string.

---

# Product Endpoints

## Product mock: POST `/products` (Create Product)

Use when you want to demonstrate the “product creation” part of your Pipedrive flow locally:

* Send a Product payload that looks like Pipedrive
* Validate your request shape and field filtering
* Get back a simple “real-looking” response with a `data` object

What it simulates:

* Pipedrive create product: `POST https://{company}.pipedrive.com/api/v2/products?api_token=TOKEN`
* A successful create returns HTTP 201 and a product object

What this endpoint actually does:

* This is a pure mock. No `requests/httpx` calls are made.
* It only checks that `PIPEDRIVE_API_TOKEN` exists, so you don’t test with an empty env.
* It builds a clean payload by removing any `null` fields.
* It returns a mocked product response with a fixed `id: 501` and echoes your fields back.

Required config:

* `PIPEDRIVE_API_TOKEN` must be set (otherwise the endpoint returns 400)
* `PIPEDRIVE_BASE_URL` should be the company root domain only, e.g. `https://yourcompany.pipedrive.com` (no `/v1`, no `/api/v2`)

Request body schema:

* `name` is required
* Optional fields: `code`, `unit`, `tax`, `active_flag`, `selectable`, `visible_to`, `owner_id`
* Optional `prices`: list of objects with `price`, `currency`, `cost`, `overhead_cost`

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reonic EV Charger",
    "code": "EV-CHR-10",
    "unit": "pcs",
    "tax": 19,
    "active_flag": 1,
    "selectable": 1,
    "visible_to": "1",
    "owner_id": 502,
    "prices": [{"price": 2300, "currency": "EUR"}]
  }'
```

What happens in mock:

* Filters out all fields that are `null`
* Returns HTTP 201 and a minimal response shaped like:

```json
{
  "data": {
    "id": 501,
    "name": "Reonic EV Charger",
    "code": "EV-CHR-10",
    "unit": "pcs",
    "tax": 19,
    "active_flag": 1,
    "selectable": 1,
    "visible_to": "1",
    "owner_id": 502,
    "prices": [
      { "price": 2300, "currency": "EUR" }
    ]
  }
}
```

---

## Notes and limitations

* All responses are mocked. No external Pipedrive calls exist here.
* The returned `id` is fixed (`501`) by design for predictable testing.
* `prices` defaults to an empty list in the response if you omit it in the request.
* This endpoint is only meant to validate request/response shape and payload transformation.

---

# Organization Endpoint

## Add an Organization (POST /organizations)

Minimal example JSON:

{
  "name": "Org Inc test"
}

Optional fields example:

{
  "name": "Org Inc test",
  "owner_id": 12345,
  "visible_to": "3",
  "address": "Main Street 1, 40210 Düsseldorf"
}

---

## Reference (official docs)

Leads v1: https://developers.pipedrive.com/docs/api/v1/Leads

Organizations: https://developers.pipedrive.com/docs/api/v1/Organizations