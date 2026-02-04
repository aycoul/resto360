from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from apps.authentication.models import Business

_current_business: ContextVar[Optional["Business"]] = ContextVar(
    "current_business", default=None
)


def get_current_business() -> Optional["Business"]:
    """Get the current business from thread-local context."""
    return _current_business.get()


def set_current_business(business: Optional["Business"]) -> None:
    """Set the current business in thread-local context."""
    _current_business.set(business)


# Backwards compatibility aliases
def get_current_restaurant() -> Optional["Business"]:
    """Backwards compatibility: alias for get_current_business."""
    return get_current_business()


def set_current_restaurant(restaurant: Optional["Business"]) -> None:
    """Backwards compatibility: alias for set_current_business."""
    set_current_business(restaurant)
