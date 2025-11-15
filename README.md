# Pipedrive Local Playground (FastAPI)

This is a local sandbox for testing Pipedrive OAuth callback and mock data exchange.

## Features
- `/callback` — Handles Pipedrive OAuth redirect and displays received code.
- `/mock/pipedrive` — Returns mocked Pipedrive deals.
- `/mock/saas` — Returns mocked SaaS project data.

## Run Locally
```bash
pip install fastapi "uvicorn[standard]"
uvicorn main:app --reload --port 5173
Test Endpoints
http://localhost:5173/callback?code=test

http://localhost:5173/mock/pipedrive

http://localhost:5173/mock/saas# api_endpoints_tesing
