from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request):
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
