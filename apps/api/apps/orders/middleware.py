"""WebSocket middleware for JWT authentication."""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_str):
    """
    Validate JWT token and return the associated user.

    Args:
        token_str: JWT access token string

    Returns:
        User instance if valid, AnonymousUser if invalid
    """
    try:
        token = AccessToken(token_str)
        user_id = token.payload.get("user_id")
        return User.objects.select_related("restaurant").get(id=user_id)
    except (TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT authentication middleware for WebSocket connections.

    Extracts JWT token from query string parameter 'token'
    and sets scope['user'] to the authenticated user.

    Usage:
        ws://host/ws/kitchen/{restaurant_id}/?token={jwt_access_token}
    """

    async def __call__(self, scope, receive, send):
        """Process the WebSocket connection with JWT authentication."""
        # Parse query string to extract token
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
