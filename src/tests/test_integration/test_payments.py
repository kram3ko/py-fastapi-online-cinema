import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.fixture
def test_payment_data(test_order):
    return {
        "order_id": test_order.id
    }


@pytest.mark.asyncio
async def test_create_payment_intent_success(auth_user_client: AsyncClient, test_payment_data):
    response = await auth_user_client.post("/api/v1/payments/create-intent", json=test_payment_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "payment_url" in data
    assert "payment_id" in data
    assert "external_payment_id" in data


@pytest.mark.asyncio
async def test_create_payment_intent_negative_amount(auth_user_client: AsyncClient, test_order_negative_amount):
    response = await auth_user_client.post("/api/v1/payments/create-intent", json={"order_id": test_order_negative_amount.id})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_get_payment_history(auth_user_client: AsyncClient):
    response = await auth_user_client.get("/api/v1/payments/history")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
async def test_admin_get_payments(auth_admin_client: AsyncClient):
    response = await auth_admin_client.get("/api/v1/payments/admin")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
async def test_refund_payment_not_found(auth_admin_client: AsyncClient):
    response = await auth_admin_client.post("/api/v1/payments/99999/refund")
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
async def test_get_payment_details_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/payments/1")
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_get_statistics(auth_admin_client: AsyncClient):
    response = await auth_admin_client.get("/api/v1/payments/admin/statistics")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
