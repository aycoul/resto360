"""Factories for creating test instances of payment models."""

import uuid

import factory
from factory.django import DjangoModelFactory

from apps.authentication.tests.factories import (
    BusinessFactory,
    CashierFactory,
    OwnerFactory,
)
from apps.orders.tests.factories import OrderFactory

from apps.payments.models import (
    CashDrawerSession,
    Payment,
    PaymentMethod,
    PaymentStatus,
)


class PaymentMethodFactory(DjangoModelFactory):
    """Factory for creating PaymentMethod instances."""

    class Meta:
        model = PaymentMethod

    business = factory.SubFactory(BusinessFactory)
    provider_code = "cash"
    name = "Cash"
    is_active = True
    config = {}
    display_order = 0


class PaymentFactory(DjangoModelFactory):
    """Factory for creating Payment instances."""

    class Meta:
        model = Payment

    business = factory.LazyAttribute(lambda o: o.order.business)
    order = factory.SubFactory(OrderFactory)
    payment_method = factory.LazyAttribute(
        lambda o: PaymentMethodFactory(
            business=o.order.business, provider_code="cash"
        )
    )
    amount = 10000
    status = PaymentStatus.PENDING
    idempotency_key = factory.LazyFunction(lambda: f"idem_{uuid.uuid4().hex[:16]}")
    provider_code = factory.LazyAttribute(lambda o: o.payment_method.provider_code)
    provider_reference = ""
    provider_response = {}
    refunded_amount = 0


class CashDrawerSessionFactory(DjangoModelFactory):
    """Factory for creating CashDrawerSession instances."""

    class Meta:
        model = CashDrawerSession

    business = factory.LazyAttribute(lambda o: o.cashier.business)
    cashier = factory.SubFactory(CashierFactory)
    opening_balance = 50000
    closed_at = None
    closing_balance = None
    expected_balance = None
    variance = None
    variance_notes = ""
