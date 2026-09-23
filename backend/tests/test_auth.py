import pytest
from httpx import AsyncClient

import uuid

@pytest.mark.asyncio
async def test_register_flow(client: AsyncClient):
    uid = uuid.uuid4().hex[:6]
    test_email = f"david_{uid}@newstartup.io"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "David Founder",
            "email": test_email,
            "password": "SecurePassword123!",
            "organization_name": f"New Startup {uid}"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["email"] == test_email
    assert data["data"]["user"]["role"] == "ORGANIZATION_ADMIN"

@pytest.mark.asyncio
async def test_login_flow(client: AsyncClient, seeded_org_and_users):
    admin_email = seeded_org_and_users["admin1"].email
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "Password123!"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    access_token = data["data"]["access_token"]
    refresh_token = data["data"]["refresh_token"]

    # Verify /me endpoint with token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == admin_email

    # Refresh token rotation
    ref_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert ref_resp.status_code == 200
    ref_data = ref_resp.json()["data"]
    assert ref_data["access_token"] != access_token

@pytest.mark.asyncio
async def test_invalid_login_rejection(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@test.com", "password": "BadPassword"}
    )
    assert resp.status_code == 401
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"
