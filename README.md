# Pipedrive Local Playground (FastAPI)

This is a local sandbox for testing Pipedrive OAuth callback and mock data exchange.

## Features
- `/callback` — Handles Pipedrive OAuth redirect and displays received code.
- `/mock/pipedrive` — Returns mocked Pipedrive deals.
- `/mock/saas` — Returns mocked SaaS project data.

## Run Locally
```bash
pip install fastapi "uvicorn[standard]"

uvicorn main:app --reload --port 8000
Test Endpoints
http://localhost:8000/callback?code=test

http://localhost:8000/mock/pipedrive

http://localhost:8000/mock/saas# api_endpoints_tesing

http://localhost:8000/get_leads

http://localhost:8000/docs

http://localhost:8000/create_lead

http://localhost:8000/sync_leads

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
