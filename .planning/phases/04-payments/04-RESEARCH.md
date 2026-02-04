# Phase 4: Payments - Research

**Researched:** 2026-02-04
**Domain:** Mobile Money Payment Integration (Wave, Orange Money, MTN MoMo) + Cash Management
**Confidence:** MEDIUM (API documentation accessed; some providers have limited public docs)

## Summary

This phase implements payment processing for a restaurant POS in Ivory Coast, integrating three major mobile money providers (Wave Money, Orange Money, MTN MoMo) plus cash payment tracking. The West African mobile money ecosystem is mature but each provider has distinct API patterns requiring a unified abstraction layer.

The standard approach is to build a **Payment Provider Strategy Pattern** that abstracts provider-specific implementations behind a common interface. Each provider handles: payment initiation, webhook verification, status polling (fallback), and refunds. The architecture must handle XOF currency (no decimals, integer amounts only), idempotent payment requests, and network unreliability common in the region.

**Primary recommendation:** Implement a `PaymentProvider` abstract base class with Wave, Orange, and MTN implementations. Use Django FSM for payment state management, Redis for idempotency key storage, and Celery for async webhook processing.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| django-fsm-2 | Latest | Payment state machine | Maintained Django FSM fork, handles pending->processing->success/failed transitions |
| requests | 2.31+ | HTTP client for provider APIs | Standard Python HTTP library |
| httpx | 0.25+ | Async HTTP (alternative) | Better async support if needed |
| hmac/hashlib | stdlib | Webhook signature verification | Built-in, no dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| django-redis | 5.4+ | Idempotency key storage | Already in stack for caching |
| celery | 5.3+ | Async webhook processing | Already in stack for background tasks |
| uuid | stdlib | Idempotency key generation | Generate client-side unique keys |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct API integration | PayDunya aggregator | Easier setup but adds aggregator fees (1-2%), less control |
| django-fsm-2 | django-transitions | django-fsm-2 is more Django-native, better documented |
| Manual status polling | Webhooks only | Webhooks are primary but polling is essential fallback |

**Installation:**
```bash
pip install django-fsm-2 requests httpx
# redis and celery already in requirements
```

## Architecture Patterns

### Recommended Project Structure
```
apps/api/apps/payments/
    __init__.py
    apps.py
    models.py              # Payment, PaymentMethod, CashDrawerSession models
    serializers.py         # DRF serializers
    views.py               # Payment endpoints + webhook handlers
    urls.py                # Route configuration
    admin.py               # Django admin
    services.py            # Payment orchestration logic
    providers/             # Provider implementations
        __init__.py
        base.py            # Abstract PaymentProvider class
        wave.py            # Wave Money implementation
        orange.py          # Orange Money implementation
        mtn.py             # MTN MoMo implementation
    webhooks/              # Webhook handlers
        __init__.py
        handlers.py        # Webhook processing logic
        verification.py    # Signature verification utilities
    tasks.py               # Celery tasks for async processing
    migrations/
    tests/
        __init__.py
        conftest.py
        factories.py
        test_models.py
        test_providers.py
        test_webhooks.py
        test_api.py
        test_reconciliation.py
```

### Pattern 1: Payment Provider Strategy
**What:** Abstract base class with provider-specific implementations
**When to use:** Any payment operation (initiate, check status, refund)
**Example:**
```python
# apps/payments/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class ProviderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class PaymentResult:
    provider_reference: str
    status: ProviderStatus
    redirect_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[dict] = None

@dataclass
class RefundResult:
    success: bool
    provider_reference: Optional[str] = None
    error_message: Optional[str] = None

class PaymentProvider(ABC):
    """Abstract base for all payment providers."""

    @property
    @abstractmethod
    def provider_code(self) -> str:
        """Unique identifier for this provider (e.g., 'wave', 'orange', 'mtn')."""
        pass

    @abstractmethod
    def initiate_payment(
        self,
        amount: int,  # XOF integer amount
        currency: str,
        order_reference: str,
        customer_phone: str,
        idempotency_key: str,
        callback_url: str,
        success_url: str,
        error_url: str,
    ) -> PaymentResult:
        """Initiate a payment request."""
        pass

    @abstractmethod
    def check_status(self, provider_reference: str) -> PaymentResult:
        """Check payment status (polling fallback)."""
        pass

    @abstractmethod
    def process_refund(
        self,
        provider_reference: str,
        amount: Optional[int] = None,  # None = full refund
    ) -> RefundResult:
        """Process a refund (full or partial)."""
        pass

    @abstractmethod
    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """Verify webhook signature."""
        pass

    @abstractmethod
    def parse_webhook(self, body: bytes) -> dict:
        """Parse webhook payload to standard format."""
        pass
```

### Pattern 2: Payment State Machine
**What:** FSM for payment lifecycle management
**When to use:** All payment status transitions
**Example:**
```python
# apps/payments/models.py
from django_fsm import FSMField, transition
from django.db import models
from apps.core.models import TenantModel

class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    EXPIRED = "expired", "Expired"

class Payment(TenantModel):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    payment_method = models.ForeignKey("payments.PaymentMethod", on_delete=models.PROTECT)

    amount = models.PositiveIntegerField(help_text="Amount in XOF (integer)")
    status = FSMField(default=PaymentStatus.PENDING, choices=PaymentStatus.choices)

    # Idempotency
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)

    # Provider details
    provider_code = models.CharField(max_length=20)  # 'wave', 'orange', 'mtn', 'cash'
    provider_reference = models.CharField(max_length=255, blank=True, db_index=True)
    provider_response = models.JSONField(default=dict, blank=True)

    # Refund tracking
    refunded_amount = models.PositiveIntegerField(default=0)

    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # FSM Transitions
    @transition(field=status, source=PaymentStatus.PENDING, target=PaymentStatus.PROCESSING)
    def start_processing(self):
        """Payment sent to provider, awaiting response."""
        pass

    @transition(field=status, source=PaymentStatus.PROCESSING, target=PaymentStatus.SUCCESS)
    def mark_success(self):
        """Payment completed successfully."""
        from django.utils import timezone
        self.completed_at = timezone.now()

    @transition(field=status, source=PaymentStatus.PROCESSING, target=PaymentStatus.FAILED)
    def mark_failed(self, error_code=None, error_message=None):
        """Payment failed."""
        self.provider_response["error_code"] = error_code
        self.provider_response["error_message"] = error_message

    @transition(field=status, source=PaymentStatus.PROCESSING, target=PaymentStatus.EXPIRED)
    def mark_expired(self):
        """Payment expired (timeout)."""
        pass

    @transition(field=status, source=PaymentStatus.SUCCESS, target=PaymentStatus.REFUNDED)
    def mark_refunded(self):
        """Full refund processed."""
        self.refunded_amount = self.amount

    @transition(field=status, source=PaymentStatus.SUCCESS, target=PaymentStatus.PARTIALLY_REFUNDED)
    def mark_partially_refunded(self, amount):
        """Partial refund processed."""
        self.refunded_amount += amount
```

### Pattern 3: Idempotency Key Implementation
**What:** Prevent duplicate payment processing
**When to use:** All payment initiation requests
**Example:**
```python
# apps/payments/services.py
import hashlib
from django.core.cache import cache
from django.db import transaction

IDEMPOTENCY_TTL = 86400  # 24 hours

def get_idempotency_lock_key(key: str) -> str:
    return f"payment:idempotency:{key}"

def check_idempotency(idempotency_key: str):
    """
    Check if this idempotency key has been used.
    Returns existing payment if found, None otherwise.
    """
    lock_key = get_idempotency_lock_key(idempotency_key)

    # Check cache first (fast path)
    cached = cache.get(lock_key)
    if cached:
        return Payment.objects.filter(id=cached).first()

    # Check database (slow path)
    existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        cache.set(lock_key, str(existing.id), IDEMPOTENCY_TTL)
        return existing

    return None

def acquire_idempotency_lock(idempotency_key: str, payment_id: str) -> bool:
    """
    Atomically acquire lock for this idempotency key.
    Returns True if lock acquired, False if already exists.
    """
    lock_key = get_idempotency_lock_key(idempotency_key)
    return cache.add(lock_key, payment_id, IDEMPOTENCY_TTL)
```

### Pattern 4: Webhook Handler with Async Processing
**What:** Receive webhook, verify, queue for processing
**When to use:** All webhook endpoints
**Example:**
```python
# apps/payments/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .tasks import process_webhook_event
from .providers import get_provider

@method_decorator(csrf_exempt, name='dispatch')
class WaveWebhookView(APIView):
    """Handle Wave webhook events."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Get raw body BEFORE any parsing
        raw_body = request.body

        # Get provider and verify signature
        provider = get_provider('wave')
        if not provider.verify_webhook(dict(request.headers), raw_body):
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Queue for async processing (respond quickly to avoid retries)
        process_webhook_event.delay(
            provider_code='wave',
            headers=dict(request.headers),
            body=raw_body.decode('utf-8')
        )

        return Response({"status": "received"}, status=status.HTTP_200_OK)
```

### Anti-Patterns to Avoid
- **Processing webhooks synchronously:** Always queue for async processing to respond within timeout
- **Trusting webhook without signature verification:** Every provider has verification; always use it
- **Storing sensitive keys in code:** Use environment variables for all API keys and secrets
- **Ignoring status polling:** Webhooks can fail; implement polling as fallback
- **Decimal amounts for XOF:** XOF has no decimals; always use integers
- **Single idempotency check:** Check both cache AND database for idempotency

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| State transitions | Custom if/else status logic | django-fsm-2 | Enforces valid transitions, audit trail, visualization |
| Webhook signature | Custom crypto | Provider-specific HMAC | Each provider has specific algorithm and format |
| Idempotency | Database-only check | Redis + DB (cache-aside) | Redis for speed, DB for durability |
| Background processing | Threads/subprocess | Celery (already in stack) | Reliable, retries, monitoring |
| Retry logic | Manual sleep/retry | tenacity or Celery retries | Exponential backoff, jitter, max attempts |

**Key insight:** Payment processing is high-stakes; use battle-tested patterns. Custom solutions miss edge cases that lead to double-charges or lost payments.

## Common Pitfalls

### Pitfall 1: Webhook Signature Verification with Parsed JSON
**What goes wrong:** Signature fails because JSON was parsed and re-serialized
**Why it happens:** Frameworks parse request body; re-serialization changes whitespace/order
**How to avoid:** Access `request.body` (raw bytes) BEFORE any parsing
**Warning signs:** Signature always fails in production, works with test payloads

### Pitfall 2: Wave Checkout URL in WebView
**What goes wrong:** Payment fails or user experience is broken
**Why it happens:** Wave explicitly prohibits WebViews; must open in system browser
**How to avoid:** Use `window.location.href` redirect, never embed in iframe/webview
**Warning signs:** Wave documentation explicitly states this limitation

### Pitfall 3: MTN MoMo Callbacks in Sandbox
**What goes wrong:** Expecting callbacks that never arrive
**Why it happens:** MTN sandbox doesn't support callbacks; must use status polling
**How to avoid:** Always implement polling fallback; test callbacks in production only
**Warning signs:** Sandbox callback URL is "callbacks-do-not-work-in-sandbox.com"

### Pitfall 4: Orange Money Notification Unreliability
**What goes wrong:** Payment completes but webhook never arrives
**Why it happens:** Orange Money notifications can be delayed or missing
**How to avoid:** Poll `checkTransactionStatus` every 2 minutes as fallback
**Warning signs:** Community reports this in SDK documentation

### Pitfall 5: XOF Decimal Handling
**What goes wrong:** API rejects amount or calculates wrong value
**Why it happens:** XOF has 0 decimal places; some systems add .00
**How to avoid:** Store as PositiveIntegerField; never convert to/from float
**Warning signs:** Payment of 1000 XOF shows as 1000.00 or 10.00

### Pitfall 6: Replay Attacks on Webhooks
**What goes wrong:** Attacker replays valid webhook to trigger duplicate action
**Why it happens:** Signature is valid for intercepted request
**How to avoid:** Check timestamp in webhook; reject if >5 minutes old
**Warning signs:** Duplicate webhook processing for same transaction

### Pitfall 7: Race Condition on Idempotency Check
**What goes wrong:** Two concurrent requests both pass idempotency check
**Why it happens:** Check-then-insert without atomic lock
**How to avoid:** Use Redis `SETNX` (cache.add) for atomic lock acquisition
**Warning signs:** Occasional duplicate payments under load

## Code Examples

Verified patterns from official sources:

### Wave Webhook Signature Verification
```python
# Source: https://docs.wave.com/webhook
import hmac
import hashlib
from typing import List, Tuple

def parse_wave_signature(header: str) -> Tuple[str, List[str]]:
    """Parse Wave-Signature header into timestamp and signatures."""
    parts = header.split(',')
    timestamp = None
    signatures = []

    for part in parts:
        key, _, value = part.strip().partition('=')
        if key == 't':
            timestamp = value
        elif key == 'v1':
            signatures.append(value)

    return timestamp, signatures

def verify_wave_signature(
    wave_signature: str,
    raw_body: bytes,
    webhook_secret: str,
    max_age_seconds: int = 300
) -> bool:
    """
    Verify Wave webhook signature.

    Args:
        wave_signature: Value of Wave-Signature header
        raw_body: Raw request body as bytes
        webhook_secret: Your webhook signing secret
        max_age_seconds: Reject webhooks older than this (default 5 min)

    Returns:
        True if signature is valid and timestamp is recent
    """
    import time

    timestamp, signatures = parse_wave_signature(wave_signature)

    if not timestamp or not signatures:
        return False

    # Check timestamp freshness (replay attack prevention)
    try:
        webhook_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - webhook_time) > max_age_seconds:
            return False
    except ValueError:
        return False

    # Compute expected signature
    payload = timestamp.encode('utf-8') + raw_body
    expected = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return any(hmac.compare_digest(expected, sig) for sig in signatures)
```

### Wave Checkout Initiation
```python
# Source: https://docs.wave.com/checkout
import requests

def create_wave_checkout(
    api_key: str,
    amount: int,  # XOF integer
    order_reference: str,
    success_url: str,
    error_url: str,
    customer_phone: str = None,
) -> dict:
    """Create Wave checkout session."""

    response = requests.post(
        "https://api.wave.com/v1/checkout/sessions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "amount": str(amount),  # Wave expects string
            "currency": "XOF",
            "client_reference": order_reference,
            "success_url": success_url,
            "error_url": error_url,
            **({"restrict_payer_mobile": customer_phone} if customer_phone else {}),
        },
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    return {
        "provider_reference": data["id"],
        "redirect_url": data["wave_launch_url"],
        "expires_at": data.get("when_expires"),
    }
```

### MTN MoMo Request to Pay
```python
# Source: https://momodeveloper.mtn.com/api-documentation
import requests
import uuid
import base64

class MTNMoMoProvider:
    def __init__(
        self,
        subscription_key: str,
        user_id: str,
        api_secret: str,
        environment: str = "sandbox",
        callback_url: str = None,
    ):
        self.subscription_key = subscription_key
        self.user_id = user_id
        self.api_secret = api_secret
        self.environment = environment
        self.callback_url = callback_url

        if environment == "sandbox":
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
        else:
            self.base_url = "https://momoapi.mtn.com"

    def _get_token(self) -> str:
        """Get OAuth2 access token."""
        credentials = base64.b64encode(
            f"{self.user_id}:{self.api_secret}".encode()
        ).decode()

        response = requests.post(
            f"{self.base_url}/collection/token/",
            headers={
                "Authorization": f"Basic {credentials}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def request_to_pay(
        self,
        amount: int,
        customer_phone: str,
        external_id: str,
        message: str = "Payment",
    ) -> dict:
        """Initiate payment request."""
        token = self._get_token()
        reference_id = str(uuid.uuid4())

        # Currency is EUR in sandbox, XOF in production (Ivory Coast)
        currency = "EUR" if self.environment == "sandbox" else "XOF"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }

        if self.callback_url and self.environment != "sandbox":
            headers["X-Callback-Url"] = self.callback_url

        response = requests.post(
            f"{self.base_url}/collection/v1_0/requesttopay",
            headers=headers,
            json={
                "amount": str(amount),
                "currency": currency,
                "externalId": external_id,
                "payer": {
                    "partyIdType": "MSISDN",
                    "partyId": customer_phone.lstrip("+"),
                },
                "payerMessage": message,
                "payeeNote": message,
            },
            timeout=30,
        )

        if response.status_code != 202:
            response.raise_for_status()

        return {
            "provider_reference": reference_id,
            "status": "pending",
        }

    def check_status(self, reference_id: str) -> dict:
        """Check payment status."""
        token = self._get_token()

        response = requests.get(
            f"{self.base_url}/collection/v1_0/requesttopay/{reference_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Target-Environment": self.environment,
                "Ocp-Apim-Subscription-Key": self.subscription_key,
            },
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        status_map = {
            "PENDING": "pending",
            "SUCCESSFUL": "success",
            "FAILED": "failed",
        }

        return {
            "provider_reference": reference_id,
            "status": status_map.get(data.get("status"), "pending"),
            "raw_response": data,
        }
```

### Cash Drawer Session Model
```python
# apps/payments/models.py
class CashDrawerSession(TenantModel):
    """Track cash drawer sessions for reconciliation."""

    cashier = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        related_name="cash_drawer_sessions",
    )

    # Opening
    opened_at = models.DateTimeField(auto_now_add=True)
    opening_balance = models.PositiveIntegerField(
        help_text="Opening cash balance in XOF"
    )

    # Closing
    closed_at = models.DateTimeField(null=True, blank=True)
    closing_balance = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Actual closing cash count in XOF"
    )
    expected_balance = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Calculated expected balance"
    )

    # Variance
    variance = models.IntegerField(
        null=True, blank=True,
        help_text="Difference: actual - expected (can be negative)"
    )
    variance_notes = models.TextField(blank=True)

    # Managers
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-opened_at"]
        indexes = [
            models.Index(fields=["restaurant", "cashier", "-opened_at"]),
        ]

    @property
    def is_open(self) -> bool:
        return self.closed_at is None

    def close(self, closing_balance: int, notes: str = ""):
        """Close the drawer session and calculate variance."""
        from django.utils import timezone
        from django.db.models import Sum

        # Calculate expected: opening + cash payments received
        cash_payments = Payment.objects.filter(
            restaurant=self.restaurant,
            provider_code="cash",
            status=PaymentStatus.SUCCESS,
            completed_at__gte=self.opened_at,
            completed_at__lt=timezone.now(),
        ).aggregate(total=Sum("amount"))["total"] or 0

        self.expected_balance = self.opening_balance + cash_payments
        self.closing_balance = closing_balance
        self.variance = closing_balance - self.expected_balance
        self.variance_notes = notes
        self.closed_at = timezone.now()
        self.save()
```

### Daily Reconciliation Query
```python
# apps/payments/services.py
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

def get_daily_reconciliation(restaurant, date=None):
    """
    Generate daily payment reconciliation report.

    Returns breakdown by payment method with totals.
    """
    if date is None:
        date = timezone.localdate()

    start = timezone.make_aware(
        timezone.datetime.combine(date, timezone.datetime.min.time())
    )
    end = start + timedelta(days=1)

    # Get all successful payments for the day
    payments = Payment.objects.filter(
        restaurant=restaurant,
        status=PaymentStatus.SUCCESS,
        completed_at__gte=start,
        completed_at__lt=end,
    )

    # Aggregate by provider
    by_provider = payments.values("provider_code").annotate(
        count=Count("id"),
        total=Sum("amount"),
    ).order_by("provider_code")

    # Calculate totals
    totals = payments.aggregate(
        total_count=Count("id"),
        total_amount=Sum("amount"),
    )

    # Get refunds
    refunds = Payment.objects.filter(
        restaurant=restaurant,
        status__in=[PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED],
        completed_at__gte=start,
        completed_at__lt=end,
    ).aggregate(
        refund_count=Count("id"),
        refund_amount=Sum("refunded_amount"),
    )

    return {
        "date": date.isoformat(),
        "by_provider": list(by_provider),
        "totals": {
            "count": totals["total_count"] or 0,
            "amount": totals["total_amount"] or 0,
        },
        "refunds": {
            "count": refunds["refund_count"] or 0,
            "amount": refunds["refund_amount"] or 0,
        },
        "net_amount": (totals["total_amount"] or 0) - (refunds["refund_amount"] or 0),
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Polling-only | Webhook-first with polling fallback | 2023+ | Faster status updates, lower API load |
| Shared secret auth | HMAC signature verification | Standard | Prevents replay attacks, ensures integrity |
| Synchronous webhook processing | Async queue + immediate 200 | Best practice | Prevents timeout-triggered retries |
| Manual idempotency | Redis atomic locks | Best practice | Prevents race conditions |
| django-fsm (archived) | django-fsm-2 (maintained) | 2024 | Active maintenance, bug fixes |

**Deprecated/outdated:**
- `mtnmomo` Python package: No longer maintained as of July 2025; implement direct API integration
- Synchronous webhook handlers: Always causes timeout issues; use Celery

## Open Questions

Things that couldn't be fully resolved:

1. **MTN MoMo Callback Signature Verification**
   - What we know: Production supports HTTPS callbacks; sandbox doesn't support callbacks at all
   - What's unclear: Exact signature verification method for production callbacks (not in public docs)
   - Recommendation: Implement polling as primary for now; add signature verification when production docs available

2. **Orange Money Notification Reliability**
   - What we know: Notifications can be delayed or missing; polling recommended
   - What's unclear: Whether this is region-specific (Ivory Coast vs Senegal)
   - Recommendation: Always implement polling fallback; poll every 2 minutes

3. **Wave Refund Limits**
   - What we know: Refund API is idempotent; respects transaction limits
   - What's unclear: Specific time limits on refund eligibility
   - Recommendation: Allow refund attempts; handle rejection gracefully

4. **Provider-Specific Currencies in Sandbox vs Production**
   - What we know: MTN sandbox uses EUR; production uses local currency (XOF for Ivory Coast)
   - What's unclear: Whether Orange Money has similar sandbox limitations
   - Recommendation: Abstract currency handling per environment in provider config

## Sources

### Primary (HIGH confidence)
- [Wave Checkout API](https://docs.wave.com/checkout) - Complete checkout flow documentation
- [Wave Webhook Documentation](https://docs.wave.com/webhook) - Signature verification, event types
- [MTN MoMo Developer Portal](https://momodeveloper.mtn.com/api-documentation) - Collection API, sandbox setup

### Secondary (MEDIUM confidence)
- [MTN MoMo Sandbox Postman Guide](https://gist.github.com/chaiwa-berian/5294fdf1360247cf4561c95c8fa740d4) - Step-by-step testing
- [Orange Money PHP SDK](https://github.com/Foris-master/orange-money-sdk) - API patterns
- [Orange Developer Portal](https://developer.orange.com/apis/om-webpay) - Overview (limited technical detail)
- [django-fsm-2 GitHub](https://github.com/django-commons/django-fsm-2) - State machine usage

### Tertiary (LOW confidence)
- [mtnmomo Python package](https://github.com/sparkplug/momoapi-python) - Deprecated but shows patterns
- Community blog posts on idempotency patterns - General guidance
- Orange Money notification reliability - Based on SDK documentation comments

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - Libraries verified; provider SDKs limited
- Architecture: HIGH - Strategy pattern is industry standard for multi-provider payments
- Pitfalls: MEDIUM - Based on official docs + community reports
- Provider APIs: MEDIUM - Wave well-documented; MTN okay; Orange limited

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - provider APIs may update)
