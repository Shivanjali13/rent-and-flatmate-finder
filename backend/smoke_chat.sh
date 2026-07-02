#!/usr/bin/env bash

cd /d/rent-flatmate-finder/backend || exit 1

rm -f smoke3.db

export DATABASE_URL="sqlite:///./smoke3.db"
export JWT_SECRET_KEY="testsecret"
export RESEND_API_KEY=""

./venv/Scripts/python.exe <<'EOF'

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("WEBSOCKET CHAT SMOKE TEST")
print("=" * 60)

# ----------------------------
# Register users
# ----------------------------
client.post(
    "/auth/register",
    json={
        "name": "Owner A",
        "email": "owner@test.com",
        "password": "pass123",
        "role": "owner"
    }
)

client.post(
    "/auth/register",
    json={
        "name": "Tenant A",
        "email": "tenant@test.com",
        "password": "pass123",
        "role": "tenant"
    }
)

# ----------------------------
# Login
# ----------------------------
owner_token = client.post(
    "/auth/login",
    data={
        "username": "owner@test.com",
        "password": "pass123"
    }
).json()["access_token"]

tenant_token = client.post(
    "/auth/login",
    data={
        "username": "tenant@test.com",
        "password": "pass123"
    }
).json()["access_token"]

owner_headers = {
    "Authorization": f"Bearer {owner_token}"
}

tenant_headers = {
    "Authorization": f"Bearer {tenant_token}"
}

# ----------------------------
# Create listing
# ----------------------------
listing = client.post(
    "/listings",
    headers=owner_headers,
    json={
        "location": "Kanpur",
        "rent": 8000,
        "available_from": "2026-07-15",
        "room_type": "single",
        "furnishing_status": "furnished",
        "photos": [],
        "description": "Nice room"
    }
)

listing_id = listing.json()["id"]

# ----------------------------
# Tenant profile
# ----------------------------
client.put(
    "/tenants/profile",
    headers=tenant_headers,
    json={
        "preferred_location": "Kanpur",
        "budget_min": 6000,
        "budget_max": 9000,
        "move_in_date": "2026-07-20",
        "notes": "Quiet flatmate"
    }
)

# ----------------------------
# Express interest
# ----------------------------
interest = client.post(
    "/interests",
    headers=tenant_headers,
    json={
        "listing_id": listing_id
    }
)

interest_id = interest.json()["id"]

# ----------------------------
# Owner accepts
# ----------------------------
client.patch(
    f"/interests/{interest_id}",
    headers=owner_headers,
    json={
        "status": "accepted"
    }
)

print("Interest accepted")

# ----------------------------
# Open WebSockets
# ----------------------------
with client.websocket_connect(
    f"/ws/chat/{interest_id}?token={tenant_token}"
) as tenant_ws:

    with client.websocket_connect(
        f"/ws/chat/{interest_id}?token={owner_token}"
    ) as owner_ws:

        print("Both WebSockets connected")

        tenant_ws.send_json({
            "content": "Hi, is this still available?"
        })

        tenant_copy = tenant_ws.receive_json()
        owner_copy = owner_ws.receive_json()

        print("Tenant received:", tenant_copy["content"])
        print("Owner received :", owner_copy["content"])

        owner_ws.send_json({
            "content": "Yes, it is available."
        })

        owner_reply = owner_ws.receive_json()
        tenant_reply = tenant_ws.receive_json()

        print("Owner received :", owner_reply["content"])
        print("Tenant received:", tenant_reply["content"])

# ----------------------------
# Verify persistence
# ----------------------------
history = client.get(
    f"/interests/{interest_id}/messages",
    headers=tenant_headers
)

messages = history.json()

print()
print("Persisted Messages:", len(messages))

for msg in messages:
    print(
        f"{msg['sender_id']} -> {msg['content']}"
    )

assert len(messages) == 2

print()
print("=" * 60)
print("WEBSOCKET TEST PASSED")
print("=" * 60)

EOF

rm -f smoke3.db