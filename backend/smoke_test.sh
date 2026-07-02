#!/usr/bin/env bash

cd /d/rent-flatmate-finder/backend || exit 1

# Remove old smoke database
rm -f smoke.db

# Temporary environment variables
export DATABASE_URL="sqlite:///./smoke.db"
export JWT_SECRET_KEY="testsecret"

./venv/Scripts/python.exe <<'EOF'

from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

print("=" * 60)
print("FASTAPI BACKEND SMOKE TEST")
print("=" * 60)

# ----------------------------
# Register Owner
# ----------------------------
r = client.post(
    "/auth/register",
    json={
        "name": "Owner A",
        "email": "owner@test.com",
        "password": "pass123",
        "role": "owner"
    }
)
print("Register Owner        :", r.status_code)

# ----------------------------
# Register Tenant
# ----------------------------
r = client.post(
    "/auth/register",
    json={
        "name": "Tenant A",
        "email": "tenant@test.com",
        "password": "pass123",
        "role": "tenant"
    }
)
print("Register Tenant       :", r.status_code)

# ----------------------------
# Owner Login
# ----------------------------
r = client.post(
    "/auth/login",
    data={
        "username": "owner@test.com",
        "password": "pass123"
    }
)

print("Owner Login           :", r.status_code)
owner_token = r.json()["access_token"]

# ----------------------------
# Tenant Login
# ----------------------------
r = client.post(
    "/auth/login",
    data={
        "username": "tenant@test.com",
        "password": "pass123"
    }
)

print("Tenant Login          :", r.status_code)
tenant_token = r.json()["access_token"]

owner_headers = {
    "Authorization": f"Bearer {owner_token}"
}

tenant_headers = {
    "Authorization": f"Bearer {tenant_token}"
}

# ----------------------------
# Create Listing
# ----------------------------
r = client.post(
    "/listings",
    headers=owner_headers,
    json={
        "location": "Kanpur Nagar",
        "rent": 8000,
        "available_from": "2026-07-15",
        "room_type": "single",
        "furnishing_status": "furnished",
        "photos": [],
        "description": "Nice room"
    }
)

print("Create Listing        :", r.status_code)
listing_id = r.json()["id"]

# ----------------------------
# Create Another Listing
# ----------------------------
r = client.post(
    "/listings",
    headers=owner_headers,
    json={
        "location": "Delhi",
        "rent": 30000,
        "available_from": "2027-01-01",
        "room_type": "1BHK",
        "furnishing_status": "unfurnished",
        "photos": [],
        "description": "Far and expensive"
    }
)

print("Create 2nd Listing    :", r.status_code)

# ----------------------------
# Tenant Preferences
# ----------------------------
r = client.put(
    "/tenants/profile",
    headers=tenant_headers,
    json={
        "preferred_location": "Kanpur Nagar",
        "budget_min": 6000,
        "budget_max": 9000,
        "move_in_date": "2026-07-20",
        "notes": "Quiet flatmate preferred"
    }
)

print("Tenant Profile Update :", r.status_code)

# ----------------------------
# Browse Listings
# ----------------------------
r = client.get(
    "/browse",
    headers=tenant_headers
)

print("Browse Listings       :", r.status_code)
print()

print("Browse Response")
print("-" * 60)
print(json.dumps(r.json(), indent=2, default=str))

# ----------------------------
# Cache Check
# ----------------------------
r2 = client.get(
    "/browse",
    headers=tenant_headers
)

same = (
    r.json()[0]["compatibility_score"] ==
    r2.json()[0]["compatibility_score"]
)

print()
print("Cached Score Same     :", same)

# ----------------------------
# Mark Filled
# ----------------------------
r = client.post(
    f"/listings/{listing_id}/mark-filled",
    headers=owner_headers
)

print("Mark Listing Filled   :", r.status_code)

# ----------------------------
# Verify Filled Listing Removed
# ----------------------------
r = client.get(
    "/browse",
    headers=tenant_headers
)

ids = [listing["id"] for listing in r.json()]

print(
    "Filled Listing Hidden :",
    listing_id not in ids
)

print("=" * 60)
print("SMOKE TEST COMPLETED")
print("=" * 60)

EOF