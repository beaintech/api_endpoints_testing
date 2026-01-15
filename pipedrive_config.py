import os

# IMPORTANT: replace with your REAL lead custom field key in Pipedrive
CF_REONIC_REQUEST_ID_KEY = os.getenv("CF_REONIC_REQUEST_ID_KEY", "cf_reonic_request_id")

# Pipedrive API token (Settings → Personal preferences → API)
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN", "YOUR_PIPEDRIVE_API_TOKEN_HERE")

# Your Pipedrive company subdomain, e.g. "acme" for https://acme.pipedrive.com
PIPEDRIVE_COMPANY_DOMAIN = os.getenv("PIPEDRIVE_COMPANY_DOMAIN", "yourcompany")

# Base URL without version suffix (v1/v2 will be appended by helpers)
PIPEDRIVE_BASE_URL = os.getenv(
    "PIPEDRIVE_BASE_URL",
    f"https://{PIPEDRIVE_COMPANY_DOMAIN}.pipedrive.com",
)