import time
import responses

from instagram_service import auth


@responses.activate
def test_exchange_long_lived_token():
    responses.add(
        responses.GET,
        auth.EXCHANGE_URL,
        json={"access_token": "long-lived-abc", "token_type": "bearer", "expires_in": 5184000},
        status=200,
    )

    result = auth.exchange_long_lived_token("short-lived-xyz")

    assert result["access_token"] == "long-lived-abc"
    assert result["expires_in"] == 5184000
    sent_params = responses.calls[0].request.params
    assert sent_params["access_token"] == "short-lived-xyz"
    assert sent_params["grant_type"] == "ig_exchange_token"


@responses.activate
def test_refresh_long_lived_token():
    responses.add(
        responses.GET,
        auth.REFRESH_URL,
        json={"access_token": "refreshed-abc", "token_type": "bearer", "expires_in": 5184000},
        status=200,
    )

    result = auth.refresh_long_lived_token("long-lived-abc")

    assert result["access_token"] == "refreshed-abc"
    sent_params = responses.calls[0].request.params
    assert sent_params["grant_type"] == "ig_refresh_token"
    assert "client_secret" not in sent_params


def test_compute_expiry_timestamp_is_in_the_future():
    expiry = auth.compute_expiry_timestamp(3600)
    assert expiry > time.time()


def test_is_token_near_expiry_true_when_within_buffer():
    expiry = int(time.time()) + (2 * 24 * 60 * 60)
    assert auth.is_token_near_expiry(expiry, buffer_days=5) is True


def test_is_token_near_expiry_false_when_far_out():
    expiry = int(time.time()) + (30 * 24 * 60 * 60)
    assert auth.is_token_near_expiry(expiry, buffer_days=5) is False
