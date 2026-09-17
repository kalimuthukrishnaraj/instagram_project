import responses
import pytest

from instagram_service.client import call_graph_api, call_graph_api_paginated
from instagram_service.exceptions import TokenExpiredError, RateLimitError, GraphAPIError


@responses.activate
def test_call_graph_api_success(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/me/media",
        json={"data": [{"id": "123", "caption": "hello"}]},
        status=200,
    )

    result = call_graph_api("me/media", token, params={"fields": "id,caption"})

    assert result["data"][0]["id"] == "123"


@responses.activate
def test_call_graph_api_raises_token_expired(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/me/media",
        json={"error": {"message": "Token expired", "code": 190, "error_subcode": 463}},
        status=401,
    )

    with pytest.raises(TokenExpiredError) as exc_info:
        call_graph_api("me/media", token)

    assert exc_info.value.code == 190


@responses.activate
def test_call_graph_api_retries_on_rate_limit_then_succeeds(base_url, token, monkeypatch):
    # Skip real sleep delays during the test
    monkeypatch.setattr("instagram_service.client._sleep_backoff", lambda attempt: None)

    responses.add(
        responses.GET,
        f"{base_url}/me/media",
        json={"error": {"message": "Rate limited", "code": 4}},
        status=429,
    )
    responses.add(
        responses.GET,
        f"{base_url}/me/media",
        json={"data": [{"id": "123"}]},
        status=200,
    )

    result = call_graph_api("me/media", token)

    assert result["data"][0]["id"] == "123"
    assert len(responses.calls) == 2


@responses.activate
def test_call_graph_api_exhausts_retries_and_raises(base_url, token, monkeypatch):
    monkeypatch.setattr("instagram_service.client._sleep_backoff", lambda attempt: None)

    # Rate-limited on every attempt
    for _ in range(3):
        responses.add(
            responses.GET,
            f"{base_url}/me/media",
            json={"error": {"message": "Rate limited", "code": 4}},
            status=429,
        )

    with pytest.raises(RateLimitError):
        call_graph_api("me/media", token)

    assert len(responses.calls) == 3


@responses.activate
def test_call_graph_api_non_retryable_error_raises_immediately(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/me/media",
        json={"error": {"message": "Unknown error", "code": 999}},
        status=400,
    )

    with pytest.raises(GraphAPIError):
        call_graph_api("me/media", token)

    # Should not retry on a non-rate-limit error
    assert len(responses.calls) == 1


@responses.activate
def test_call_graph_api_paginated_follows_next_cursor(base_url, token):
    next_url = f"{base_url}/me/media?after=CURSOR123"

    responses.add(
        responses.GET,
        f"{base_url}/me/media",
        json={
            "data": [{"id": "1"}, {"id": "2"}],
            "paging": {"next": next_url},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        next_url,
        json={"data": [{"id": "3"}]},
        status=200,
    )

    pages = list(call_graph_api_paginated("me/media", token))

    assert len(pages) == 2
    assert pages[0]["data"][0]["id"] == "1"
    assert pages[1]["data"][0]["id"] == "3"


@responses.activate
def test_call_graph_api_paginated_respects_max_pages(base_url, token):
    next_url = f"{base_url}/me/media?after=CURSOR123"

    responses.add(
        responses.GET,
        f"{base_url}/me/media",
        json={"data": [{"id": "1"}], "paging": {"next": next_url}},
        status=200,
    )
    # This second page should never be requested because max_pages=1
    responses.add(
        responses.GET,
        next_url,
        json={"data": [{"id": "2"}]},
        status=200,
    )

    pages = list(call_graph_api_paginated("me/media", token, max_pages=1))

    assert len(pages) == 1
    assert len(responses.calls) == 1
