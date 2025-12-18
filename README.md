# Pipedrive Local Playground (FastAPI)

A fully local sandbox for simulating Pipedrive API calls using mocked data.  
This playground is designed for demonstrating how Pipedrive <-> Reonic integrations work **without requiring real credentials**.

 To connect it to a real Pipedrive account you only need three changes: switch the base URL to the official /api/v2 endpoint, change the deal value structure to use value and currency as separate fields as required by Pipedrive, and add a small mapping layer from Reonic’s semantic field names to the actual Pipedrive custom field keys. After that you can replace the internal MockResponse objects with real HTTP calls using a client such as httpx or requests.

---

## Installation

```
pip install fastapi "uvicorn[standard]" python-dotenv
```

---

## Run Locally

uvicorn main:app --reload --port 8000

Server starts at:

http://localhost:8000

---

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
/reonic_push_status_to_pipedrive → /reonic/push/deal-status
/reonic_push_activity_to_pipedrive → /reonic/push/activity
/reonic_push_project_update → /reonic/push/project-update

---

## Test Endpoints

### OAuth Callback Test

[http://localhost:8000/callback?code=test](http://localhost:8000/callback?code=test)

### Mock Data Endpoints

[http://localhost:8000/mock/pipedrive](http://localhost:8000/mock/pipedrive)
[http://localhost:8000/mock/saas](http://localhost:8000/mock/saas)

### Pipedrive Mock Endpoints

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

## POST Examples (Leads)

### Create a Lead (POST /leads)

POST → `/leads` → “Try it out” → paste:

```json
{
  "title": "Lead 158",
  "amount": 3000,
  "currency": "USD",
  "owner_id": 13293848,
  "label_ids": ["f981d20f-cd00-4e30-a406-06576a92058b"],
  "person_id": 1,
  "organization_id": 1,
  "expected_close_date": "2025-07-12",
  "visible_to": "1",
  "was_seen": true
}
```

---

## Update a Lead (PATCH /leads/{lead_id})

[http://localhost:8000/leads/101](http://localhost:8000/leads/101)

Example body:

```json
{
  "title": "Updated Lead Title",
  "amount": 5000,
  "currency": "EUR"
}
```

All fields are optional.

---

## Delete a Lead (DELETE /leads/{lead_id})

[http://localhost:8000/leads/101](http://localhost:8000/leads/101)

Returns:

```json
{
  "success": true,
  "data": { "id": 101, "deleted": true }
}
```

---

## Fetch a Single Lead (GET /leads/{lead_id})

[http://localhost:8000/leads/101](http://localhost:8000/leads/101)

---

## Sync Leads (Pipedrive → Reonic)

Trigger the sync:

[http://localhost:8000/sync/pipedrive-to-reonic/leads](http://localhost:8000/sync/pipedrive-to-reonic/leads)

This endpoint does **not** require a request body.

## Sync Projects (Reonic → Pipedrive)

Trigger the reverse sync:

[http://localhost:8000/sync/reonic-to-pipedrive/projects](http://localhost:8000/sync/reonic-to-pipedrive/projects)

This fetches mocked Reonic projects, transforms them, and shows the POST payloads that would be sent to `/leads`.

## Sync Products (Reonic → Pipedrive)

Trigger the product sync:

[http://localhost:8000/sync/reonic-to-pipedrive/products](http://localhost:8000/sync/reonic-to-pipedrive/products)

It loads a mocked catalog from Reonic, converts them to Pipedrive product JSON, and returns the mocked POST bodies.

---

# Reonic → Pipedrive (Deals & Activities)

Reonic does **not** create Leads, but it can push updates to existing CRM Deals and Activities.

These endpoints simulate project → CRM sync flows.

[http://localhost:8000/reonic/push/deal-status](http://localhost:8000/reonic/push/deal-status)

## Update Deal Status (POST /reonic/push/deal-status)

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

Example use case:

* Engineering milestone reached → update CRM Deal stage/value.

---

## Create Activity (POST /reonic/push/activity)

[http://localhost:8000/reonic/push/activity](http://localhost:8000/reonic/push/activity)

This simulates Reonic logging an activity into Pipedrive, such as:

* Installation completed
* Site visit
* Maintenance
* Commissioning
* General notes

Typical fields:

* `subject`
* `type` (task, call, meeting, installation)
* `deal_id`
* `person_id`
* `due_date`
* `note`
* `reonic_project_id`

---

## Combined Project Update (POST /reonic/push/project-update)

[http://localhost:8000/reonic/push/project-update](http://localhost:8000/reonic/push/project-update)

This endpoint performs two mock actions:

1. **Updates a Deal** (stage/value/date/status)
2. **Creates an Activity** (log an event about the update)

Simulates how Reonic would inform CRM when a project hits a major milestone.

---

# Product Endpoints

## Add a Product (POST /products)

[http://localhost:8000/products](http://localhost:8000/products)

You can send the full Pipedrive-style JSON body, including price entries.

[http://localhost:8000/sync/reonic-to-pipedrive/products](http://localhost:8000/sync/reonic-to-pipedrive/products)

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

Returns mocked Pipedrive product payload:

```json
{
  "success": true,
  "data": {
    "id": 501,
    "name": "Test Product",
    "code": "PRD-001",
    "unit": "pcs",
    "prices": [...]
  }
}
```

---

# Organization Endpoint

## Add an Organization (POST /organizations)

[http://localhost:8000/organizations](http://localhost:8000/organizations)

This endpoint creates a mocked Pipedrive Organization.
It mirrors the official tutorial example (only `name` is required), but also accepts optional fields such as `owner_id`, `visible_to`, and `address`.

### Minimal example JSON

```json
{
  "name": "Org Inc test"
}
```

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

• All responses are fully mocked – no real requests are sent to Pipedrive.
• URL structure and JSON payloads match real Pipedrive API behavior.
• Safe for demos, onboarding, teaching API flows, and integration planning.
• Can be used to prototype Pipedrive → Reonic sync pipelines before building the real one.


