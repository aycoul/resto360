# RESTO360 Lite - Design Document

**Date:** 2026-02-04
**Status:** Approved
**Author:** Claude (AI Assistant)
**Stakeholder:** Project Owner

---

## Executive Summary

RESTO360 Lite is a free/low-cost digital menu solution that lets any restaurant get a QR menu in under 5 minutes. It serves as the entry point to the full RESTO360 platform, capturing the market segment currently served by competitors like FindMenu while creating a natural upsell funnel to the complete restaurant operating system.

---

## Problem Statement

### Current Situation
- RESTO360 is a comprehensive restaurant platform (POS, payments, delivery, inventory)
- No public marketing website exists
- No self-service onboarding - requires manual setup
- No "lite" option for restaurants that just want a digital menu
- Missing the large market of small restaurants wanting simple QR menus

### Competitive Landscape
FindMenu (India) offers QR menus at $2.50-3.75/month with:
- Digital QR menu (view only, no ordering)
- Basic/Advanced analytics
- Custom branding (paid tier)
- White label option (annual plan)

**FindMenu's Limitations:**
- No ordering capability
- No payment integration
- No kitchen/POS integration
- No delivery management

### Opportunity
Capture the "menu-only" market segment in West Africa, then upsell to full RESTO360 when restaurants grow and need more capabilities.

---

## Product Definition

### What is RESTO360 Lite?
A free/low-cost digital menu solution that lets any restaurant get a QR menu in under 5 minutes. It's the "gateway" to the full RESTO360 platform.

### Target Users
- Small restaurants wanting to ditch paper menus
- Food trucks and pop-ups
- Cafes and bars
- Restaurants curious about RESTO360 but not ready to commit

### Value Proposition
> "Get your restaurant online in 5 minutes. Free forever for basic menus."

---

## Tier Structure

| Feature | Free | Pro ($10/mo) | Full RESTO360 |
|---------|------|--------------|---------------|
| Digital QR menu | ✓ | ✓ | ✓ |
| Menu items limit | 20 | Unlimited | Unlimited |
| Categories | 3 | Unlimited | Unlimited |
| Basic analytics (views) | ✓ | ✓ | ✓ |
| Advanced analytics | - | ✓ | ✓ |
| Custom branding/colors | - | ✓ | ✓ |
| Custom logo | - | ✓ | ✓ |
| Remove "Powered by" badge | - | ✓ | ✓ |
| Customer ordering | - | - | ✓ |
| POS system | - | - | ✓ |
| Kitchen display | - | - | ✓ |
| Mobile money payments | - | - | ✓ |
| Inventory management | - | - | ✓ |
| Delivery tracking | - | - | ✓ |
| WhatsApp ordering | - | - | ✓ |

### Upsell Triggers
- "Want customers to order directly? Upgrade to RESTO360"
- "Reached 20 item limit? Go Pro for unlimited"
- "Need POS + payments? See RESTO360 full platform"
- After 30 days: "You've had 500 menu views! Ready to take orders?"

---

## User Flows

### Flow 1: Registration (2 minutes)

```
Landing Page → Click "Get Started Free"
     ↓
Registration Form:
  - Restaurant name
  - Owner name
  - Phone (WhatsApp)
  - Email
  - Password
     ↓
Email/SMS verification (optional for MVP)
     ↓
Redirect to Onboarding Wizard
```

### Flow 2: Onboarding Wizard (3 minutes)

```
Step 1: Restaurant Details
  - Name (pre-filled)
  - Address
  - Phone
  - Description (optional)
  - Logo upload (optional)
     ↓
Step 2: Create First Category
  - Quick suggestions: Plats Principaux, Boissons, Desserts
  - Or custom name
     ↓
Step 3: Add Menu Items
  - Name, price, description
  - Photo (optional)
  - "Add another" button
  - Live preview on side
     ↓
Step 4: Get QR Code
  - Generated QR code
  - Download PNG/PDF
  - Print instructions
  - WhatsApp share
  - Link to live menu
     ↓
Dashboard (onboarding complete)
```

### Flow 3: Daily Usage

```
Login → Dashboard Overview
  - See views this week
  - See top items
  - Check menu item count
     ↓
Menu Tab → Edit menu
  - Add/edit/delete items
  - Upload photos
  - Reorder items
  - Toggle visibility
     ↓
QR Code Tab → Download/share
     ↓
Settings → Update restaurant info
```

### Flow 4: Upgrade Path

```
Hit limit (20 items) OR Click "Upgrade"
     ↓
Upgrade Modal:
  - Compare tiers
  - Highlight benefits
  - Pricing
     ↓
Pro: Mobile money payment
Full: Contact sales / Demo request
     ↓
Plan activated → Features unlocked
```

---

## Information Architecture

### URL Structure

```
resto360.com/                    # Landing page
resto360.com/pricing             # Pricing page
resto360.com/about               # About page
resto360.com/register            # Registration
resto360.com/login               # Login
resto360.com/onboarding          # Onboarding wizard
resto360.com/dashboard           # Lite dashboard home
resto360.com/dashboard/menu      # Menu editor
resto360.com/dashboard/qr        # QR code page
resto360.com/dashboard/settings  # Settings
resto360.com/menu/[slug]         # Public menu (existing)
resto360.com/pos                 # Full platform (existing)
resto360.com/kitchen             # Full platform (existing)
```

### Navigation (Lite Users)

```
┌──────────────────────────────────────────────────────────┐
│ RESTO360 Lite        [Restaurant Name ▼]      [Upgrade]  │
├──────────────────────────────────────────────────────────┤
│ 📊 Overview │ 🍔 Menu │ 📱 QR Code │ ⚙️ Settings         │
└──────────────────────────────────────────────────────────┘
```

---

## Page Designs

### Landing Page

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                      │
│ Logo | Features | Pricing | About | [Login] [Get Started]   │
├─────────────────────────────────────────────────────────────┤
│ HERO SECTION                                                │
│                                                             │
│ "Your Restaurant Menu,              ┌─────────────────┐    │
│  Now Digital"                       │  [Phone mockup  │    │
│                                     │   showing menu] │    │
│ Free QR menu in 5 minutes.          │                 │    │
│ No credit card required.            └─────────────────┘    │
│                                                             │
│ [Get Started Free]  [View Demo]                             │
│                                                             │
│ 100+ Restaurants  |  10K+ Scans  |  West Africa #1          │
├─────────────────────────────────────────────────────────────┤
│ WHY DIGITAL MENU?                                           │
│                                                             │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ 🌱       │ │ 📱       │ │ 💰       │ │ 📊       │        │
│ │ Eco-     │ │ Always   │ │ Save on  │ │ Track    │        │
│ │ friendly │ │ Updated  │ │ Printing │ │ Popular  │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────────────────┤
│ HOW IT WORKS                                                │
│                                                             │
│    ①              ②               ③                        │
│ Sign Up  →   Add Menu   →   Print QR Code                   │
│ Free         Items           & Share                        │
├─────────────────────────────────────────────────────────────┤
│ PRICING                                                     │
│ [Free] [Pro $10/mo] [Full Platform]                         │
│ (See detailed table above)                                  │
├─────────────────────────────────────────────────────────────┤
│ TESTIMONIALS                                                │
│ "RESTO360 helped us go paperless!" - Restaurant Owner       │
├─────────────────────────────────────────────────────────────┤
│ CTA BANNER                                                  │
│ Ready to go digital? [Get Started Free]                     │
├─────────────────────────────────────────────────────────────┤
│ FOOTER                                                      │
│ Links | Contact | WhatsApp | Social | © RESTO360            │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Welcome back, Amadou!                                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 📱 156      │  │ 🍔 12/20    │  │ ⭐ Upgrade  │         │
│  │ Menu Views  │  │ Menu Items  │  │ Go Pro for  │         │
│  │ This Week   │  │ Used        │  │ unlimited   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  📈 Views This Week                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Mon  Tue  Wed  Thu  Fri  Sat  Sun               │   │
│  │      ▂    ▄    ▃    ▅    ▇    █    ▆                │   │
│  │     12   24   18   32   48   62   45                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🔥 Top Items                              [See all →]      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Poulet Yassa ...................... 45 views     │   │
│  │ 2. Thieboudienne ..................... 38 views     │   │
│  │ 3. Bissap ............................ 29 views     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 💡 Want customers to order directly from the menu?  │   │
│  │    Upgrade to RESTO360 Full Platform                │   │
│  │                                    [Learn More →]   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Menu Editor

```
┌─────────────────────────────────────────────────────────────┐
│  Menu Items                            12/20 items used     │
│                                        [+ Add Category]     │
├─────────────────────────────────────────────────────────────┤
│  📁 Plats Principaux (3 items)                    [Edit ▼]  │
│  ├─────────────────────────────────────────────────────────┤
│  │ [img] Poulet Yassa          4,500 XOF    [Edit] [Hide]  │
│  │ [img] Thieboudienne         5,000 XOF    [Edit] [Hide]  │
│  │ [img] Mafé                  4,000 XOF    [Edit] [Hide]  │
│  │                              [+ Add Item]                │
│  ├─────────────────────────────────────────────────────────┤
│  📁 Boissons (2 items)                            [Edit ▼]  │
│  ├─────────────────────────────────────────────────────────┤
│  │ [img] Bissap                1,000 XOF    [Edit] [Hide]  │
│  │ [img] Gingembre             1,000 XOF    [Edit] [Hide]  │
│  │                              [+ Add Item]                │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

### Database Changes

```python
# apps/api/apps/restaurants/models.py

class Restaurant(models.Model):
    # Existing fields...

    # Plan management
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('full', 'Full Platform'),
    ]
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    plan_started_at = models.DateTimeField(null=True, blank=True)
    plan_expires_at = models.DateTimeField(null=True, blank=True)

    # Lite-specific settings
    custom_branding_enabled = models.BooleanField(default=False)
    brand_primary_color = models.CharField(max_length=7, default='#10B981')
    brand_secondary_color = models.CharField(max_length=7, default='#059669')
    show_powered_by = models.BooleanField(default=True)

    # Onboarding tracking
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step = models.IntegerField(default=0)

    @property
    def menu_item_limit(self):
        if self.plan_type == 'free':
            return 20
        return None  # Unlimited

    @property
    def category_limit(self):
        if self.plan_type == 'free':
            return 3
        return None  # Unlimited

    @property
    def can_access_pos(self):
        return self.plan_type == 'full'

    @property
    def can_access_ordering(self):
        return self.plan_type == 'full'

    @property
    def can_customize_branding(self):
        return self.plan_type in ('pro', 'full')
```

```python
# apps/api/apps/analytics/models.py (NEW)

class MenuView(models.Model):
    """Track anonymous menu page views for analytics."""
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    menu_item = models.ForeignKey('menu.MenuItem', null=True, blank=True, on_delete=models.SET_NULL)
    viewed_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=64)  # Anonymous session tracking
    user_agent = models.TextField(blank=True)
    ip_country = models.CharField(max_length=2, blank=True)  # Country code
    referrer = models.URLField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['restaurant', 'viewed_at']),
            models.Index(fields=['restaurant', 'menu_item', 'viewed_at']),
        ]


class DailyMenuStats(models.Model):
    """Aggregated daily stats for faster queries."""
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    date = models.DateField()
    total_views = models.IntegerField(default=0)
    unique_sessions = models.IntegerField(default=0)

    class Meta:
        unique_together = ['restaurant', 'date']
        indexes = [
            models.Index(fields=['restaurant', 'date']),
        ]
```

### New API Endpoints

```
# Authentication & Registration
POST /api/v1/auth/register/              # Public self-service registration
POST /api/v1/auth/login/                 # Login (existing, may need updates)
POST /api/v1/auth/forgot-password/       # Password reset

# Onboarding
GET  /api/v1/onboarding/status/          # Get current onboarding step
POST /api/v1/onboarding/restaurant/      # Step 1: Save restaurant details
POST /api/v1/onboarding/category/        # Step 2: Create first category
POST /api/v1/onboarding/items/           # Step 3: Create menu items
POST /api/v1/onboarding/complete/        # Step 4: Mark onboarding complete

# Dashboard & Analytics
GET  /api/v1/dashboard/stats/            # Overview stats (views, items used)
GET  /api/v1/analytics/views/            # View history with date range
GET  /api/v1/analytics/top-items/        # Top viewed items

# Menu Management (simplified for Lite)
GET  /api/v1/menu/lite/                  # Get menu for editing
POST /api/v1/menu/lite/category/         # Create category
PUT  /api/v1/menu/lite/category/:id/     # Update category
DELETE /api/v1/menu/lite/category/:id/   # Delete category
POST /api/v1/menu/lite/item/             # Create item (with limit check)
PUT  /api/v1/menu/lite/item/:id/         # Update item
DELETE /api/v1/menu/lite/item/:id/       # Delete item

# QR Code
GET  /api/v1/qr/generate/                # Generate QR code
GET  /api/v1/qr/download/png/            # Download as PNG
GET  /api/v1/qr/download/pdf/            # Download as PDF with instructions

# Billing & Upgrades
GET  /api/v1/billing/plans/              # List available plans
POST /api/v1/billing/upgrade/            # Initiate upgrade
POST /api/v1/billing/webhook/            # Payment webhook
```

### Frontend File Structure

```
apps/web/app/
├── [locale]/
│   ├── (marketing)/                 # Public marketing pages (no auth)
│   │   ├── layout.tsx               # Marketing layout (header/footer)
│   │   ├── page.tsx                 # Landing page (/)
│   │   ├── pricing/
│   │   │   └── page.tsx             # Pricing page
│   │   ├── about/
│   │   │   └── page.tsx             # About page
│   │   └── demo/
│   │       └── page.tsx             # Demo menu showcase
│   │
│   ├── (auth)/                      # Auth pages (no auth required)
│   │   ├── layout.tsx               # Minimal auth layout
│   │   ├── register/
│   │   │   └── page.tsx             # Registration form
│   │   ├── login/
│   │   │   └── page.tsx             # Login form
│   │   └── forgot-password/
│   │       └── page.tsx             # Password reset
│   │
│   ├── onboarding/                  # Onboarding wizard (auth required)
│   │   ├── layout.tsx               # Wizard layout with progress
│   │   ├── page.tsx                 # Redirect to current step
│   │   ├── restaurant/
│   │   │   └── page.tsx             # Step 1: Restaurant details
│   │   ├── category/
│   │   │   └── page.tsx             # Step 2: First category
│   │   ├── items/
│   │   │   └── page.tsx             # Step 3: Add items
│   │   └── qr/
│   │       └── page.tsx             # Step 4: Get QR code
│   │
│   ├── dashboard/                   # Lite dashboard (auth required)
│   │   ├── layout.tsx               # Dashboard layout with nav
│   │   ├── page.tsx                 # Overview/home
│   │   ├── menu/
│   │   │   └── page.tsx             # Menu editor
│   │   ├── qr/
│   │   │   └── page.tsx             # QR code page
│   │   ├── settings/
│   │   │   └── page.tsx             # Settings
│   │   └── upgrade/
│   │       └── page.tsx             # Upgrade page
│   │
│   ├── menu/[slug]/                 # Public menu (existing)
│   │   └── page.tsx                 # Enhanced with view tracking
│   │
│   ├── pos/                         # Full platform (existing, plan-gated)
│   ├── kitchen/                     # Full platform (existing, plan-gated)
│   └── track/                       # Delivery tracking (existing)
│
├── components/
│   ├── marketing/                   # Marketing page components
│   │   ├── Hero.tsx
│   │   ├── Features.tsx
│   │   ├── HowItWorks.tsx
│   │   ├── PricingTable.tsx
│   │   ├── Testimonials.tsx
│   │   └── Footer.tsx
│   ├── onboarding/                  # Onboarding components
│   │   ├── ProgressBar.tsx
│   │   ├── RestaurantForm.tsx
│   │   ├── CategorySelector.tsx
│   │   ├── ItemEditor.tsx
│   │   └── QRCodeDisplay.tsx
│   ├── dashboard/                   # Dashboard components
│   │   ├── StatsCard.tsx
│   │   ├── ViewsChart.tsx
│   │   ├── TopItemsList.tsx
│   │   ├── MenuEditor.tsx
│   │   ├── CategoryCard.tsx
│   │   ├── ItemRow.tsx
│   │   └── UpgradePrompt.tsx
│   └── ui/                          # Shared UI (existing)
```

### Access Control

```typescript
// middleware.ts - Plan-based route protection

const FULL_PLAN_ROUTES = ['/pos', '/kitchen', '/inventory', '/delivery'];
const PRO_ROUTES = [...FULL_PLAN_ROUTES]; // Same for now
const LITE_ROUTES = ['/dashboard', '/onboarding'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const user = getUser(request); // From session/token

  // Public routes - no auth needed
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  // Auth required
  if (!user) {
    return NextResponse.redirect('/login');
  }

  // Plan-based access
  const planType = user.restaurant.plan_type;

  if (FULL_PLAN_ROUTES.some(r => pathname.startsWith(r))) {
    if (planType !== 'full') {
      return NextResponse.redirect('/dashboard?upgrade=pos');
    }
  }

  return NextResponse.next();
}
```

```python
# apps/api/apps/core/decorators.py

from functools import wraps
from rest_framework.exceptions import PermissionDenied

def requires_plan(*allowed_plans):
    """Decorator to restrict API endpoints by plan type."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            restaurant = request.user.restaurant
            if restaurant.plan_type not in allowed_plans:
                raise PermissionDenied(
                    f"This feature requires {' or '.join(allowed_plans)} plan. "
                    f"Current plan: {restaurant.plan_type}"
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@requires_plan('pro', 'full')
def custom_branding_view(request):
    ...

@requires_plan('full')
def pos_view(request):
    ...
```

---

## Implementation Plan

### Wave 1: Foundation (Days 1-2)

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Add plan fields to Restaurant model | 2h |
| 1.2 | Create MenuView and DailyMenuStats models | 2h |
| 1.3 | Run migrations | 0.5h |
| 1.4 | Create public registration endpoint | 3h |
| 1.5 | Add plan-based access decorators | 2h |
| 1.6 | Frontend route guards middleware | 2h |

### Wave 2: Marketing Site (Days 3-4)

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Landing page with hero, features, how-it-works | 4h |
| 2.2 | Pricing page with tier comparison | 3h |
| 2.3 | Registration page with form | 3h |
| 2.4 | Login page updates | 1h |
| 2.5 | Marketing header/footer components | 2h |
| 2.6 | Mobile responsiveness | 2h |

### Wave 3: Onboarding Wizard (Days 5-6)

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Onboarding layout with progress bar | 2h |
| 3.2 | Step 1: Restaurant details form | 3h |
| 3.3 | Step 2: Category creation | 2h |
| 3.4 | Step 3: Menu item editor with preview | 4h |
| 3.5 | Step 4: QR code generation & download | 3h |
| 3.6 | Onboarding API endpoints | 2h |

### Wave 4: Lite Dashboard (Days 7-8)

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Dashboard layout with navigation | 2h |
| 4.2 | Overview page with stats cards | 3h |
| 4.3 | Views chart component | 2h |
| 4.4 | Top items list | 1h |
| 4.5 | Menu editor page | 4h |
| 4.6 | QR code page | 2h |
| 4.7 | Settings page | 2h |

### Wave 5: Analytics & Polish (Days 9-10)

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | View tracking on public menu | 2h |
| 5.2 | Analytics aggregation service | 3h |
| 5.3 | Dashboard stats API | 2h |
| 5.4 | Upgrade prompts and modals | 2h |
| 5.5 | French translations | 2h |
| 5.6 | End-to-end testing | 3h |
| 5.7 | Deploy to production | 2h |

---

## Success Metrics

### Launch Goals (First 30 Days)
- 50+ restaurant signups
- 25+ restaurants complete onboarding
- 1,000+ menu scans across all restaurants

### Growth Goals (First 90 Days)
- 200+ restaurant signups
- 10% upgrade rate to Pro
- 5% upgrade rate to Full Platform
- 10,000+ monthly menu scans

### Key Performance Indicators
- **Signup rate:** Visitors → Registrations
- **Activation rate:** Registrations → Completed onboarding
- **Engagement:** Weekly active restaurants (edited menu)
- **Conversion:** Free → Pro, Pro → Full
- **Retention:** Monthly active restaurants

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low signup conversion | High | A/B test landing page, simplify registration |
| Users don't complete onboarding | High | Email reminders, simplify to 3 steps |
| Free users never upgrade | Medium | Strategic feature limits, upgrade prompts |
| Support burden from free users | Medium | Self-service docs, WhatsApp chatbot |
| Competitors copy approach | Low | Move fast, build network effects |

---

## Future Enhancements (Post-Launch)

### Phase 2: Growth Features
- Referral program (invite restaurant, get free month)
- Multi-language menus (French, English, Wolof)
- Menu item photos AI enhancement
- Social sharing features

### Phase 3: Monetization
- Payment integration for Pro upgrades
- Annual billing discounts
- Enterprise/chain restaurant pricing
- White-label reseller program

### Phase 4: Platform Features
- Lite → Full migration wizard
- Data import from competitors
- Menu templates library
- Customer feedback collection

---

## Appendix: Competitive Analysis

### FindMenu (India)
- **Pricing:** $2.50-3.75/month
- **Strengths:** Very cheap, simple
- **Weaknesses:** No ordering, no payments, India-only

### FineDine (Global)
- **Pricing:** $29-99/month
- **Strengths:** Beautiful design, ordering
- **Weaknesses:** Expensive for West Africa

### RESTO360 Lite Positioning
- **Pricing:** Free + $10/month Pro
- **Strengths:** Full platform upgrade path, West Africa focus, mobile money
- **Differentiator:** Only solution that scales from free menu to full restaurant OS

---

*Document created: 2026-02-04*
*Last updated: 2026-02-04*
