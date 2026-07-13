import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "doc_test@example.com",
        "password": "Pass123",
        "department_id": 1,
        "role_id": 3,
    })
    data = resp.json()
    return data.get("access_token", "")


@pytest.mark.asyncio
async def test_upload_document(client):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", b"Hello, this is a test document content", "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_documents(client):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/documents",
        files={"file": ("doc1.txt", b"Content of doc 1", "text/plain")},
        headers=headers,
    )

    resp = await client.get("/api/v1/documents", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
