from decimal import Decimal

import pytest
from django.urls import reverse

from apps.inventory.models import MovementReason, MovementType, StockItem, StockMovement

pytestmark = pytest.mark.django_db


class TestStockItemAPI:
    """Tests for the StockItem API endpoints."""

    def test_list_stock_items_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list stock items."""
        url = reverse("stock-item-list")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_list_stock_items_authenticated(self, owner_client, sample_inventory):
        """Test listing stock items for authenticated user."""
        url = reverse("stock-item-list")
        response = owner_client.get(url)

        assert response.status_code == 200
        # Should see all items from their restaurant (including inactive)
        assert response.data["count"] == 5

    def test_list_stock_items_filter_active(self, owner_client, sample_inventory):
        """Test filtering stock items by active status."""
        url = reverse("stock-item-list")
        response = owner_client.get(url, {"is_active": "true"})

        assert response.status_code == 200
        # Should only see active items
        assert response.data["count"] == 4

    def test_retrieve_stock_item(self, owner_client, sample_stock_item):
        """Test retrieving a single stock item."""
        url = reverse("stock-item-detail", kwargs={"pk": sample_stock_item.id})
        response = owner_client.get(url)

        assert response.status_code == 200
        assert response.data["name"] == "Tomatoes"
        assert response.data["sku"] == "TOM-001"
        assert response.data["unit"] == "kg"

    def test_create_stock_item(self, owner_client, owner):
        """Test creating a new stock item."""
        url = reverse("stock-item-list")
        data = {
            "name": "New Item",
            "sku": "NEW-001",
            "unit": "piece",
            "low_stock_threshold": "10.0000",
        }
        response = owner_client.post(url, data)

        assert response.status_code == 201
        assert response.data["name"] == "New Item"
        assert response.data["current_quantity"] == "0.0000"

        # Verify in database
        item = StockItem.all_objects.get(id=response.data["id"])
        assert item.restaurant == owner.restaurant

    def test_create_stock_item_cashier_forbidden(self, cashier_client):
        """Test that cashiers cannot create stock items."""
        url = reverse("stock-item-list")
        data = {
            "name": "Forbidden Item",
            "sku": "FORBIDDEN-001",
            "unit": "piece",
        }
        response = cashier_client.post(url, data)

        assert response.status_code == 403

    def test_update_stock_item(self, owner_client, sample_stock_item):
        """Test updating a stock item (not quantity)."""
        url = reverse("stock-item-detail", kwargs={"pk": sample_stock_item.id})
        data = {
            "name": "Updated Tomatoes",
            "sku": "TOM-002",
            "unit": "kg",
        }
        response = owner_client.patch(url, data)

        assert response.status_code == 200
        assert response.data["name"] == "Updated Tomatoes"
        assert response.data["sku"] == "TOM-002"

    def test_delete_stock_item(self, owner_client, sample_stock_item):
        """Test deleting a stock item."""
        url = reverse("stock-item-detail", kwargs={"pk": sample_stock_item.id})
        response = owner_client.delete(url)

        assert response.status_code == 204
        assert not StockItem.all_objects.filter(id=sample_stock_item.id).exists()

    def test_tenant_isolation(self, owner_client, owner):
        """Test that users can only see their own restaurant's items."""
        from apps.authentication.tests.factories import RestaurantFactory
        from apps.inventory.tests.factories import StockItemFactory

        # Create a completely separate restaurant
        other_restaurant = RestaurantFactory()

        # Create item in owner's restaurant
        owner_item = StockItemFactory(restaurant=owner.restaurant, name="Owner Item")

        # Create item in other restaurant
        other_item = StockItemFactory(restaurant=other_restaurant, name="Other Item")

        # Owner should only see their own items
        url = reverse("stock-item-list")
        response = owner_client.get(url)

        assert response.status_code == 200
        item_ids = [item["id"] for item in response.data["results"]]
        assert str(owner_item.id) in item_ids
        assert str(other_item.id) not in item_ids


class TestAddStockAction:
    """Tests for the add_stock action."""

    def test_add_stock_success(self, owner_client, sample_stock_item, owner):
        """Test successfully adding stock."""
        initial_quantity = Decimal(sample_stock_item.current_quantity)
        url = reverse("stock-item-add-stock", kwargs={"pk": sample_stock_item.id})
        data = {
            "quantity": "25.0000",
            "reason": "purchase",
            "notes": "Weekly delivery",
        }
        response = owner_client.post(url, data)

        assert response.status_code == 200

        # Verify quantity increased
        expected_quantity = initial_quantity + Decimal("25.0000")
        assert Decimal(response.data["current_quantity"]) == expected_quantity

        # Verify movement record created
        movement = StockMovement.all_objects.filter(stock_item=sample_stock_item).first()
        assert movement is not None
        assert movement.quantity_change == Decimal("25.0000")
        assert movement.movement_type == MovementType.IN
        assert movement.reason == MovementReason.PURCHASE
        assert movement.notes == "Weekly delivery"
        assert movement.created_by == owner

    def test_add_stock_invalid_quantity(self, owner_client, sample_stock_item):
        """Test adding stock with invalid (zero or negative) quantity."""
        url = reverse("stock-item-add-stock", kwargs={"pk": sample_stock_item.id})
        data = {
            "quantity": "-5.0000",
            "reason": "purchase",
        }
        response = owner_client.post(url, data)

        assert response.status_code == 400

    def test_add_stock_cashier_forbidden(self, cashier_client, sample_stock_item):
        """Test that cashiers cannot add stock."""
        url = reverse("stock-item-add-stock", kwargs={"pk": sample_stock_item.id})
        data = {
            "quantity": "10.0000",
            "reason": "purchase",
        }
        response = cashier_client.post(url, data)

        assert response.status_code == 403


class TestAdjustStockAction:
    """Tests for the adjust stock action."""

    def test_adjust_stock_increase(self, owner_client, sample_stock_item, owner):
        """Test adjusting stock upward (physical count higher)."""
        url = reverse("stock-item-adjust", kwargs={"pk": sample_stock_item.id})
        data = {
            "new_quantity": "75.0000",
            "reason": "correction",
            "notes": "Physical inventory count",
        }
        response = owner_client.post(url, data)

        assert response.status_code == 200
        assert Decimal(response.data["current_quantity"]) == Decimal("75.0000")

        # Verify movement record
        movement = StockMovement.all_objects.filter(
            stock_item=sample_stock_item,
            movement_type=MovementType.ADJUSTMENT,
        ).first()
        assert movement is not None
        # Original was 50, new is 75, so change is +25
        assert movement.quantity_change == Decimal("25.0000")

    def test_adjust_stock_decrease(self, owner_client, sample_stock_item):
        """Test adjusting stock downward (physical count lower)."""
        url = reverse("stock-item-adjust", kwargs={"pk": sample_stock_item.id})
        data = {
            "new_quantity": "40.0000",
            "reason": "waste",
            "notes": "Spoilage discovered",
        }
        response = owner_client.post(url, data)

        assert response.status_code == 200
        assert Decimal(response.data["current_quantity"]) == Decimal("40.0000")

        # Verify movement record
        movement = StockMovement.all_objects.filter(
            stock_item=sample_stock_item,
            movement_type=MovementType.ADJUSTMENT,
        ).first()
        assert movement is not None
        # Original was 50, new is 40, so change is -10
        assert movement.quantity_change == Decimal("-10.0000")

    def test_adjust_stock_no_change(self, owner_client, sample_stock_item):
        """Test adjusting to same quantity creates no movement."""
        initial_count = StockMovement.all_objects.filter(
            stock_item=sample_stock_item
        ).count()

        url = reverse("stock-item-adjust", kwargs={"pk": sample_stock_item.id})
        data = {
            "new_quantity": "50.0000",  # Same as current
            "reason": "correction",
        }
        response = owner_client.post(url, data)

        assert response.status_code == 200

        # No new movement should be created
        new_count = StockMovement.all_objects.filter(stock_item=sample_stock_item).count()
        assert new_count == initial_count

    def test_adjust_stock_negative_fails(self, owner_client, sample_stock_item):
        """Test that negative quantity is rejected."""
        url = reverse("stock-item-adjust", kwargs={"pk": sample_stock_item.id})
        data = {
            "new_quantity": "-5.0000",
            "reason": "correction",
        }
        response = owner_client.post(url, data)

        assert response.status_code == 400


class TestMovementsEndpoint:
    """Tests for the stock item movements endpoint."""

    def test_get_movements_for_item(self, owner_client, sample_stock_item, owner):
        """Test getting movement history for a specific item."""
        # Create some movements via the add_stock action
        add_url = reverse("stock-item-add-stock", kwargs={"pk": sample_stock_item.id})
        owner_client.post(add_url, {"quantity": "10.0000", "reason": "purchase"})
        owner_client.post(add_url, {"quantity": "5.0000", "reason": "purchase"})

        # Get movements
        url = reverse("stock-item-movements", kwargs={"pk": sample_stock_item.id})
        response = owner_client.get(url)

        assert response.status_code == 200
        # Should have 2 movements
        assert len(response.data["results"]) == 2

        # Most recent first
        assert Decimal(response.data["results"][0]["quantity_change"]) == Decimal("5.0000")
        assert Decimal(response.data["results"][1]["quantity_change"]) == Decimal("10.0000")


class TestStockMovementAPI:
    """Tests for the StockMovement API endpoints."""

    def test_list_movements_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list movements."""
        url = reverse("stock-movement-list")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_list_movements_authenticated(self, owner_client, sample_stock_item, owner):
        """Test listing movements for authenticated user."""
        # Create a movement
        StockMovement.all_objects.create(
            restaurant=sample_stock_item.restaurant,
            stock_item=sample_stock_item,
            quantity_change=Decimal("10.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            balance_after=Decimal("60.0000"),
            created_by=owner,
        )

        url = reverse("stock-movement-list")
        response = owner_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] >= 1

    def test_filter_movements_by_stock_item(self, owner_client, sample_inventory, owner):
        """Test filtering movements by stock item."""
        tomatoes = sample_inventory["items"]["tomatoes"]
        onions = sample_inventory["items"]["onions"]

        # Create movements for different items
        StockMovement.all_objects.create(
            restaurant=tomatoes.restaurant,
            stock_item=tomatoes,
            quantity_change=Decimal("10.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            balance_after=Decimal("60.0000"),
            created_by=owner,
        )
        StockMovement.all_objects.create(
            restaurant=onions.restaurant,
            stock_item=onions,
            quantity_change=Decimal("5.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            balance_after=Decimal("35.0000"),
            created_by=owner,
        )

        # Filter by tomatoes
        url = reverse("stock-movement-list")
        response = owner_client.get(url, {"stock_item": str(tomatoes.id)})

        assert response.status_code == 200
        # Should only show tomatoes movements
        for movement in response.data["results"]:
            assert str(movement["stock_item"]) == str(tomatoes.id)

    def test_filter_movements_by_type(self, owner_client, sample_stock_item, owner):
        """Test filtering movements by movement type."""
        # Create different types of movements
        StockMovement.all_objects.create(
            restaurant=sample_stock_item.restaurant,
            stock_item=sample_stock_item,
            quantity_change=Decimal("10.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            balance_after=Decimal("60.0000"),
            created_by=owner,
        )
        StockMovement.all_objects.create(
            restaurant=sample_stock_item.restaurant,
            stock_item=sample_stock_item,
            quantity_change=Decimal("-5.0000"),
            movement_type=MovementType.OUT,
            reason=MovementReason.ORDER_USAGE,
            balance_after=Decimal("55.0000"),
            created_by=owner,
        )

        # Filter by IN type
        url = reverse("stock-movement-list")
        response = owner_client.get(url, {"movement_type": "in"})

        assert response.status_code == 200
        for movement in response.data["results"]:
            assert movement["movement_type"] == "in"

    def test_movements_read_only(self, owner_client, sample_stock_item, owner):
        """Test that movements cannot be created directly via API."""
        url = reverse("stock-movement-list")
        data = {
            "stock_item": str(sample_stock_item.id),
            "quantity_change": "10.0000",
            "movement_type": "in",
            "reason": "purchase",
            "balance_after": "60.0000",
        }
        response = owner_client.post(url, data)

        # Should not allow POST (read-only viewset)
        assert response.status_code == 405

    def test_movement_tenant_isolation(self, owner_client, owner):
        """Test that users can only see their own restaurant's movements."""
        from apps.authentication.tests.factories import RestaurantFactory
        from apps.inventory.tests.factories import StockItemFactory

        # Create a completely separate restaurant
        other_restaurant = RestaurantFactory()

        # Create items in each restaurant
        owner_item = StockItemFactory(restaurant=owner.restaurant, name="Owner Item")
        other_item = StockItemFactory(restaurant=other_restaurant, name="Other Item")

        # Create movement in owner's restaurant
        owner_movement = StockMovement.all_objects.create(
            restaurant=owner.restaurant,
            stock_item=owner_item,
            quantity_change=Decimal("10.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            balance_after=Decimal("110.0000"),
            created_by=owner,
        )

        # Create movement in other restaurant
        StockMovement.all_objects.create(
            restaurant=other_restaurant,
            stock_item=other_item,
            quantity_change=Decimal("5.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            balance_after=Decimal("105.0000"),
            created_by=None,  # No user for other restaurant
        )

        # Owner should only see their own movements
        url = reverse("stock-movement-list")
        response = owner_client.get(url)

        assert response.status_code == 200
        # Should only see movements from owner's restaurant
        movement_stock_items = [str(m["stock_item"]) for m in response.data["results"]]
        assert str(owner_item.id) in movement_stock_items
        assert str(other_item.id) not in movement_stock_items
