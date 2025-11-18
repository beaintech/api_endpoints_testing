# Pipedrive Local Playground (FastAPI)

A fully local sandbox for simulating Pipedrive API calls using mocked data.  
This playground is designed for demonstrating how Pipedrive → Reonic integrations work **without requiring real credentials**.

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

## Test Endpoints

### OAuth Callback Test
http://localhost:8000/callback?code=test

### Mock Data Endpoints
http://localhost:8000/mock/pipedrive  
http://localhost:8000/mock/saas

### Pipedrive Mock Endpoints
```
GET    /get_leads
GET    /get_lead/{lead_id}
POST   /create_lead
PATCH  /update_lead/{lead_id}
DELETE /delete_lead/{lead_id}
POST   /sync_leads
POST   /sync_reonic_to_pipedrive

POST   /add_product
POST   /sync_reonic_products
```

### Swagger UI
http://localhost:8000/docs

---

## POST Examples (Leads)

### Create a Lead (POST /create_lead)

Open Swagger UI:  
http://localhost:8000/docs

POST → `/create_lead` → “Try it out” → paste:
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

---

## Update a Lead (PATCH /update_lead/{lead_id})
http://localhost:8000/update_lead/101

Example body:
{
  "title": "Updated Lead Title",
  "amount": 5000,
  "currency": "EUR"
}

All fields are optional.

---

## Delete a Lead (DELETE /delete_lead/{lead_id})
http://localhost:8000/delete_lead/101


Returns:
{
  "success": true,
  "data": { "id": 101, "deleted": true }
}

---

## Fetch a Single Lead (GET /get_lead/{lead_id})
http://localhost:8000/get_lead/101

---

## Sync Leads (Pipedrive → Reonic)

Trigger the sync:

http://localhost:8000/sync_leads

This endpoint does **not** require a request body.

## Sync Projects (Reonic → Pipedrive)

Trigger the reverse sync:

http://localhost:8000/sync_reonic_to_pipedrive

This fetches mocked Reonic projects, transforms them, and shows the POST payloads that would be sent to `/leads`.

## Sync Products (Reonic → Pipedrive)

Trigger the product sync:

http://localhost:8000/sync_reonic_products

It loads a mocked catalog from Reonic, converts them to Pipedrive product JSON, and returns the mocked POST bodies.

---

# Reonic → Pipedrive (Deals & Activities)

Reonic does **not** create Leads, but it can push updates to existing CRM Deals and Activities.

These endpoints simulate project → CRM sync flows.

## Update Deal Status (POST /reonic_push_status_to_pipedrive)

This endpoint simulates sending project progress from Reonic to an existing Pipedrive Deal.

Typical updated fields:
- `stage_id`
- `status`
- `probability`
- `value_amount` / `value_currency`
- `expected_close_date`
- `technical_status`
- `reonic_project_id`

Example use case:
- Engineering milestone reached → update CRM Deal stage/value.

---

## Create Activity (POST /reonic_push_activity_to_pipedrive)

This simulates Reonic logging an activity into Pipedrive, such as:

- Installation completed  
- Site visit  
- Maintenance  
- Commissioning  
- General notes  

Typical fields:
- `subject`
- `type` (task, call, meeting, installation)
- `deal_id`
- `person_id`
- `due_date`
- `note`
- `reonic_project_id`

---

## Combined Project Update (POST /reonic_push_project_update)

This endpoint performs two mock actions:

1. **Updates a Deal** (stage/value/date/status)  
2. **Creates an Activity** (log an event about the update)  

Simulates how Reonic would inform CRM when a project hits a major milestone.

---

# Product Endpoints

## Add a Product (POST /add_product)

You can send the full Pipedrive-style JSON body, including price entries.

Example JSON:
```
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
```
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

## Notes

• All responses are fully mocked – no real requests are sent to Pipedrive.  
• URL structure and JSON payloads match real Pipedrive API behavior.  
• Safe for demos, onboarding, teaching API flows, and integration planning.  
• Can be used to prototype Pipedrive → Reonic sync pipelines before building the real one.

