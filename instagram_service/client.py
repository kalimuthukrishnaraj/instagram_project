import time
import logging
import requests

from . import config
from .exceptions import parse_graph_error, RateLimitError

logger = logging.getLogger("instagram_service.client")


def call_graph_api(endpoint, access_token, params=None, method="GET", data=None):
    """
    Single choke point for every Graph API call.
    - Injects base URL, version, and token
    - Retries with exponential backoff on rate limits / transient errors
    - Raises a typed exception (see exceptions.py) on failure
    - Logs usage headers so you can see how close you are to limits

    endpoint: e.g. "17895695668004550" or "me/media" (no leading slash needed)
    """
    url = f"{config.GRAPH_API_BASE_URL}/{endpoint.lstrip('/')}"
    params = dict(params or {})
    params["access_token"] = access_token

    last_exception = None

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            # Graph API accepts its call params as query string on every verb,
            # not just GET, so always send `params`. `data` is only for the
            # rare case of an actual request body on top of that.
            response = requests.request(
                method,
                url,
                params=params,
                data=data,
                timeout=config.DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            # Network-level failure (timeout, DNS, connection reset) — retry
            last_exception = exc
            logger.warning("Network error on attempt %d/%d: %s", attempt, config.MAX_RETRIES, exc)
            _sleep_backoff(attempt)
            continue

        _log_rate_limit_usage(response)

        if response.ok:
            return response.json()

        # Non-2xx response — try to parse Graph API's structured error
        try:
            body = response.json()
        except ValueError:
            body = {"error": {"message": response.text, "code": response.status_code}}

        error = parse_graph_error(body, http_status=response.status_code)
        last_exception = error

        if isinstance(error, RateLimitError) and attempt < config.MAX_RETRIES:
            logger.warning("Rate limited (attempt %d/%d): %s", attempt, config.MAX_RETRIES, error.message)
            _sleep_backoff(attempt)
            continue

        # Not retryable (bad token, permission error, etc.) — raise immediately
        raise error

    # Exhausted retries
    raise last_exception


def call_graph_api_paginated(endpoint, access_token, params=None, method="GET", max_pages=None):
    """
    Generator that yields each page's raw JSON dict.
    Follows paging.next automatically until there are no more pages
    or max_pages is reached. Use this instead of assuming one page = all data.

    Usage:
        for page in call_graph_api_paginated("me/media", token, {"fields": "id,caption"}):
            for item in page.get("data", []):
                ...
    """
    page_count = 0
    next_url = None
    current_params = dict(params or {})

    while True:
        if next_url:
            # 'next' URLs from Graph API already contain all needed query params
            resp = requests.get(next_url, timeout=config.DEFAULT_TIMEOUT)
            if not resp.ok:
                try:
                    body = resp.json()
                except ValueError:
                    body = {"error": {"message": resp.text, "code": resp.status_code}}
                raise parse_graph_error(body, http_status=resp.status_code)
            page = resp.json()
        else:
            page = call_graph_api(endpoint, access_token, current_params, method)

        yield page
        page_count += 1

        next_url = page.get("paging", {}).get("next")
        if not next_url:
            break
        if max_pages is not None and page_count >= max_pages:
            break


def _sleep_backoff(attempt):
    delay = config.BACKOFF_BASE_SECONDS ** attempt
    time.sleep(delay)


def _log_rate_limit_usage(response):
    """
    Meta sends usage as a JSON string in this header, e.g.:
    {"call_count": 12, "total_cputime": 3, "total_time": 5}
    Log it so you have visibility before you actually get throttled.
    """
    usage_header = response.headers.get("X-Business-Use-Case-Usage") or response.headers.get(
        "X-App-Usage"
    )
    if usage_header:
        logger.debug("Rate limit usage: %s", usage_header)
