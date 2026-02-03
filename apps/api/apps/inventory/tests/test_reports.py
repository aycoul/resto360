"""Tests for inventory reports."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from apps.inventory.models import MovementReason, MovementType, StockMovement

pytestmark = pytest.mark.django_db


class TestCurrentStockReport:
    """Test current stock report endpoint."""

    def test_returns_all_active_stock_items(self, owner_client, sample_inventory):
        """Report includes all active stock items."""
        url = reverse("report-current-stock")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # sample_inventory has 4 active items
        assert response.data["count"] == 4

    def test_annotates_low_stock_status(self, owner_client, owner):
        """Items below threshold have is_low_stock=True."""
        from apps.inventory.tests.factories import StockItemFactory

        # Create item below threshold
        low_item = StockItemFactory(
            restaurant=owner.restaurant,
            name="Low Stock Item",
            current_quantity=Decimal("5.0000"),
            low_stock_threshold=Decimal("10.0000"),
        )

        # Create item above threshold
        normal_item = StockItemFactory(
            restaurant=owner.restaurant,
            name="Normal Stock Item",
            current_quantity=Decimal("50.0000"),
            low_stock_threshold=Decimal("10.0000"),
        )

        url = reverse("report-current-stock")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Find items in response
        items_by_id = {str(i["id"]): i for i in response.data["items"]}

        assert items_by_id[str(low_item.id)]["is_low_stock"] is True
        assert items_by_id[str(normal_item.id)]["is_low_stock"] is False

    def test_excludes_inactive_by_default(self, owner_client, sample_inventory):
        """Inactive items excluded by default."""
        url = reverse("report-current-stock")
        response = owner_client.get(url)

        # sample_inventory has 4 active items, 1 inactive
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 4

        # Check inactive item is not in results
        inactive_item = sample_inventory["items"]["inactive_item"]
        item_ids = [i["id"] for i in response.data["items"]]
        assert str(inactive_item.id) not in item_ids

    def test_include_inactive_param(self, owner_client, sample_inventory):
        """include_inactive=true includes inactive items."""
        url = reverse("report-current-stock")
        response = owner_client.get(url, {"include_inactive": "true"})

        assert response.status_code == status.HTTP_200_OK
        # Should include all 5 items
        assert response.data["count"] == 5

        # Check inactive item IS in results
        inactive_item = sample_inventory["items"]["inactive_item"]
        item_ids = [i["id"] for i in response.data["items"]]
        assert str(inactive_item.id) in item_ids

    def test_unauthenticated_forbidden(self, api_client):
        """Unauthenticated users cannot access report."""
        url = reverse("report-current-stock")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cashier_forbidden(self, cashier_client):
        """Cashiers cannot access stock reports."""
        url = reverse("report-current-stock")
        response = cashier_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLowStockReport:
    """Test low stock report endpoint."""

    def test_returns_only_low_stock_items(self, owner_client, owner):
        """Report only includes items at or below threshold."""
        from apps.inventory.tests.factories import StockItemFactory

        # Create item below threshold
        low_item = StockItemFactory(
            restaurant=owner.restaurant,
            name="Low Stock Item",
            current_quantity=Decimal("5.0000"),
            low_stock_threshold=Decimal("10.0000"),
        )

        # Create item at threshold (should be included)
        at_threshold_item = StockItemFactory(
            restaurant=owner.restaurant,
            name="At Threshold Item",
            current_quantity=Decimal("10.0000"),
            low_stock_threshold=Decimal("10.0000"),
        )

        # Create item above threshold (should not be included)
        normal_item = StockItemFactory(
            restaurant=owner.restaurant,
            name="Normal Stock Item",
            current_quantity=Decimal("50.0000"),
            low_stock_threshold=Decimal("10.0000"),
        )

        # Create item without threshold (should not be included)
        no_threshold_item = StockItemFactory(
            restaurant=owner.restaurant,
            name="No Threshold Item",
            current_quantity=Decimal("1.0000"),
            low_stock_threshold=None,
        )

        url = reverse("report-low-stock")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        item_ids = [i["id"] for i in response.data["items"]]

        # Low and at-threshold items should be included
        assert str(low_item.id) in item_ids
        assert str(at_threshold_item.id) in item_ids

        # Normal and no-threshold items should not be included
        assert str(normal_item.id) not in item_ids
        assert str(no_threshold_item.id) not in item_ids

    def test_unauthenticated_forbidden(self, api_client):
        """Unauthenticated users cannot access report."""
        url = reverse("report-low-stock")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMovementReport:
    """Test movement report endpoint."""

    def test_returns_summary_for_date_range(self, owner_client, sample_stock_item, owner):
        """Report returns summary, daily, and by_item data."""
        # Create some movements
        today = date.today()

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

        url = reverse("report-movements")
        response = owner_client.get(
            url,
            {
                "start_date": (today - timedelta(days=7)).isoformat(),
                "end_date": today.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "period" in response.data
        assert "summary" in response.data
        assert "daily" in response.data
        assert "by_item" in response.data

    def test_validates_date_range(self, owner_client):
        """Start date must be before end date."""
        today = date.today()
        url = reverse("report-movements")
        response = owner_client.get(
            url,
            {
                "start_date": today.isoformat(),
                "end_date": (today - timedelta(days=7)).isoformat(),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_limits_date_range_to_90_days(self, owner_client):
        """Date range cannot exceed 90 days."""
        today = date.today()
        url = reverse("report-movements")
        response = owner_client.get(
            url,
            {
                "start_date": (today - timedelta(days=100)).isoformat(),
                "end_date": today.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filters_by_stock_item(self, owner_client, sample_inventory, owner):
        """Can filter movements to specific stock item."""
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

        today = date.today()
        url = reverse("report-movements")
        response = owner_client.get(
            url,
            {
                "start_date": (today - timedelta(days=7)).isoformat(),
                "end_date": today.isoformat(),
                "stock_item": str(tomatoes.id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        # All by_item entries should be for the specified item
        for item in response.data["by_item"]:
            assert str(item["stock_item__id"]) == str(tomatoes.id)

    def test_requires_start_date(self, owner_client):
        """Start date is required."""
        url = reverse("report-movements")
        response = owner_client.get(url, {"end_date": date.today().isoformat()})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_requires_end_date(self, owner_client):
        """End date is required."""
        url = reverse("report-movements")
        response = owner_client.get(url, {"start_date": date.today().isoformat()})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_forbidden(self, api_client):
        """Unauthenticated users cannot access report."""
        today = date.today()
        url = reverse("report-movements")
        response = api_client.get(
            url,
            {
                "start_date": (today - timedelta(days=7)).isoformat(),
                "end_date": today.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
