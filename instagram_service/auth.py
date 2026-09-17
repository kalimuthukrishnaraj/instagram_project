"""
Token lifecycle management — Instagram Login (Business Login for Instagram).

This matches tokens that start with "IGAA" (as opposed to "EAA" tokens from
Facebook Login for Business, which use a different host and different
exchange/refresh endpoints entirely).

Flow:
1. You already have a short-lived Instagram User access token (from the
   OAuth redirect at api.instagram.com/oauth/authorize).
2. exchange_long_lived_token() swaps it for a long-lived token (~60 days).
3. Store the returned token + expires_in (persist it — e.g. DB row with an
   expiry timestamp). Don't just keep it in memory.
4. Before it expires (e.g. daily cron, or check-on-startup), call
   refresh_long_lived_token() to get a fresh 60-day token.
   Note: a long-lived token can only be refreshed once it's at least 24
   hours old, and refreshing again resets the 60-day clock.
"""

import time
import requests

from . import config
from .exceptions import parse_graph_error

# Note: unlike Facebook Login's oauth/access_token endpoint, these Instagram
# Login endpoints don't include an API version in the path, and don't take
# a client_id — only the app secret and the token being exchanged/refreshed.
EXCHANGE_URL = "https://graph.instagram.com/access_token"
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"


def exchange_long_lived_token(short_lived_token):
    """
    Exchange a short-lived Instagram User token for a long-lived one (~60 days).
    Returns dict: {"access_token": ..., "token_type": ..., "expires_in": ...}
    """
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": config.APP_SECRET,
        "access_token": short_lived_token,
    }
    response = requests.get(EXCHANGE_URL, params=params, timeout=config.DEFAULT_TIMEOUT)
    return _parse_or_raise(response)


def refresh_long_lived_token(current_long_lived_token):
    """
    Refresh an existing long-lived token before it expires.
    Must be at least 24h old to be eligible for refresh.
    Returns the same shape as exchange_long_lived_token().
    Note: no client_secret needed here — just the current token.
    """
    params = {
        "grant_type": "ig_refresh_token",
        "access_token": current_long_lived_token,
    }
    response = requests.get(REFRESH_URL, params=params, timeout=config.DEFAULT_TIMEOUT)
    return _parse_or_raise(response)


def compute_expiry_timestamp(expires_in_seconds):
    """Helper: convert 'expires_in' (seconds from now) into a Unix timestamp to store."""
    return int(time.time()) + int(expires_in_seconds)


def is_token_near_expiry(expiry_timestamp, buffer_days=5):
    """
    True if the stored token will expire within buffer_days.
    Use this in a daily job to decide whether to call refresh_long_lived_token().
    """
    buffer_seconds = buffer_days * 24 * 60 * 60
    return time.time() >= (expiry_timestamp - buffer_seconds)


def _parse_or_raise(response):
    if response.ok:
        return response.json()
    try:
        body = response.json()
    except ValueError:
        body = {"error": {"message": response.text, "code": response.status_code}}
    raise parse_graph_error(body, http_status=response.status_code)
