import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from leads import router as leads_router
from products import router as products_router
from reonic_sync import router as reonic_router 
from pipedrive_sync import router as pipedrive_router
from organization import router as rorganization_router 

app = FastAPI()
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(rorganization_router, prefix="/organization", tags=["organization"])

app.include_router(pipedrive_router, tags=["Pipedrive Integration"])
app.include_router(reonic_router, tags=["Reonic Integration"])
