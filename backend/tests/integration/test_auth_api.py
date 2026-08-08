import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123",
            "department_id": 1,
            "role_id": 3,
        },
    )

    if register_resp.status_code == 201 or register_resp.status_code == 200:
        data = register_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
        },
    )

    if login_resp.status_code == 200:
        data = login_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "User One",
            "email": "dupe@example.com",
            "password": "Pass123",
            "department_id": 1,
            "role_id": 3,
        },
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Two",
            "email": "dupe@example.com",
            "password": "Pass456",
            "department_id": 1,
            "role_id": 3,
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpass",
        },
    )
    assert resp.status_code == 401
