# RESTO360 Lite - Integration with Existing Roadmap

**Date:** 2026-02-04
**Status:** Proposal
**Related:** `2026-02-04-resto360-lite-design.md`

---

## Executive Summary

This document shows how RESTO360 Lite integrates with the existing 9-phase roadmap, leverages what's already built, and proposes improvements to maximize value from existing and future work.

**Key Insight:** The QR menu we enhanced today (FindMenu-style) IS the core of RESTO360 Lite. We're closer to launch than expected.

---

## Current State Analysis

### What's Built (Phases 1-5)

| Phase | Components | Lite Can Reuse? |
|-------|------------|-----------------|
| **1. Foundation** | Auth, multi-tenant, roles | ✅ Yes - needs public registration |
| **2. POS Core** | Menu, orders, QR menu, kitchen | ✅ Menu + QR menu |
| **3. Inventory** | Stock tracking, recipes, alerts | ❌ Full tier only |
| **4. Payments** | Wave, Orange, MTN, cash | ❌ Full tier only |
| **5. Delivery** | Zones, drivers, tracking | ❌ Full tier only |

### What's Planned (Phases 6-9)

| Phase | Components | Lite Opportunity |
|-------|------------|------------------|
| **6. WhatsApp** | Chat ordering, AI parsing | 🔶 Menu sharing via WhatsApp |
| **7. Suppliers** | Catalogs, purchase orders | ❌ Full tier only |
| **8. Finance** | Loans, credit scoring | ❌ Full tier only |
| **9. Analytics** | Sales reports, trends | ✅ Menu analytics for Lite |

---

## Integration Strategy

### Option A: Insert as Phase 5.5 (Recommended)

Insert RESTO360 Lite between Phase 5 (Delivery) and Phase 6 (WhatsApp).

**Rationale:**
- Phase 5 complete - natural pause point
- Lite uses existing menu infrastructure from Phase 2
- Lite's menu analytics becomes foundation for Phase 9
- Lite's landing page supports WhatsApp in Phase 6 (menu link sharing)

**Updated Roadmap:**

```
- [x] Phase 1: Foundation ✓
- [x] Phase 2: POS Core ✓
- [x] Phase 3: Inventory ✓
- [x] Phase 4: Payments ✓
- [x] Phase 5: Delivery ✓
- [ ] Phase 5.5: RESTO360 Lite (NEW) ← INSERT HERE
- [ ] Phase 6: WhatsApp
- [ ] Phase 7: Suppliers
- [ ] Phase 8: Finance
- [ ] Phase 9: Analytics
```

### Option B: Run in Parallel

Build Lite incrementally alongside Phases 6-9.

**Rationale:**
- Doesn't block core platform development
- Can ship landing page now, dashboard later
- Risk: context switching overhead

---

## What RESTO360 Lite Needs (Gap Analysis)

### Already Built ✅

| Component | Location | Notes |
|-----------|----------|-------|
| Menu models | `apps/api/apps/menu/` | Category, MenuItem, Modifier |
| Menu API | `/api/v1/menu/` | Full CRUD endpoints |
| QR menu page | `/menu/[slug]` | Enhanced today (FindMenu style) |
| Auth system | `apps/api/apps/users/` | JWT, roles, permissions |
| Multi-tenant | `apps/api/apps/restaurants/` | Restaurant model, tenant context |
| i18n | `apps/web/i18n/` | French/English |
| PWA | `apps/web/` | Offline-capable, installable |

### Needs Building 🔨

| Component | Effort | Dependencies |
|-----------|--------|--------------|
| Public registration endpoint | 4h | Phase 1 auth |
| Plan type field on Restaurant | 2h | None |
| Landing page | 6h | None |
| Pricing page | 3h | None |
| Registration page | 4h | Public registration API |
| Onboarding wizard | 8h | Registration |
| Lite dashboard | 8h | Plan-based access |
| Menu view tracking | 4h | Analytics models |
| QR code generator/download | 3h | Existing QR lib (Segno) |

**Total New Work:** ~42 hours (~1 week)

### Can Reuse with Modifications 🔄

| Component | Current State | Needed Changes |
|-----------|---------------|----------------|
| Restaurant model | Has name, address, slug | Add plan_type, branding fields |
| Menu editor | POS-integrated | Standalone version for Lite dashboard |
| QR generation | Order receipts only | Restaurant menu QR codes |
| User registration | Admin/invite only | Public self-service |

---

## Improvements to Existing Phases

### Phase 1: Foundation - Improvements

**Current:** Admin creates restaurants, invites users
**Improvement:** Add public self-service registration

```python
# NEW: apps/api/apps/users/views.py

class PublicRegistrationView(APIView):
    """Allow anyone to register a restaurant (Lite tier)."""
    permission_classes = [AllowAny]

    def post(self, request):
        # Create restaurant + owner user in single transaction
        # Auto-assign 'free' plan
        # Send welcome WhatsApp/email
```

**Current:** Single role per user
**Improvement:** Plan-based feature access (orthogonal to roles)

```python
# ENHANCED: apps/api/apps/restaurants/models.py

class Restaurant(models.Model):
    # Existing fields...

    # NEW: Plan management
    plan_type = models.CharField(choices=[
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('full', 'Full Platform'),
    ], default='free')

    @property
    def can_access_pos(self):
        return self.plan_type == 'full'

    @property
    def can_access_ordering(self):
        return self.plan_type == 'full'
```

---

### Phase 2: POS Core - Improvements

**Current:** QR menu is public, but no view tracking
**Improvement:** Track menu views for analytics

```python
# NEW: Track when customer views menu
# apps/api/apps/menu/views.py

class PublicMenuViewSet(viewsets.ReadOnlyModelViewSet):
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)

        # Track view (async to not slow response)
        track_menu_view.delay(
            restaurant_id=self.get_object().id,
            session_id=request.session.session_key,
        )
        return response
```

**Current:** Menu editor tightly coupled to POS
**Improvement:** Standalone menu editor component

```typescript
// Extract reusable menu editor from POS
// apps/web/components/menu-editor/
├── MenuEditor.tsx        // Main component
├── CategoryList.tsx      // Draggable categories
├── ItemForm.tsx          // Add/edit item modal
├── ImageUploader.tsx     // Photo upload with preview
└── index.ts              // Exports
```

**Current:** QR codes only for order receipts
**Improvement:** Restaurant menu QR generator

```python
# NEW: apps/api/apps/restaurants/services/qr_service.py

def generate_menu_qr(restaurant: Restaurant) -> bytes:
    """Generate QR code pointing to public menu."""
    url = f"https://resto360.com/menu/{restaurant.slug}"
    return segno.make(url).png_data_uri(scale=10)
```

---

### Phase 4: Payments - Improvements

**Current:** Payments only for orders
**Improvement:** Subscription payments for Pro/Full tiers

```python
# NEW: apps/api/apps/billing/models.py

class Subscription(TenantModel):
    """Track restaurant subscription to RESTO360."""
    restaurant = models.OneToOneField(Restaurant, on_delete=CASCADE)
    plan = models.CharField(choices=PLAN_CHOICES)
    status = models.CharField(choices=['active', 'past_due', 'cancelled'])
    current_period_end = models.DateTimeField()

    # Payment via existing mobile money providers
    payment_method = models.CharField()  # wave, orange, mtn
```

**Synergy:** Reuse Wave/Orange/MTN providers for subscription billing!

---

### Phase 5: Delivery - No Changes

Delivery remains Full tier only. No modifications needed.

---

## Synergies with Future Phases

### Phase 6: WhatsApp - Enhanced with Lite

**Original Plan:** Chat ordering with AI parsing
**Enhanced Plan:** Add menu sharing for Lite users

```
Customer: "Menu please"
Bot: "Here's our menu: https://resto360.com/menu/teranga
      Tap to view and order! 📱"
```

**Lite Benefit:** Even free-tier restaurants can share menu via WhatsApp
**Full Benefit:** Full-tier adds ordering within conversation

---

### Phase 7: Suppliers - No Integration

Suppliers feature is Full tier only. No Lite integration needed.

---

### Phase 8: Finance - Future Lite Opportunity

**Future Enhancement (not MVP):**
- Lite Pro users with consistent menu traffic could qualify for micro-loans
- "Your menu was viewed 5,000 times this month - you may qualify for expansion financing"

---

### Phase 9: Analytics - Built for Lite First

**Original Plan:** Sales reports, trends, performance metrics
**Enhanced Plan:** Build in two stages

**Stage 1 (Lite Analytics):**
- Menu view counts
- Popular items (by views)
- Traffic by day/hour
- Basic dashboard

**Stage 2 (Full Analytics):**
- Sales reports (revenue, orders)
- Payment method breakdown
- Delivery performance
- Financial trends

**Synergy:** Lite analytics becomes the foundation for Full analytics. Same models, same UI patterns, expanded data sources.

```python
# Unified analytics models work for both tiers
# apps/api/apps/analytics/models.py

class DailyMetrics(TenantModel):
    """Aggregated daily metrics - supports Lite and Full."""
    date = models.DateField()

    # Lite metrics (menu-only)
    menu_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    top_viewed_items = models.JSONField(default=list)

    # Full metrics (orders + payments)
    order_count = models.IntegerField(default=0)
    revenue = models.IntegerField(default=0)  # XOF
    average_order_value = models.IntegerField(default=0)
    payment_breakdown = models.JSONField(default=dict)
```

---

## Proposed Phase 5.5: RESTO360 Lite

### Goal
Anyone can create a free digital menu in 5 minutes, with upgrade path to full platform.

### Success Criteria
1. Visitor can register and create menu without assistance
2. Restaurant has live QR menu within 5 minutes of starting
3. Owner can see how many times menu was viewed
4. Owner can upgrade to Pro (branding) or Full (POS) tier
5. 50+ signups in first month

### Plans

```
- [ ] 05.5-01-PLAN.md - Plan system and public registration (Wave 1)
- [ ] 05.5-02-PLAN.md - Marketing landing page and pricing (Wave 1)
- [ ] 05.5-03-PLAN.md - Onboarding wizard and QR generator (Wave 2)
- [ ] 05.5-04-PLAN.md - Lite dashboard and menu editor (Wave 2)
- [ ] 05.5-05-PLAN.md - Menu analytics and upgrade flow (Wave 3)
```

### Dependencies
- Phase 1 (auth infrastructure)
- Phase 2 (menu models and QR page)

### What We're NOT Building
- Lite does NOT include: POS, kitchen display, inventory, payments, delivery
- Those remain gated to Full tier

---

## Implementation Priority

### Week 1: Core Infrastructure

| Day | Task | Output |
|-----|------|--------|
| 1 | Add plan_type to Restaurant model | Migration |
| 1 | Public registration API endpoint | `/api/v1/auth/register/` |
| 2 | Landing page (hero, features, CTA) | `/` route |
| 2 | Pricing page | `/pricing` route |
| 3 | Registration page | `/register` route |
| 3 | Plan-based route guards | Middleware |

### Week 2: User Experience

| Day | Task | Output |
|-----|------|--------|
| 4 | Onboarding step 1-2 (restaurant + category) | Wizard pages |
| 4 | Onboarding step 3-4 (items + QR) | Wizard pages |
| 5 | Lite dashboard layout | `/dashboard` |
| 5 | Dashboard overview with stats | Stats cards |
| 6 | Standalone menu editor | `/dashboard/menu` |
| 6 | QR code page with downloads | `/dashboard/qr` |
| 7 | Menu view tracking | Analytics API |
| 7 | Upgrade prompts and flow | Modals |

---

## Summary: What Changes

### New Files to Create

```
apps/api/apps/billing/           # NEW: Subscription management
apps/api/apps/analytics/         # NEW: View tracking
apps/web/app/[locale]/(marketing)/  # NEW: Landing pages
apps/web/app/[locale]/onboarding/   # NEW: Wizard
apps/web/app/[locale]/dashboard/    # NEW: Lite dashboard
```

### Existing Files to Modify

```
apps/api/apps/restaurants/models.py  # Add plan fields
apps/api/apps/users/views.py         # Add public registration
apps/web/middleware.ts               # Add plan-based guards
apps/web/app/[locale]/menu/[slug]/   # Add view tracking
```

### Roadmap Changes

```diff
  - [x] Phase 5: Delivery ✓
+ - [ ] Phase 5.5: RESTO360 Lite (NEW)
  - [ ] Phase 6: WhatsApp
```

---

## Decision Needed

**Should we proceed with Phase 5.5 (RESTO360 Lite) before Phase 6 (WhatsApp)?**

**Arguments FOR:**
- Natural pause point after Phase 5
- Generates revenue/users immediately
- Menu analytics foundation benefits Phase 9
- Landing page needed eventually anyway

**Arguments AGAINST:**
- Delays WhatsApp feature
- Context switch from platform features

**Recommendation:** YES - Phase 5.5 provides immediate value (user acquisition) and builds foundation for Phase 9 analytics.

---

*Document created: 2026-02-04*
