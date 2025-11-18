import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from leads import router as leads_router
from products import router as products_router
from reonic_sync import router as reonic_router 

app = FastAPI()
app.include_router(leads_router, prefix="/leads", tags=["Leads"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(reonic_router, prefix="/reonic", tags=["Reonic Integration"])

# Note: in real use, set these as environment variables
PIPEDRIVE_CLIENT_ID = os.getenv("PIPEDRIVE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
PIPEDRIVE_CLIENT_SECRET = os.getenv("PIPEDRIVE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")
PIPEDRIVE_REDIRECT_URI = os.getenv("PIPEDRIVE_REDIRECT_URI", "http://localhost:8000/callback")

# Simple in-memory storage for demo only
oauth_tokens: dict[str, dict] = {}

def mock_pipedrive_token_exchange(code: str) -> dict:
    """
    Local mock for Pipedrive OAuth token exchange.
    Used ONLY in your playground instead of calling the real Pipedrive API.
    """
    return {
        "access_token": f"mock_access_token_for_{code}",
        "refresh_token": f"mock_refresh_token_for_{code}",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "deals:read deals:write contacts:read",
        "api_domain": "https://mockcompany.pipedrive.com",
        "user_id": 123456,
        "company_id": 78910,
        "client_id_used": PIPEDRIVE_CLIENT_ID,
        "redirect_uri_used": PIPEDRIVE_REDIRECT_URI,
    }

@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request):
    """
    EN: Receive the OAuth redirect from Pipedrive (?code=xxx),
        exchange the code for an access token and display it.
    DE: Empfängt die OAuth-Weiterleitung von Pipedrive (?code=xxx),
        tauscht den Code gegen ein Access-Token und zeigt es an.
    """
    params = dict(request.query_params)
    code = params.get("code")

    if not code:
        html = """
        <html><body>
          <h2>No OAuth code found in query parameters.</h2>
          <p>Expected something like ?code=ABC123 in the URL.</p>
        </body></html>
        """
        return HTMLResponse(content=html, status_code=400)

    # Mock token exchange instead of real HTTP call
    token_data = mock_pipedrive_token_exchange(code)
    oauth_tokens["pipedrive"] = token_data

    access_token = token_data.get("access_token", "(no access_token)")
    refresh_token = token_data.get("refresh_token", "(no refresh_token)")

    html = f"""
    <html>
      <body>
        <h2>Pipedrive OAuth callback – MOCK token generated</h2>
        <p><b>Code:</b> {code}</p>
        <p><b>Mock access token:</b> {access_token}</p>
        <p><b>Mock refresh token:</b> {refresh_token}</p>
        <h3>Raw mock token data:</h3>
        <pre>{token_data}</pre>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

# Here is the OAuth client ID and secret for Pipedrive.
@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback_simple(request: Request):
    """
    EN: Receive the OAuth redirect from Pipedrive (?code=xxx).
        This only displays the code and does not perform the real token exchange.
    DE: Empfängt die OAuth-Weiterleitung von Pipedrive (?code=xxx).
        Hier wird der Code nur angezeigt, ohne einen echten Token-Austausch durchzuführen.
    """
    params = dict(request.query_params)
    code = params.get("code", "(no code)")
    html = f"""
    <html>
      <body>
        <h2>Pipedrive OAuth callback received code / Empfangener Code:</h2>
        <p><b>{code}</b></p>
        <p>All query parameters / Alle Query-Parameter: {params}</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/mock/pipedrive")
async def mock_pipedrive():
    """
    EN: Mock data representing a typical Pipedrive response (e.g., list of deals).
    DE: Beispielhafte Mock-Daten, die eine typische Pipedrive-Antwort darstellen (z. B. eine Liste von Deals).
    """
    data = {
        "success": True,
        "data": [
            {
                "id": 1,
                "title": "Solar Project A / Solarprojekt A",
                "value": 10000,
                "currency": "EUR",
                "status": "open / offen",
            },
            {
                "id": 2,
                "title": "EV Charging Station B / Ladestation B",
                "value": 25000,
                "currency": "EUR",
                "status": "won / gewonnen",
            },
        ],
    }
    return JSONResponse(content=data)


@app.get("/mock/saas")
async def mock_saas():
    """
    EN: Mock data representing another SaaS system.
    DE: Beispielhafte Mock-Daten, die ein anderes SaaS-System darstellen.
    """
    data = {
        "projects": [
            {
                "project_id": "PRJ-1001",
                "name": "Reonic Site Münster",
                "monthly_fee": 199.0,
                "status": "active / aktiv",
            },
            {
                "project_id": "PRJ-1002",
                "name": "Reonic Site Düsseldorf",
                "monthly_fee": 299.0,
                "status": "draft / Entwurf",
            },
        ]
    }
    return JSONResponse(content=data)

@app.get("/tokens")
async def get_tokens():
    """
    EN: Simple endpoint to inspect stored tokens during local testing.
    DE: Einfaches Endpoint, um gespeicherte Tokens beim lokalen Testen anzusehen.
    """
    return JSONResponse(content=oauth_tokens)