# Phase 2: POS Core - Research

**Researched:** 2026-02-03
**Domain:** Restaurant POS System with Offline-First PWA
**Confidence:** HIGH

## Summary

This phase implements the core Point-of-Sale functionality for a multi-tenant restaurant system. The research covers menu management (categories, items, modifiers), order workflow (cart, submission, kitchen display), offline-first architecture, and customer self-ordering via QR codes.

The standard approach combines Django REST Framework for APIs with WebSocket support via Django Channels for real-time kitchen display updates. The PWA frontend uses Dexie.js for IndexedDB-based offline storage with operation-based sync. PDF receipts use WeasyPrint (HTML/CSS to PDF), and QR codes use Segno.

The key architectural decision is **offline-first with server authority**: all mutations write to IndexedDB first, sync when online, and the server resolves conflicts using timestamps with server authority as the final arbiter (matching the pre-build decision).

**Primary recommendation:** Build the API layer first with comprehensive serializers, then the offline sync layer, then real-time kitchen display - this order minimizes rework and ensures solid foundations.

## Standard Stack

The established libraries/tools for this domain:

### Core Backend
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django REST Framework | 3.15.x | REST API | Already in project, industry standard |
| Django Channels | 4.3.2 | WebSocket/real-time | Official Django async, supports Django 5.2+ |
| channels-redis | 4.x | Channel layer backend | Production-ready pub/sub for Channels |
| WeasyPrint | 68.0 | PDF receipt generation | HTML/CSS to PDF, no external dependencies |
| Segno | 1.6.6 | QR code generation | Pure Python, no dependencies, ISO compliant |
| django-imagekit | 6.0 | Image processing/thumbnails | Production stable, supports Django 5.2 |
| Pillow | 10.x | Image processing (imagekit dep) | Industry standard for Python imaging |

### Core Frontend (Next.js PWA)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Dexie.js | 4.0 | IndexedDB wrapper | Best-in-class offline-first, React hooks |
| dexie-react-hooks | latest | React integration | useLiveQuery for reactive UI |
| @ducanh2912/next-pwa | latest | PWA/Service Worker | Maintained fork, App Router support |
| next-intl | 4.x | i18n French/English | Best Next.js i18n, App Router native |
| react-query/tanstack-query | 5.x | Server state management | Works with offline, mutation queuing |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| drf-writable-nested | latest | Nested serializers | Menu items with modifiers CRUD |
| django-sequences | latest | Gapless sequences | Daily order number generation |
| qrcode-artistic | latest | Styled QR codes | If branded QR codes needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| WeasyPrint | ReportLab | ReportLab has more control but requires more code; WeasyPrint leverages HTML/CSS skills |
| Segno | qrcode | qrcode requires Pillow dependency; Segno is pure Python |
| Dexie.js | localForage | localForage simpler but lacks Dexie's query power and sync features |
| Django Channels | Pusher/Ably | External services add latency and cost; Channels keeps data in-house |

**Installation (Backend):**
```bash
pip install channels channels-redis weasyprint segno django-imagekit pillow drf-writable-nested
```

**Installation (Frontend):**
```bash
npm install dexie dexie-react-hooks @ducanh2912/next-pwa next-intl @tanstack/react-query
```

## Architecture Patterns

### Recommended Backend Structure (Django App)
```
apps/api/apps/
├── menu/                    # Menu management
│   ├── models.py           # Category, MenuItem, Modifier, ModifierOption
│   ├── serializers.py      # Nested serializers for full menu
│   ├── views.py            # ViewSets with permission classes
│   ├── urls.py             # /api/menu/...
│   └── admin.py            # Admin interface for menu management
├── orders/                  # Order processing
│   ├── models.py           # Order, OrderItem, OrderItemModifier
│   ├── serializers.py      # Order creation with items
│   ├── views.py            # Order CRUD, status updates
│   ├── signals.py          # Post-save signals for notifications
│   ├── consumers.py        # WebSocket consumers for KDS
│   ├── services.py         # Business logic (order number gen)
│   └── routing.py          # WebSocket URL routing
├── receipts/               # Receipt generation
│   ├── services.py         # PDF generation logic
│   ├── templates/          # HTML templates for receipts
│   └── views.py            # PDF download endpoint
└── qr/                     # QR code generation
    └── services.py         # QR URL generation
```

### Recommended Frontend Structure (Next.js)
```
apps/web/
├── app/
│   ├── [locale]/           # i18n routing (fr/en)
│   │   ├── pos/            # POS cashier interface
│   │   │   └── page.tsx
│   │   ├── kitchen/        # Kitchen display
│   │   │   └── page.tsx
│   │   └── menu/           # Customer menu view
│   │       └── [restaurantSlug]/
│   │           └── page.tsx
│   └── layout.tsx
├── lib/
│   ├── db/                 # Dexie database setup
│   │   ├── schema.ts       # IndexedDB schema
│   │   └── sync.ts         # Sync logic
│   ├── api/                # API client with offline queue
│   └── i18n/               # Translation files
├── components/
│   ├── pos/                # POS-specific components
│   ├── kitchen/            # KDS components
│   └── menu/               # Customer menu components
└── messages/               # Translation JSON files
    ├── en.json
    └── fr.json
```

### Pattern 1: Offline-First Data Flow
**What:** All mutations write to IndexedDB first, then sync to server
**When to use:** All order creation and modifications
**Example:**
```typescript
// Source: Dexie.js documentation pattern
// lib/db/schema.ts
import Dexie, { Table } from 'dexie';

interface PendingOperation {
  id?: number;
  type: 'CREATE_ORDER' | 'UPDATE_STATUS';
  payload: any;
  createdAt: Date;
  syncStatus: 'pending' | 'syncing' | 'failed';
  retryCount: number;
}

class RestaurantDB extends Dexie {
  orders!: Table<Order>;
  pendingOps!: Table<PendingOperation>;
  menu!: Table<MenuItem>;

  constructor() {
    super('resto360');
    this.version(1).stores({
      orders: '++id, localId, serverId, status, createdAt',
      pendingOps: '++id, type, syncStatus, createdAt',
      menu: 'id, categoryId, name'
    });
  }
}

export const db = new RestaurantDB();
```

### Pattern 2: Daily Order Number Generation
**What:** Gapless sequence that resets daily per restaurant
**When to use:** Order number assignment (e.g., "Order #42 for today")
**Example:**
```python
# Source: jujens.eu daily sequence pattern
# apps/orders/services.py
from datetime import date
from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist

class DailySequence(models.Model):
    restaurant = models.ForeignKey('authentication.Restaurant', on_delete=models.CASCADE)
    day = models.DateField()
    sequence = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['restaurant', 'day']
        indexes = [
            models.Index(fields=['restaurant', 'day'])
        ]

class DailySequenceManager(models.Manager):
    @transaction.atomic
    def get_next_order_number(self, restaurant):
        today = date.today()
        sequence, created = DailySequence.objects.select_for_update().get_or_create(
            restaurant=restaurant,
            day=today,
            defaults={'sequence': 0}
        )
        sequence.sequence += 1
        sequence.save(update_fields=['sequence'])
        return sequence.sequence
```

### Pattern 3: Kitchen Display WebSocket Consumer
**What:** Real-time order updates to kitchen displays
**When to use:** Order queue management for kitchen staff
**Example:**
```python
# Source: Django Channels documentation
# apps/orders/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class KitchenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.room_group_name = f'kitchen_{self.restaurant_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def order_update(self, event):
        """Receive order update from channel layer and send to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order': event['order']
        }))

# Usage: Send updates via Django signals
# apps/orders/signals.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def notify_kitchen(order):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'kitchen_{order.restaurant_id}',
        {
            'type': 'order_update',
            'order': OrderSerializer(order).data
        }
    )
```

### Pattern 4: Menu Item with Modifiers (Nested Serializers)
**What:** Full menu hierarchy in single API response
**When to use:** Menu CRUD and display
**Example:**
```python
# Source: DRF nested serializers documentation
# apps/menu/serializers.py
from rest_framework import serializers
from .models import Category, MenuItem, Modifier, ModifierOption

class ModifierOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModifierOption
        fields = ['id', 'name', 'price_adjustment']

class ModifierSerializer(serializers.ModelSerializer):
    options = ModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Modifier
        fields = ['id', 'name', 'required', 'max_selections', 'options']

class MenuItemSerializer(serializers.ModelSerializer):
    modifiers = ModifierSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'image',
                  'thumbnail_url', 'is_available', 'modifiers']

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None

class CategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'display_order', 'is_visible', 'items']
```

### Anti-Patterns to Avoid
- **Polling for kitchen updates:** Use WebSockets, not repeated API calls
- **Storing images in database:** Use ImageField with proper storage backend
- **Client-side order number generation:** Always generate on server with locking
- **Syncing full state:** Use operation-based sync, not state replacement
- **Blocking on sync:** Never block UI waiting for server sync

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| IndexedDB operations | Raw IndexedDB API | Dexie.js | Dexie handles browser quirks, provides clean API |
| PDF generation | HTML string manipulation | WeasyPrint | CSS Paged Media, proper pagination, fonts |
| QR codes | Canvas drawing | Segno | ISO compliant, multiple output formats |
| Image thumbnails | PIL resize code | django-imagekit | Caching, specs, admin integration |
| WebSocket auth | Custom middleware | Django Channels AuthMiddleware | Session/token integration built-in |
| i18n routing | Manual locale detection | next-intl | Middleware, static generation, type safety |
| Gapless sequences | Counter models | django-sequences or custom with locking | Transaction-safe, no gaps on rollback |
| Nested create/update | Manual create loops | drf-writable-nested | Handles all edge cases correctly |

**Key insight:** POS systems have many subtle edge cases (concurrent orders, offline sync, receipt formatting). Using established libraries prevents weeks of debugging race conditions and edge cases.

## Common Pitfalls

### Pitfall 1: Offline Sync Race Conditions
**What goes wrong:** Multiple offline orders sync simultaneously, causing duplicate order numbers or conflicts
**Why it happens:** Naive sync implementations don't handle concurrent sync attempts
**How to avoid:**
- Use a single sync queue with mutex/lock
- Process operations sequentially, not in parallel
- Server generates order numbers, not client
**Warning signs:** Duplicate orders appearing, order numbers skipping

### Pitfall 2: Kitchen Display Memory Leaks
**What goes wrong:** KDS page becomes slow after hours of use
**Why it happens:** WebSocket event handlers accumulate, orders not cleaned from state
**How to avoid:**
- Clean up old orders (completed > 1 hour)
- Proper useEffect cleanup for WebSocket subscriptions
- Virtual scrolling for long order lists
**Warning signs:** Page refresh "fixes" slowness, increasing memory in DevTools

### Pitfall 3: Image Upload Size Issues
**What goes wrong:** Menu item images take forever to upload or fail on mobile
**Why it happens:** Original photos are 5-10MB, no client-side resize
**How to avoid:**
- Resize on client before upload (max 1200px width)
- Use ImageKit for server-side thumbnails
- Set reasonable MAX_UPLOAD_SIZE
**Warning signs:** Timeout errors on image upload, slow menu loading

### Pitfall 4: Receipt PDF Rendering Inconsistencies
**What goes wrong:** Receipts look different on different systems/printers
**Why it happens:** System font differences, CSS assumptions
**How to avoid:**
- Embed fonts in PDF (WeasyPrint supports this)
- Use explicit sizes (pt, mm), not relative units
- Test on target thermal printers
**Warning signs:** Fonts changing, elements misaligned in production

### Pitfall 5: IndexedDB Storage Quota
**What goes wrong:** Offline storage fails silently on mobile Safari
**Why it happens:** iOS Safari has aggressive storage limits (~500MB, less in private mode)
**How to avoid:**
- Handle storage quota errors gracefully
- Clean old synced operations regularly
- Show user-friendly message when storage full
**Warning signs:** Sync failing on iOS, "QuotaExceededError" in console

### Pitfall 6: i18n Missing Keys Silent Failures
**What goes wrong:** UI shows raw translation keys in production
**Why it happens:** Missing translations not caught during development
**How to avoid:**
- Enable strict mode in next-intl
- Add CI check for translation key completeness
- Default to fallback locale, not key name
**Warning signs:** "pos.cart.total" appearing in UI instead of translated text

## Code Examples

Verified patterns from official sources:

### QR Code Generation for Menu URL
```python
# Source: Segno documentation
# apps/qr/services.py
import segno
from io import BytesIO
from django.conf import settings

def generate_menu_qr(restaurant_slug: str) -> bytes:
    """Generate QR code PNG for restaurant menu URL"""
    menu_url = f"{settings.FRONTEND_URL}/menu/{restaurant_slug}"
    qr = segno.make(menu_url, error='H')  # High error correction

    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=10, border=2)
    buffer.seek(0)
    return buffer.getvalue()
```

### PDF Receipt Generation
```python
# Source: WeasyPrint documentation pattern
# apps/receipts/services.py
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from io import BytesIO

def generate_receipt_pdf(order) -> bytes:
    """Generate PDF receipt from order"""
    html_string = render_to_string('receipts/receipt.html', {
        'order': order,
        'restaurant': order.restaurant,
        'items': order.items.all(),
    })

    html = HTML(string=html_string)
    css = CSS(string='''
        @page { size: 80mm 200mm; margin: 5mm; }
        body { font-family: monospace; font-size: 10pt; }
    ''')

    buffer = BytesIO()
    html.write_pdf(buffer, stylesheets=[css])
    buffer.seek(0)
    return buffer.getvalue()
```

### Dexie.js Offline Order Creation
```typescript
// Source: Dexie.js documentation
// lib/db/operations.ts
import { db } from './schema';

export async function createOfflineOrder(orderData: CreateOrderInput) {
  const localId = crypto.randomUUID();

  // 1. Store order locally
  await db.orders.add({
    localId,
    serverId: null,
    status: 'pending',
    orderType: orderData.orderType,
    items: orderData.items,
    createdAt: new Date(),
    syncedAt: null,
  });

  // 2. Queue sync operation
  await db.pendingOps.add({
    type: 'CREATE_ORDER',
    payload: { localId, ...orderData },
    createdAt: new Date(),
    syncStatus: 'pending',
    retryCount: 0,
  });

  // 3. Trigger sync if online
  if (navigator.onLine) {
    syncPendingOperations();
  }

  return localId;
}
```

### Next.js i18n Setup with next-intl
```typescript
// Source: next-intl documentation
// middleware.ts
import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
  locales: ['fr', 'en'],
  defaultLocale: 'fr',
  localePrefix: 'always'
});

export const config = {
  matcher: ['/((?!api|_next|.*\\..*).*)']
};

// app/[locale]/layout.tsx
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';

export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

### Django Channels ASGI Configuration
```python
# Source: Django Channels documentation
# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

django_asgi_app = get_asgi_application()

from apps.orders.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LocalStorage for offline | IndexedDB via Dexie | 2022-2023 | Better storage limits, structured data |
| next-pwa (original) | @ducanh2912/next-pwa or Serwist | 2023-2024 | App Router support, maintained |
| react-i18next | next-intl | 2023-2024 | Better Next.js App Router integration |
| Django Channels 3.x | Django Channels 4.3.2 | 2024-2025 | Django 5.x support, performance |
| ReportLab for receipts | WeasyPrint | 2020+ | HTML/CSS based, easier design |
| Polling for real-time | WebSockets via Channels | Standard | Lower latency, less server load |

**Deprecated/outdated:**
- next-pwa (original): Unmaintained, use @ducanh2912/next-pwa or Serwist
- Django Channels 3.x: Upgrade to 4.x for Django 5.2 support
- django-imagekit 5.x: Upgrade to 6.0 for Django 5.2 support
- localStorage for app data: Migrate to IndexedDB for complex data

## Open Questions

Things that couldn't be fully resolved:

1. **django-imagekit exact Django 5.2.11 compatibility**
   - What we know: v6.0 lists Django 5.2 as supported
   - What's unclear: Whether 5.2.11 LTS specifically tested
   - Recommendation: Should work, test during implementation; have Pillow fallback if issues

2. **Serwist vs @ducanh2912/next-pwa for service workers**
   - What we know: Both are maintained, both support App Router
   - What's unclear: Which has better long-term maintenance
   - Recommendation: Start with @ducanh2912/next-pwa (more examples available), can migrate if needed

3. **Thermal printer receipt formatting**
   - What we know: 80mm width is standard for POS
   - What's unclear: Specific Ivory Coast printer models and their quirks
   - Recommendation: Build generic receipt, test with actual hardware in Phase 3+

4. **Background Sync API browser support**
   - What we know: Chrome/Edge excellent, Safari limited
   - What's unclear: Exact Safari iOS PWA behavior in 2026
   - Recommendation: Use manual sync trigger as fallback, don't rely solely on Background Sync

## Sources

### Primary (HIGH confidence)
- Django Channels PyPI - version 4.3.2, Django 4.2-6.0 support: https://pypi.org/project/channels/
- Dexie.js official docs - v4.0, offline-first patterns: https://dexie.org/docs/Tutorial/Getting-started
- next-intl official site - v4, App Router support: https://next-intl.dev/
- WeasyPrint PyPI - v68.0: https://pypi.org/project/weasyprint/
- Segno documentation - v1.6.6: https://segno.readthedocs.io/
- django-imagekit GitHub - v6.0, Django 5.2 support: https://github.com/matthewwithanm/django-imagekit

### Secondary (MEDIUM confidence)
- Jujens' blog on daily sequence reset: https://www.jujens.eu/posts/en/2021/Apr/08/sequence-reset-every-day/
- LogRocket on Next.js PWA: https://blog.logrocket.com/dexie-js-indexeddb-react-apps-offline-data-storage/
- DRF nested serializers docs: https://www.django-rest-framework.org/topics/writable-nested-serializers/
- GeekyAnts POS architecture guide: https://geekyants.com/blog/how-to-build-a-restaurant-pos-system-for-modern-businesses--a-step-by-step-guide
- Quantic POS features list: https://getquantic.com/restaurant-pos-system-features/

### Tertiary (LOW confidence)
- Various Medium articles on i18n patterns
- Community discussions on offline sync strategies

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via PyPI/npm with version numbers
- Architecture: HIGH - Patterns from official documentation
- Pitfalls: MEDIUM - Based on community experience and best practices articles

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - stable tech stack)

---

## Quick Reference for Planner

### Required pip packages
```
channels==4.3.2
channels-redis>=4.0
weasyprint>=68.0
segno>=1.6.6
django-imagekit>=6.0
pillow>=10.0
drf-writable-nested>=0.7.0
```

### Required npm packages
```
dexie@^4.0
dexie-react-hooks
@ducanh2912/next-pwa
next-intl@^4.0
@tanstack/react-query@^5.0
```

### Model Hierarchy
```
Restaurant (existing)
├── Category
│   └── MenuItem
│       ├── Modifier
│       │   └── ModifierOption
│       └── Image (via ImageKit)
├── Order
│   └── OrderItem
│       └── OrderItemModifier
├── Table (for dine-in)
└── DailySequence (for order numbers)
```

### API Endpoints Needed
- `GET/POST /api/menu/categories/` - Category CRUD
- `GET/POST /api/menu/items/` - MenuItem CRUD
- `GET/POST /api/menu/modifiers/` - Modifier CRUD
- `GET/POST /api/orders/` - Order CRUD
- `PATCH /api/orders/{id}/status/` - Status update
- `GET /api/orders/queue/` - Kitchen queue
- `GET /api/receipts/{order_id}/pdf/` - Receipt download
- `GET /api/qr/{restaurant_slug}/` - QR code image
- `WS /ws/kitchen/{restaurant_id}/` - Kitchen display WebSocket
