import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "doc_test@example.com",
            "password": "StrongPass123",
            "department_id": 1,
            "role_id": 3,
        },
    )
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


@pytest.mark.asyncio
async def test_upload_rejects_content_type_mismatch(client):
    """A .pdf whose bytes are plain text must be rejected (magic-byte check)."""
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("fake.pdf", b"This is definitely not a PDF", "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "does not match" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_empty_file(client):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_and_delete_are_audited(client, db_session):
    """Upload + RBAC-denied delete must produce readable audit rows."""
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    upload_resp = await client.post(
        "/api/v1/documents",
        files={"file": ("audit.txt", b"audited content", "text/plain")},
        headers=headers,
    )
    assert upload_resp.status_code == 200
    doc_id = upload_resp.json()["id"]

    # Non-admin attempts admin-only delete -> rbac_denied audit row.
    denied = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert denied.status_code == 403

    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    result = await db_session.execute(select(AuditLog).order_by(AuditLog.id))
    logs = result.scalars().all()
    actions = [log.action for log in logs]

    assert "upload" in actions
    assert "rbac_denied" in actions
