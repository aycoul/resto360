"""Payment providers package."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import PaymentProvider


def get_provider(provider_code: str) -> "PaymentProvider":
    """
    Get the payment provider instance for the given provider code.

    Args:
        provider_code: The provider identifier (wave, orange, mtn, cash)

    Returns:
        PaymentProvider instance

    Raises:
        ValueError: If provider_code is not recognized
    """
    # Import here to avoid circular imports
    from .cash import CashProvider
    from .orange import OrangeProvider
    from .wave import WaveProvider

    providers = {
        "cash": CashProvider,
        "orange": OrangeProvider,
        "wave": WaveProvider,
        # MTN MoMo provider will be added in this plan:
        # "mtn": MTNProvider,
    }

    provider_class = providers.get(provider_code)
    if provider_class is None:
        raise ValueError(f"Unknown payment provider: {provider_code}")

    return provider_class()
