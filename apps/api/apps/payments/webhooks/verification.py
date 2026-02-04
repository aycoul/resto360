"""Webhook signature verification utilities."""

import hashlib
import hmac
import logging
import time

logger = logging.getLogger(__name__)


def verify_wave_signature(
    headers: dict,
    body: bytes,
    secret: str,
    max_age_seconds: int = 300,
) -> bool:
    """
    Verify the authenticity of a Wave webhook request.

    Wave uses HMAC-SHA256 signature verification with timestamp.
    The signature header format is: "t={timestamp},v1={signature}"

    Args:
        headers: Request headers (must contain 'Wave-Signature')
        body: Raw request body (bytes, not parsed JSON)
        secret: Webhook secret from Wave dashboard
        max_age_seconds: Maximum age of webhook to accept (default 5 minutes)

    Returns:
        True if the webhook is authentic and not expired, False otherwise
    """
    if not secret:
        logger.warning("Wave webhook secret not configured")
        return False

    # Get signature header (case-insensitive)
    signature_header = None
    for key, value in headers.items():
        if key.lower() == "wave-signature":
            signature_header = value
            break

    if not signature_header:
        logger.warning("Wave-Signature header missing")
        return False

    # Parse the signature header
    # Format: "t={timestamp},v1={signature}"
    try:
        parts = {}
        for part in signature_header.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key.strip()] = value.strip()

        timestamp_str = parts.get("t")
        signature = parts.get("v1")

        if not timestamp_str or not signature:
            logger.warning("Invalid Wave-Signature header format")
            return False

        timestamp = int(timestamp_str)

    except (ValueError, AttributeError) as e:
        logger.warning("Failed to parse Wave-Signature header: %s", e)
        return False

    # Check timestamp is not too old (replay attack protection)
    current_time = int(time.time())
    if abs(current_time - timestamp) > max_age_seconds:
        logger.warning(
            "Wave webhook timestamp too old: %d (current: %d)",
            timestamp,
            current_time,
        )
        return False

    # Compute expected signature
    # The signed payload is: {timestamp}.{body}
    if isinstance(body, str):
        body = body.encode("utf-8")

    signed_payload = f"{timestamp}.".encode("utf-8") + body
    expected_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=signed_payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Compare signatures (constant-time comparison)
    if not hmac.compare_digest(expected_signature, signature):
        logger.warning("Wave webhook signature mismatch")
        return False

    return True
