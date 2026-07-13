import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/register", json={
        "name": "Chat User",
        "email": "chat_test@example.com",
        "password": "Pass123",
        "department_id": 1,
        "role_id": 3,
    })
    return resp.json().get("access_token", "")


@pytest.mark.asyncio
async def test_chat_endpoint(client):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/chat",
        json={"question": "What is our company policy?"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "session_id" in data
    assert "sources" in data


@pytest.mark.asyncio
async def test_search_endpoint(client):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/search",
        json={"query": "company policy", "top_k": 3},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "total" in data
