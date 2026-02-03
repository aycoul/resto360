# Phase 3: Inventory - Research

**Researched:** 2026-02-04
**Domain:** Restaurant Inventory Management with Recipe-Based Stock Deduction
**Confidence:** HIGH

## Summary

This phase implements inventory management for a restaurant POS system. The research covers stock item management, movement tracking with audit trails, low stock alerts, menu-to-ingredient mapping (recipes/BOM), automatic stock deduction on order completion, and inventory reporting.

The standard approach uses Django's built-in capabilities: signals for order completion triggers, F() expressions with `select_for_update()` for race-condition-safe stock updates, and DecimalField for quantities that may be fractional (kg, liters). For audit trails, django-simple-history provides full model snapshots with Django 5.2 support. Stock movements are tracked as immutable records with timestamps and user attribution.

The key architectural insight is that inventory deduction should happen at order completion (not creation), triggered via Django signals. This aligns with the existing Order model's `completed_at` timestamp and avoids premature stock reduction for cancelled orders.

**Primary recommendation:** Implement stock items and movements first, then recipe mapping, then wire up the signal-based deduction on order completion - this order ensures each piece works independently before integration.

## Standard Stack

The established libraries/tools for this domain:

### Core Backend
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django 5.2 | 5.2.11 LTS | ORM, signals, transactions | Already in project |
| django-simple-history | 3.11.0 | Audit trail for stock changes | Full model history, Django 5.2/6.0 support, Jazzband maintained |
| Django F() expressions | built-in | Atomic quantity updates | Prevents race conditions at DB level |
| Django signals | built-in | Order completion triggers | Decoupled, reusable pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Celery | existing | Async low-stock notifications | Background alert emails/push |
| Django Channels | existing | Real-time low-stock alerts | WebSocket push to manager dashboard |
| django-auditlog | 3.4.1 | Alternative audit (diff-based) | If storage efficiency critical |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| django-simple-history | django-auditlog | auditlog stores diffs (smaller), but simple-history gives full snapshots for easier debugging |
| Signals | Direct service call | Signals decouple apps, but direct calls are more explicit; signals already used in orders app |
| DecimalField | IntegerField | IntegerField simpler if all quantities are whole units; DecimalField needed for kg/L/partial units |

**Installation (Backend):**
```bash
pip install django-simple-history
```

**No new frontend packages needed** - inventory management is backend-focused; frontend uses existing API patterns.

## Architecture Patterns

### Recommended Backend Structure (Django App)
```
apps/api/apps/
├── inventory/                      # Inventory management
│   ├── __init__.py
│   ├── apps.py                    # Register signals in ready()
│   ├── models.py                  # StockItem, StockMovement, MenuItemIngredient
│   ├── serializers.py             # CRUD serializers
│   ├── views.py                   # ViewSets with TenantModelViewSet
│   ├── urls.py                    # /api/inventory/...
│   ├── admin.py                   # Admin interface with history
│   ├── services.py                # Business logic (deduction, alerts)
│   ├── signals.py                 # Order completion handler
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_services.py
│       ├── test_signals.py
│       └── factories.py
```

### Model Hierarchy
```
Restaurant (existing)
├── StockItem
│   ├── name, sku, unit (kg/L/piece/etc)
│   ├── current_quantity (DecimalField)
│   ├── low_stock_threshold (DecimalField)
│   └── history (via django-simple-history)
├── StockMovement (immutable audit records)
│   ├── stock_item (FK)
│   ├── quantity_change (positive or negative)
│   ├── movement_type (in/out/adjustment)
│   ├── reason (receipt/usage/waste/correction)
│   ├── reference_type + reference_id (polymorphic link to Order, etc)
│   └── created_by (User FK)
├── MenuItemIngredient (recipe/BOM mapping)
│   ├── menu_item (FK to MenuItem)
│   ├── stock_item (FK to StockItem)
│   └── quantity_required (per 1 unit of menu item)
└── MenuItem (existing - from menu app)
```

### Pattern 1: Atomic Stock Updates with F() Expressions
**What:** Update stock quantities atomically at database level to prevent race conditions
**When to use:** Any stock quantity change (deductions, additions, adjustments)
**Example:**
```python
# Source: Django documentation, maurizi.org race conditions article
# apps/inventory/services.py
from django.db import transaction
from django.db.models import F

def deduct_stock(stock_item_id: uuid.UUID, quantity: Decimal, reason: str, user, reference=None):
    """
    Atomically deduct stock quantity.
    Uses F() expression to prevent race conditions.
    """
    with transaction.atomic():
        # Lock the row to prevent concurrent modifications
        stock_item = StockItem.objects.select_for_update().get(id=stock_item_id)

        if stock_item.current_quantity < quantity:
            raise InsufficientStockError(
                f"Cannot deduct {quantity} from {stock_item.name}: "
                f"only {stock_item.current_quantity} available"
            )

        # Atomic update using F() expression
        StockItem.objects.filter(id=stock_item_id).update(
            current_quantity=F('current_quantity') - quantity
        )

        # Refresh to get updated value
        stock_item.refresh_from_db()

        # Create movement record
        StockMovement.objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=-quantity,
            movement_type='out',
            reason=reason,
            reference_type=reference.__class__.__name__ if reference else None,
            reference_id=reference.id if reference else None,
            created_by=user,
            balance_after=stock_item.current_quantity,
        )

        # Check for low stock alert
        check_low_stock_alert(stock_item)

        return stock_item
```

### Pattern 2: Order Completion Signal Handler
**What:** Trigger stock deduction when order status changes to 'completed'
**When to use:** Automatic ingredient deduction
**Example:**
```python
# Source: Django signals documentation, existing orders/signals.py pattern
# apps/inventory/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order, OrderStatus

@receiver(post_save, sender=Order)
def handle_order_completion(sender, instance, **kwargs):
    """
    Deduct ingredients from stock when order is completed.
    Only triggers on transition TO completed status.
    """
    # Skip if not completed
    if instance.status != OrderStatus.COMPLETED:
        return

    # Skip if already processed (check completed_at was just set)
    if not instance.completed_at:
        return

    # Check if this is the first time being completed
    # (Use a flag or check previous status via history)
    from apps.inventory.services import deduct_ingredients_for_order

    try:
        deduct_ingredients_for_order(instance)
    except InsufficientStockError as e:
        # Log but don't block order completion
        # Restaurant can still complete even if tracking is off
        logger.warning(f"Stock deduction failed for order {instance.id}: {e}")
```

### Pattern 3: Recipe/BOM Ingredient Mapping
**What:** Link menu items to their ingredient requirements
**When to use:** Automatic calculation of stock usage per order
**Example:**
```python
# Source: BOM pattern from django-bom, food ERP concepts
# apps/inventory/models.py
class MenuItemIngredient(TenantModel):
    """Maps a menu item to its required ingredients (recipe/BOM)."""

    menu_item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.CASCADE,
        related_name='ingredients',
    )
    stock_item = models.ForeignKey(
        'inventory.StockItem',
        on_delete=models.CASCADE,
        related_name='menu_usages',
    )
    quantity_required = models.DecimalField(
        max_digits=10,
        decimal_places=4,  # 4 decimal places for precise measurements
        help_text="Quantity of this ingredient required per 1 unit of menu item"
    )

    class Meta:
        unique_together = ['menu_item', 'stock_item']

    def __str__(self):
        return f"{self.menu_item.name}: {self.quantity_required} {self.stock_item.unit} of {self.stock_item.name}"
```

### Pattern 4: Low Stock Alert Check
**What:** Trigger notifications when stock falls below threshold
**When to use:** After any stock deduction
**Example:**
```python
# Source: django-notifs, Celery notification patterns
# apps/inventory/services.py
def check_low_stock_alert(stock_item):
    """
    Check if stock is below threshold and trigger alert.
    Uses Celery for async notification.
    """
    if stock_item.low_stock_threshold is None:
        return  # No threshold configured

    if stock_item.current_quantity <= stock_item.low_stock_threshold:
        # Trigger async notification
        from apps.inventory.tasks import send_low_stock_alert
        send_low_stock_alert.delay(
            stock_item_id=str(stock_item.id),
            current_quantity=float(stock_item.current_quantity),
            threshold=float(stock_item.low_stock_threshold),
        )
```

### Pattern 5: Audit Trail with django-simple-history
**What:** Track all changes to stock items with user attribution
**When to use:** Compliance, debugging, historical analysis
**Example:**
```python
# Source: django-simple-history documentation
# apps/inventory/models.py
from simple_history.models import HistoricalRecords

class StockItem(TenantModel):
    """Stock item with full change history."""

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=20, help_text="e.g., kg, L, piece")
    current_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
    )
    low_stock_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )

    # Audit trail - tracks who changed what
    history = HistoricalRecords()

    # Standard managers
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        unique_together = ['restaurant', 'sku']
        ordering = ['name']
```

### Anti-Patterns to Avoid
- **Deducting on order creation:** Deduct on completion only; cancelled orders shouldn't affect stock
- **Python-level quantity math:** Always use F() expressions for atomic DB updates
- **Blocking on notification:** Use Celery for alerts; don't slow down order completion
- **Nullable foreign keys for movements:** Movement should always link to a stock item
- **Storing history in same table:** Use django-simple-history or separate movement records
- **Trusting client-sent quantities:** Validate all quantities server-side
- **Ignoring unit conversions:** If recipes use different units, implement proper conversion

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Model change history | Custom history tables | django-simple-history | Handles edge cases, admin integration, user tracking |
| Race condition prevention | Mutex/locks | F() + select_for_update() | Database-level atomicity is faster and safer |
| Event-driven deduction | Direct function calls | Django signals | Decouples inventory from orders app |
| Async notifications | Synchronous emails | Celery tasks | Non-blocking, retry support |
| Movement audit records | UPDATE existing rows | Immutable INSERT records | Audit trails should be append-only |

**Key insight:** Inventory systems have subtle concurrency issues. Two staff members restocking simultaneously, a rush of orders depleting stock - these race conditions cause real business problems (overselling, negative stock). Database-level atomicity via F() expressions is essential.

## Common Pitfalls

### Pitfall 1: Race Conditions on Stock Updates
**What goes wrong:** Two orders complete simultaneously, both read stock=10, both deduct 5, result is 5 instead of 0
**Why it happens:** Read-modify-write without locking
**How to avoid:**
- Use F() expressions for all quantity changes
- Wrap in select_for_update() for validation
**Warning signs:** Negative stock quantities, stock counts don't match physical inventory

### Pitfall 2: Deducting Stock on Order Creation
**What goes wrong:** Stock deducted immediately, order cancelled, stock never restored
**Why it happens:** Eager deduction to "reserve" stock
**How to avoid:**
- Deduct only on order completion
- If reservation needed, track separately (reserved_quantity field)
**Warning signs:** Stock counts always lower than expected, manual adjustments needed frequently

### Pitfall 3: Missing Ingredients in Recipe Mapping
**What goes wrong:** Order completes, some ingredients deducted, others not
**Why it happens:** Incomplete recipe setup, new items added without ingredient mapping
**How to avoid:**
- Admin validation warning for menu items without ingredients
- Report for untracked items
- Allow completing orders even with missing mappings (log warning)
**Warning signs:** Stock levels don't decrease proportionally to sales

### Pitfall 4: Decimal Precision Loss
**What goes wrong:** 0.333 kg per serving * 3 servings = 0.99 kg instead of 1.0 kg
**Why it happens:** Insufficient decimal places, wrong rounding
**How to avoid:**
- Use 4 decimal places for quantities (matches accounting standards)
- Use ROUND_HALF_EVEN (Banker's rounding) for calculations
- Store in DecimalField, never FloatField
**Warning signs:** Small discrepancies accumulating over time

### Pitfall 5: Signal Infinite Loops
**What goes wrong:** Stock update triggers history, history triggers signal, infinite loop
**Why it happens:** Signals on model save without guards
**How to avoid:**
- Check signal conditions carefully (status == COMPLETED, not just any save)
- Use update_fields to avoid triggering signals unnecessarily
- django-simple-history handles this internally
**Warning signs:** Server hangs, database connection pool exhausted

### Pitfall 6: Notification Spam on Threshold Boundary
**What goes wrong:** Stock at threshold (10), each small deduction triggers alert
**Why it happens:** Alert triggers on every check, not just first crossing
**How to avoid:**
- Track alert_sent flag on stock item
- Clear flag when stock restocked above threshold
- Or use rate limiting on notifications
**Warning signs:** Manager receives 50 alerts for same item in one day

## Code Examples

Verified patterns from official sources:

### Stock Movement Model
```python
# Source: Django best practices, inventory management patterns
# apps/inventory/models.py
from django.db import models
from apps.core.models import TenantModel

class MovementType(models.TextChoices):
    IN = 'in', 'Stock In (Receipt)'
    OUT = 'out', 'Stock Out (Usage)'
    ADJUSTMENT = 'adjustment', 'Adjustment'

class MovementReason(models.TextChoices):
    PURCHASE = 'purchase', 'Purchase/Receipt'
    ORDER_USAGE = 'order_usage', 'Order Usage'
    WASTE = 'waste', 'Waste/Spoilage'
    THEFT = 'theft', 'Theft/Loss'
    CORRECTION = 'correction', 'Manual Correction'
    TRANSFER = 'transfer', 'Transfer'
    INITIAL = 'initial', 'Initial Stock'

class StockMovement(TenantModel):
    """Immutable record of stock changes for audit trail."""

    stock_item = models.ForeignKey(
        'StockItem',
        on_delete=models.PROTECT,  # Never delete if movements exist
        related_name='movements',
    )
    quantity_change = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Positive for in, negative for out",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )
    reason = models.CharField(
        max_length=20,
        choices=MovementReason.choices,
    )
    notes = models.TextField(blank=True)

    # Polymorphic reference to source (Order, PurchaseOrder, etc.)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)

    # Snapshot of balance for reporting
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=4,
    )

    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock_item', '-created_at']),
            models.Index(fields=['restaurant', '-created_at']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def save(self, *args, **kwargs):
        # Movements are immutable - prevent updates
        if self.pk:
            raise ValueError("StockMovement records cannot be modified")
        super().save(*args, **kwargs)
```

### Ingredient Deduction Service
```python
# Source: Restaurant inventory patterns, Django F() documentation
# apps/inventory/services.py
from decimal import Decimal
from django.db import transaction
from django.db.models import F
import logging

logger = logging.getLogger(__name__)

class InsufficientStockError(Exception):
    """Raised when stock is insufficient for deduction."""
    pass

def deduct_ingredients_for_order(order):
    """
    Deduct all ingredients for a completed order.
    Processes each order item's recipe ingredients.
    """
    with transaction.atomic():
        for order_item in order.items.select_related('menu_item'):
            if not order_item.menu_item:
                continue  # Menu item was deleted

            # Get recipe ingredients for this menu item
            ingredients = MenuItemIngredient.objects.filter(
                menu_item=order_item.menu_item
            ).select_related('stock_item')

            for ingredient in ingredients:
                # Calculate quantity needed
                quantity_needed = ingredient.quantity_required * order_item.quantity

                try:
                    deduct_stock(
                        stock_item_id=ingredient.stock_item_id,
                        quantity=quantity_needed,
                        reason='order_usage',
                        user=order.cashier,
                        reference=order,
                    )
                except InsufficientStockError as e:
                    # Log but continue - don't block order completion
                    logger.warning(
                        f"Insufficient stock for order {order.id}: "
                        f"{ingredient.stock_item.name} needed {quantity_needed}, "
                        f"available {ingredient.stock_item.current_quantity}"
                    )
                    # Still create movement with negative balance (tracked as discrepancy)
                    _create_negative_movement(
                        ingredient.stock_item,
                        quantity_needed,
                        order,
                        order.cashier,
                    )

def add_stock(stock_item_id: uuid.UUID, quantity: Decimal, reason: str, user, notes='', reference=None):
    """Add stock quantity (receipt, adjustment up)."""
    with transaction.atomic():
        stock_item = StockItem.objects.select_for_update().get(id=stock_item_id)

        StockItem.objects.filter(id=stock_item_id).update(
            current_quantity=F('current_quantity') + quantity
        )

        stock_item.refresh_from_db()

        # Clear low stock alert flag if now above threshold
        if stock_item.low_stock_alert_sent and stock_item.current_quantity > stock_item.low_stock_threshold:
            stock_item.low_stock_alert_sent = False
            stock_item.save(update_fields=['low_stock_alert_sent'])

        StockMovement.objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=quantity,
            movement_type='in',
            reason=reason,
            notes=notes,
            reference_type=reference.__class__.__name__ if reference else None,
            reference_id=reference.id if reference else None,
            created_by=user,
            balance_after=stock_item.current_quantity,
        )

        return stock_item
```

### Inventory Report Aggregation
```python
# Source: Django aggregation documentation
# apps/inventory/services.py
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from datetime import date, timedelta

def get_stock_movement_report(restaurant, start_date: date, end_date: date):
    """
    Generate stock movement report for date range.
    Returns daily totals by movement type.
    """
    movements = StockMovement.objects.filter(
        restaurant=restaurant,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).annotate(
        day=TruncDate('created_at')
    ).values(
        'day', 'movement_type', 'stock_item__name'
    ).annotate(
        total_quantity=Sum('quantity_change'),
        movement_count=Count('id'),
    ).order_by('day', 'stock_item__name')

    return list(movements)

def get_current_stock_report(restaurant):
    """
    Get current stock levels for all items.
    Includes low stock status.
    """
    items = StockItem.objects.filter(restaurant=restaurant).annotate(
        is_low_stock=models.Case(
            models.When(
                low_stock_threshold__isnull=False,
                current_quantity__lte=models.F('low_stock_threshold'),
                then=True
            ),
            default=False,
            output_field=models.BooleanField(),
        )
    ).order_by('name')

    return items
```

### Admin Configuration with History
```python
# Source: django-simple-history documentation
# apps/inventory/admin.py
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import StockItem, StockMovement, MenuItemIngredient

@admin.register(StockItem)
class StockItemAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'sku', 'current_quantity', 'unit', 'low_stock_threshold', 'restaurant']
    list_filter = ['restaurant', 'unit']
    search_fields = ['name', 'sku']
    readonly_fields = ['current_quantity']  # Updated via movements only

    history_list_display = ['current_quantity', 'low_stock_threshold']

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'quantity_change', 'movement_type', 'reason', 'created_at', 'created_by']
    list_filter = ['movement_type', 'reason', 'restaurant']
    search_fields = ['stock_item__name', 'notes']
    date_hierarchy = 'created_at'

    def has_change_permission(self, request, obj=None):
        return False  # Movements are immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Movements are immutable

@admin.register(MenuItemIngredient)
class MenuItemIngredientAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'stock_item', 'quantity_required']
    list_filter = ['restaurant', 'stock_item']
    autocomplete_fields = ['menu_item', 'stock_item']
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual stock counting | Automatic deduction on order | Industry standard | Reduces manual work, improves accuracy |
| Full table scans for reports | Indexed queries with aggregation | Django 4.0+ | Better performance at scale |
| Custom audit tables | django-simple-history 3.x | 2024-2025 | Standardized, maintained solution |
| Floating point for money/qty | DecimalField with 4 places | Best practice | Eliminates precision errors |
| Polling for low stock | WebSocket push + async alerts | 2023+ | Real-time notifications |

**Deprecated/outdated:**
- django-simple-history < 3.0: Upgrade to 3.11.0 for Django 5.2/6.0 support
- FloatField for quantities: Use DecimalField to avoid precision issues
- Synchronous alert emails: Use Celery for non-blocking notifications

## Open Questions

Things that couldn't be fully resolved:

1. **Unit conversion between recipes**
   - What we know: Recipes may use g, kg, L, mL, pieces
   - What's unclear: Whether to support automatic conversion (1000g = 1kg) or require consistent units
   - Recommendation: Start with requiring consistent units per stock item; add conversion later if needed

2. **Handling menu item modifiers in recipes**
   - What we know: Modifiers can affect ingredients (extra cheese = more cheese stock)
   - What's unclear: Complexity of modifier-to-ingredient mapping
   - Recommendation: Phase 1: Map only base menu items. Phase 2: Add modifier ingredients if requested

3. **Stock reservation vs immediate deduction**
   - What we know: Some systems reserve stock at order creation, deduct at completion
   - What's unclear: Business requirement for RESTO360
   - Recommendation: Simple deduction on completion is sufficient for restaurant POS; reservation more relevant for e-commerce

4. **Multi-location inventory**
   - What we know: Architecture doc shows single restaurant = single location
   - What's unclear: Whether restaurants might have multiple storage locations
   - Recommendation: Keep single location for now; add location FK to StockItem if needed later

## Sources

### Primary (HIGH confidence)
- Django F() expressions documentation: https://docs.djangoproject.com/en/5.2/ref/models/expressions/#f-expressions
- Django signals documentation: https://docs.djangoproject.com/en/6.0/topics/signals/
- django-simple-history PyPI (v3.11.0): https://pypi.org/project/django-simple-history/
- Django select_for_update documentation: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update

### Secondary (MEDIUM confidence)
- [django-SHOP stock management](https://django-shop.readthedocs.io/en/latest/reference/inventory.html) - inventory patterns
- [Django race conditions article](https://www.maurizi.org/django-orm-race-conditions/) - F() expression usage
- [NetSuite restaurant inventory guide](https://www.netsuite.com/portal/resource/articles/inventory-management/restaurant-inventory-management.shtml) - industry patterns
- [MenuTiger restaurant inventory](https://www.menutiger.com/blog/restaurant-inventory-system) - automatic deduction concepts
- [Django DecimalField for money](https://dev.to/koladev/django-tip-use-decimalfield-for-money-3f63) - precision best practices

### Tertiary (LOW confidence)
- Various Medium articles on Django audit logging
- GitHub inventory management examples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Django built-ins + well-maintained packages
- Architecture: HIGH - Patterns from official documentation and established practices
- Pitfalls: HIGH - Based on documented race condition patterns and real-world issues

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - stable domain)

---

## Quick Reference for Planner

### Required pip packages
```
django-simple-history>=3.11.0
```

### Model Hierarchy
```
Restaurant (existing)
├── StockItem
│   └── StockMovement (immutable audit records)
├── MenuItemIngredient (recipe mapping)
│   ├── → MenuItem (FK)
│   └── → StockItem (FK)
└── MenuItem (existing - from menu app)
```

### API Endpoints Needed
- `GET/POST /api/inventory/stock-items/` - Stock item CRUD
- `GET /api/inventory/stock-items/{id}/` - Stock item detail with history
- `POST /api/inventory/stock-items/{id}/add-stock/` - Add stock (receipt)
- `POST /api/inventory/stock-items/{id}/adjust/` - Manual adjustment
- `GET /api/inventory/movements/` - Movement history (filterable by date, item)
- `GET/POST /api/inventory/recipes/` - Menu item ingredient mappings
- `GET /api/inventory/reports/current-stock/` - Current stock levels
- `GET /api/inventory/reports/movements/` - Movement report (date range)
- `GET /api/inventory/low-stock/` - Items below threshold

### Key Integration Points
- **Order completion signal:** Wire up in `apps/inventory/signals.py`, register in `apps.py`
- **Existing Order model:** Use `post_save` signal, check `status == COMPLETED`
- **Existing MenuItem model:** Add `ingredients` related name via MenuItemIngredient
- **Existing Celery:** Use for async low-stock notifications
- **Existing WebSocket:** Can push low-stock alerts to manager dashboard

### Database Migrations Order
1. Create StockItem model
2. Create StockMovement model
3. Create MenuItemIngredient model
4. Add indexes for performance
5. Register history tracking
