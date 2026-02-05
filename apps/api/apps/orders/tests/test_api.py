"""Tests for order API endpoints."""

import pytest

from apps.orders.models import Order, OrderStatus, Table


@pytest.mark.django_db
class TestTableAPI:
    """Tests for the Table API endpoints."""

    def test_list_tables(self, owner_client, owner, table_factory):
        """Test listing tables."""
        table_factory(business=owner.business, number="1")
        table_factory(business=owner.business, number="2")

        response = owner_client.get("/api/v1/tables/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_list_tables_requires_auth(self, api_client):
        """Test listing tables requires authentication."""
        response = api_client.get("/api/v1/tables/")
        assert response.status_code == 401

    def test_create_table_as_owner(self, owner_client, owner):
        """Test owner can create table."""
        data = {"number": "T1", "capacity": 6}
        response = owner_client.post("/api/v1/tables/", data)
        assert response.status_code == 201
        assert response.data["number"] == "T1"
        assert response.data["capacity"] == 6

        # Verify business assignment
        table = Table.all_objects.get(id=response.data["id"])
        assert table.business == owner.business

    def test_create_table_as_cashier_forbidden(self, cashier_client, cashier):
        """Test cashier cannot create table."""
        data = {"number": "T1", "capacity": 4}
        response = cashier_client.post("/api/v1/tables/", data)
        assert response.status_code == 403

    def test_filter_tables_by_active(self, owner_client, owner, table_factory):
        """Test filtering tables by active status."""
        table_factory(business=owner.business, number="1", is_active=True)
        table_factory(business=owner.business, number="2", is_active=False)

        response = owner_client.get("/api/v1/tables/?is_active=true")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["number"] == "1"


@pytest.mark.django_db
class TestOrderAPI:
    """Tests for the Order API endpoints."""

    def test_list_orders(self, owner_client, owner, order_factory, cashier_factory):
        """Test listing orders."""
        cashier = cashier_factory(business=owner.business)
        order_factory(business=owner.business, cashier=cashier, order_type="takeaway")
        order_factory(business=owner.business, cashier=cashier, order_type="takeaway")

        response = owner_client.get("/api/v1/orders/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_list_orders_requires_auth(self, api_client):
        """Test listing orders requires authentication."""
        response = api_client.get("/api/v1/orders/")
        assert response.status_code == 401

    def test_create_order_dine_in(self, cashier_client, sample_order_data, cashier):
        """Test cashier can create dine-in order."""
        # Update cashier to sample business
        cashier.business = sample_order_data["business"]
        cashier.save()

        data = {
            "order_type": "dine_in",
            "table_id": str(sample_order_data["table"].id),
            "customer_name": "John Doe",
            "items": [
                {
                    "menu_item_id": str(sample_order_data["burger"].id),
                    "quantity": 2,
                    "modifiers": [
                        {"modifier_option_id": str(sample_order_data["large_option"].id)}
                    ],
                },
                {
                    "menu_item_id": str(sample_order_data["fries"].id),
                    "quantity": 1,
                },
            ],
        }

        response = cashier_client.post("/api/v1/orders/", data, format="json")
        assert response.status_code == 201
        assert response.data["order_number"] == 1
        assert response.data["order_type"] == "dine_in"
        assert response.data["customer_name"] == "John Doe"
        assert len(response.data["items"]) == 2

        # Check totals: burger (5000 + 500 Large) * 2 = 11000, fries 2000 = 13000
        assert response.data["subtotal"] == 13000
        assert response.data["total"] == 13000

    def test_create_order_takeaway(self, cashier_client, sample_order_data, cashier):
        """Test creating takeaway order (no table required)."""
        cashier.business = sample_order_data["business"]
        cashier.save()

        data = {
            "order_type": "takeaway",
            "items": [
                {
                    "menu_item_id": str(sample_order_data["burger"].id),
                    "quantity": 1,
                },
            ],
        }

        response = cashier_client.post("/api/v1/orders/", data, format="json")
        assert response.status_code == 201
        assert response.data["order_type"] == "takeaway"
        assert response.data["table"] is None

    def test_create_order_dine_in_requires_table(
        self, cashier_client, sample_order_data, cashier
    ):
        """Test dine-in order requires table."""
        cashier.business = sample_order_data["business"]
        cashier.save()

        data = {
            "order_type": "dine_in",
            # No table_id
            "items": [
                {
                    "menu_item_id": str(sample_order_data["burger"].id),
                    "quantity": 1,
                },
            ],
        }

        response = cashier_client.post("/api/v1/orders/", data, format="json")
        assert response.status_code == 400
        assert "table_id" in response.data

    def test_create_order_requires_items(self, cashier_client, sample_order_data, cashier):
        """Test order requires at least one item."""
        cashier.business = sample_order_data["business"]
        cashier.save()

        data = {
            "order_type": "takeaway",
            "items": [],
        }

        response = cashier_client.post("/api/v1/orders/", data, format="json")
        assert response.status_code == 400

    def test_create_order_invalid_menu_item(
        self, cashier_client, sample_order_data, cashier
    ):
        """Test order fails with invalid menu item."""
        cashier.business = sample_order_data["business"]
        cashier.save()

        data = {
            "order_type": "takeaway",
            "items": [
                {
                    "menu_item_id": "00000000-0000-0000-0000-000000000000",
                    "quantity": 1,
                },
            ],
        }

        response = cashier_client.post("/api/v1/orders/", data, format="json")
        assert response.status_code == 400

    def test_create_order_with_discount(
        self, cashier_client, sample_order_data, cashier
    ):
        """Test creating order with discount."""
        cashier.business = sample_order_data["business"]
        cashier.save()

        data = {
            "order_type": "takeaway",
            "discount": 1000,
            "items": [
                {
                    "menu_item_id": str(sample_order_data["burger"].id),
                    "quantity": 1,
                },
            ],
        }

        response = cashier_client.post("/api/v1/orders/", data, format="json")
        assert response.status_code == 201
        assert response.data["discount"] == 1000
        assert response.data["subtotal"] == 5000
        assert response.data["total"] == 4000  # 5000 - 1000

    def test_retrieve_order(self, owner_client, owner, order_factory, cashier_factory):
        """Test retrieving order details."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(business=owner.business, cashier=cashier, order_type="takeaway")

        response = owner_client.get(f"/api/v1/orders/{order.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(order.id)

    def test_filter_orders_by_status(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test filtering orders by status."""
        cashier = cashier_factory(business=owner.business)
        order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.PENDING,
            order_type="takeaway",
        )
        order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.COMPLETED,
            order_type="takeaway",
        )

        response = owner_client.get("/api/v1/orders/?status=pending")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == "pending"


@pytest.mark.django_db
class TestOrderStatusUpdateAPI:
    """Tests for the order status update endpoint."""

    def test_update_status_pending_to_preparing(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test updating order from pending to preparing."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.PENDING,
            order_type="takeaway",
        )

        response = owner_client.patch(
            f"/api/v1/orders/{order.id}/status/",
            {"status": "preparing"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "preparing"

    def test_update_status_preparing_to_ready(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test updating order from preparing to ready."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.PREPARING,
            order_type="takeaway",
        )

        response = owner_client.patch(
            f"/api/v1/orders/{order.id}/status/",
            {"status": "ready"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "ready"

    def test_update_status_ready_to_completed(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test updating order from ready to completed."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.READY,
            order_type="takeaway",
        )

        response = owner_client.patch(
            f"/api/v1/orders/{order.id}/status/",
            {"status": "completed"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "completed"
        assert response.data["completed_at"] is not None

    def test_cancel_order_requires_reason(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test cancelling order requires reason."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.PENDING,
            order_type="takeaway",
        )

        response = owner_client.patch(
            f"/api/v1/orders/{order.id}/status/",
            {"status": "cancelled"},
            format="json",
        )
        assert response.status_code == 400
        assert "cancelled_reason" in response.data

    def test_cancel_order_with_reason(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test cancelling order with reason."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.PENDING,
            order_type="takeaway",
        )

        response = owner_client.patch(
            f"/api/v1/orders/{order.id}/status/",
            {"status": "cancelled", "cancelled_reason": "Customer changed mind"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "cancelled"
        assert response.data["cancelled_reason"] == "Customer changed mind"
        assert response.data["cancelled_at"] is not None

    def test_invalid_status_transition(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test invalid status transitions are rejected."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(
            business=owner.business,
            cashier=cashier,
            status=OrderStatus.PENDING,
            order_type="takeaway",
        )

        # Cannot go directly from pending to completed
        response = owner_client.patch(
            f"/api/v1/orders/{order.id}/status/",
            {"status": "completed"},
            format="json",
        )
        assert response.status_code == 400
        assert "status" in response.data


@pytest.mark.django_db
class TestKitchenQueueAPI:
    """Tests for the kitchen queue endpoint."""

    def test_kitchen_queue_returns_pending_and_preparing(
        self, kitchen_client, kitchen_user, order_factory, cashier_factory
    ):
        """Test kitchen queue returns pending and preparing orders."""
        cashier = cashier_factory(business=kitchen_user.business)
        order_factory(
            business=kitchen_user.business,
            cashier=cashier,
            status=OrderStatus.PENDING,
            order_type="takeaway",
        )
        order_factory(
            business=kitchen_user.business,
            cashier=cashier,
            status=OrderStatus.PREPARING,
            order_type="takeaway",
        )
        order_factory(
            business=kitchen_user.business,
            cashier=cashier,
            status=OrderStatus.COMPLETED,
            order_type="takeaway",
        )

        response = kitchen_client.get("/api/v1/kitchen-queue/")
        assert response.status_code == 200
        assert len(response.data) == 2  # Only pending and preparing

    def test_kitchen_queue_requires_auth(self, api_client):
        """Test kitchen queue requires authentication."""
        response = api_client.get("/api/v1/kitchen-queue/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestMultiTenantOrderIsolation:
    """Tests for multi-tenant order isolation."""

    def test_user_cannot_see_other_business_orders(
        self,
        owner_client,
        owner,
        order_factory,
        business_factory,
        cashier_factory,
    ):
        """Test user cannot access another business's orders."""
        other_business = business_factory()
        other_cashier = cashier_factory(business=other_business)

        # Create order for another business
        order_factory(
            business=other_business,
            cashier=other_cashier,
            order_type="takeaway",
        )

        # Create order for owner's business
        owner_cashier = cashier_factory(business=owner.business)
        order_factory(
            business=owner.business,
            cashier=owner_cashier,
            order_type="takeaway",
        )

        response = owner_client.get("/api/v1/orders/")
        assert response.status_code == 200
        assert response.data["count"] == 1
