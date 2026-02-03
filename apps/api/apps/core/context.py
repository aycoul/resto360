from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from apps.authentication.models import Restaurant

_current_restaurant: ContextVar[Optional["Restaurant"]] = ContextVar(
    "current_restaurant", default=None
)


def get_current_restaurant() -> Optional["Restaurant"]:
    """Get the current restaurant from thread-local context."""
    return _current_restaurant.get()


def set_current_restaurant(restaurant: Optional["Restaurant"]) -> None:
    """Set the current restaurant in thread-local context."""
    _current_restaurant.set(restaurant)
