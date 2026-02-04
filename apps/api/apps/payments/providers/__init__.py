"""Payment providers package."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import PaymentProvider


def get_provider(provider_code: str) -> "PaymentProvider":
    """
    Get the payment provider instance for the given provider code.

    Args:
        provider_code: The provider identifier (wave, orange, mtn, cash, flutterwave, paystack, cinetpay)

    Returns:
        PaymentProvider instance

    Raises:
        ValueError: If provider_code is not recognized
    """
    # Import here to avoid circular imports
    from .cash import CashProvider
    from .cinetpay import CinetPayProvider
    from .flutterwave import FlutterwaveProvider
    from .mtn import MTNProvider
    from .orange import OrangeProvider
    from .paystack import PaystackProvider
    from .wave import WaveProvider

    providers = {
        "cash": CashProvider,
        "mtn": MTNProvider,
        "orange": OrangeProvider,
        "wave": WaveProvider,
        "flutterwave": FlutterwaveProvider,
        "paystack": PaystackProvider,
        "cinetpay": CinetPayProvider,
    }

    provider_class = providers.get(provider_code)
    if provider_class is None:
        raise ValueError(f"Unknown payment provider: {provider_code}")

    return provider_class()
