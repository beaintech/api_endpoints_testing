````markdown
# Reonic ↔ Pipedrive Mock Playground (Pipedrive v2-style)

This router is a **pure mock playground** for validating data shapes and flow direction before doing any real integration.
It does **not** call Pipedrive or Reonic for real.
Every endpoint returns a JSON payload that shows what would be sent (method / endpoint / headers / json_body) and a mocked `data` result.

## What “v2-style” means here

This playground formats Pipedrive requests as if you were using Pipedrive v2:
- URL style: `.../api/v2/...`
- Auth style: `x-api-token` header
- No `api_token` query params

It is still mock-only. No HTTP requests are made.

## Config (pipedrive_config.py)

You need these variables:

- `PIPEDRIVE_API_TOKEN`  
  Any non-empty string is fine for mock mode. If empty, endpoints return 400.

- `PIPEDRIVE_BASE_URL`  
  Example: `https://companydomain.pipedrive.com`  
  Important: **do not** include `/api/v2` here.

- `REONIC_API_BASE`  
  Any base URL string used only for building the mocked “Reonic receiver” endpoint.
  Example: `http://localhost:8000/reonic-mock`

## Run locally

If this router is included in a FastAPI app, run:

```bash
uvicorn app.main:app --reload --port 8000
````

Open docs:

* [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Design note: why `_apply_reonic_fields` exists

Multiple endpoints construct a “Pipedrive payload”.
You want to attach Reonic business identifiers consistently:

* `reonic_project_id`
* `reonic_technical_status`

Instead of duplicating those lines in every endpoint, `_apply_reonic_fields(payload, ...)` injects them the same way everywhere.

## Endpoints and what each one is for

### 1) POST `/reonic_push_status_to_pipedrive`

Use when a Reonic status change should update an existing Pipedrive deal.

What it simulates:

* Pipedrive v2 deal patch: `PATCH /api/v2/deals/{deal_id}`
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
```

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

```bash
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
```

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

```bash
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
```

Response structure:

* `deal_update` block shows the mocked patch call + payload
* `activity_created` block shows the mocked create call + payload

---

### 4) POST `/pipedrive_push_leads_to_reonic`

Use when you want to demonstrate the reverse direction:

* read leads from Pipedrive
* transform them
* push them into a Reonic “import endpoint” (mock)

What it simulates:

* Pipedrive v2 leads search: `GET /api/v2/leads/search`
* Reonic receiver: `POST {REONIC_API_BASE}/leads/import` (mocked endpoint name)

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/pipedrive_push_leads_to_reonic?term=solar"
```

What happens in mock:

* It returns two example leads as if they were found by search
* It transforms them to your simplified Reonic import schema:

  * `external_id`, `title`, `source`, `person_id`, `owner_id`, `add_time`
* It returns a mocked “Reonic import response” with `imported: N`

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
* Reonic endpoints like `/leads/import` are placeholders for your demo receiver side.

```
::contentReference[oaicite:0]{index=0}
```
