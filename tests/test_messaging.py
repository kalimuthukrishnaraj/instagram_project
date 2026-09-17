import time

import pytest
import responses

from instagram_service import messaging
from instagram_service.exceptions import MessagingWindowExpiredError

IG_USER_ID = "17841400000000000"


@responses.activate
def test_list_conversations_sends_instagram_platform_param(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/{IG_USER_ID}/conversations",
        json={"data": [{"id": "conv1"}]},
        status=200,
    )

    result = messaging.list_conversations(IG_USER_ID, token)

    assert result["data"][0]["id"] == "conv1"
    sent_params = responses.calls[0].request.params
    assert sent_params["platform"] == "instagram"


@responses.activate
def test_get_all_conversations_flattens_pagination(base_url, token):
    next_url = f"{base_url}/{IG_USER_ID}/conversations?after=CURSOR123"

    responses.add(
        responses.GET,
        f"{base_url}/{IG_USER_ID}/conversations",
        json={"data": [{"id": "conv1"}], "paging": {"next": next_url}},
        status=200,
    )
    responses.add(
        responses.GET,
        next_url,
        json={"data": [{"id": "conv2"}]},
        status=200,
    )

    result = messaging.get_all_conversations(IG_USER_ID, token)

    assert [c["id"] for c in result] == ["conv1", "conv2"]


@responses.activate
def test_get_messages_requests_nested_fields(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/conv1",
        json={"messages": {"data": [{"id": "m1", "message": "hi"}]}},
        status=200,
    )

    result = messaging.get_messages("conv1", token)

    assert result["messages"]["data"][0]["message"] == "hi"
    sent_params = responses.calls[0].request.params
    assert "messages.limit(25)" in sent_params["fields"]


def test_is_within_messaging_window_true_for_recent_timestamp():
    assert messaging.is_within_messaging_window(time.time() - 60) is True


def test_is_within_messaging_window_false_for_old_timestamp():
    assert messaging.is_within_messaging_window(time.time() - 25 * 3600) is False


def test_is_within_messaging_window_accepts_iso_string():
    from datetime import datetime, timezone

    recent_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
    assert messaging.is_within_messaging_window(recent_iso) is True


@responses.activate
def test_send_message_sends_recipient_and_message_json(base_url, token):
    responses.add(
        responses.POST,
        f"{base_url}/{IG_USER_ID}/messages",
        json={"recipient_id": "user1", "message_id": "msg1"},
        status=200,
    )

    result = messaging.send_message(IG_USER_ID, "user1", "Thanks for reaching out!", token)

    assert result["message_id"] == "msg1"
    sent_params = responses.calls[0].request.params
    assert sent_params["recipient"] == '{"id": "user1"}'
    assert sent_params["message"] == '{"text": "Thanks for reaching out!"}'


def test_send_message_raises_when_window_closed(token):
    stale_ts = time.time() - 25 * 3600

    with pytest.raises(MessagingWindowExpiredError):
        messaging.send_message(IG_USER_ID, "user1", "hello", token, last_incoming_message_ts=stale_ts)
