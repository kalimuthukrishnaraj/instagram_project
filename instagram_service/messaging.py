"""
Instagram Direct Messages (Instagram Messaging API).

Reads (list_conversations / get_messages) work any time. Sends are
constrained by Meta's 24h "standard messaging window": you can only send a
free-form message to someone within 24h of their last message to you.
Outside that window Meta rejects the send outright, so
is_within_messaging_window() / send_message()'s guard raise a clear local
exception instead of burning an API call to find that out.

Automated sends are also throttled (~200/hr/account) — that's enforced by
Meta, not checked here.
"""

import json
import time
from datetime import datetime

from .client import call_graph_api, call_graph_api_paginated
from .exceptions import MessagingWindowExpiredError

DEFAULT_CONVERSATION_FIELDS = "id,updated_time,participants"
DEFAULT_MESSAGE_FIELDS = "id,created_time,from,to,message"
MESSAGING_WINDOW_HOURS = 24


def list_conversations(ig_user_id, access_token, fields=DEFAULT_CONVERSATION_FIELDS, limit=25):
    """Fetch one page of Instagram DM conversations for this account."""
    return call_graph_api(
        f"{ig_user_id}/conversations",
        access_token,
        params={"platform": "instagram", "fields": fields, "limit": limit},
    )


def get_all_conversations(ig_user_id, access_token, fields=DEFAULT_CONVERSATION_FIELDS, max_pages=None):
    """Fetch ALL conversations, following pagination. Returns a flat list."""
    items = []
    for page in call_graph_api_paginated(
        f"{ig_user_id}/conversations",
        access_token,
        params={"platform": "instagram", "fields": fields, "limit": 50},
        max_pages=max_pages,
    ):
        items.extend(page.get("data", []))
    return items


def get_messages(conversation_id, access_token, fields=DEFAULT_MESSAGE_FIELDS, limit=25):
    """
    Fetch messages within one conversation (newest first).
    Returns dict; the messages themselves are at result["messages"]["data"].
    """
    return call_graph_api(
        conversation_id,
        access_token,
        params={"fields": f"messages.limit({limit}){{{fields}}}"},
    )


def is_within_messaging_window(last_incoming_message_ts, window_hours=MESSAGING_WINDOW_HOURS):
    """
    True if last_incoming_message_ts is recent enough to still send a
    free-form reply. Accepts a Unix timestamp (int/float) or an ISO 8601
    string as Graph API returns in created_time (e.g. "2026-09-15T10:00:00+0000").
    """
    if isinstance(last_incoming_message_ts, str):
        ts_str = last_incoming_message_ts.replace("+0000", "+00:00")
        last_incoming_message_ts = datetime.fromisoformat(ts_str).timestamp()

    return (time.time() - last_incoming_message_ts) <= window_hours * 3600


def send_message(ig_user_id, recipient_id, message, access_token, last_incoming_message_ts=None):
    """
    Send a DM to recipient_id from the connected IG account.
    Requires instagram_business_manage_messages scope.

    Pass last_incoming_message_ts (from get_messages/list_conversations) to
    guard the send: if the 24h window has closed, raises
    MessagingWindowExpiredError locally instead of letting Meta reject the
    call. Omit it only if you've already confirmed the window is open.

    Returns dict: {"recipient_id": ..., "message_id": ...}
    """
    if last_incoming_message_ts is not None and not is_within_messaging_window(last_incoming_message_ts):
        raise MessagingWindowExpiredError(
            f"The 24h standard messaging window for recipient {recipient_id} has "
            "closed — Meta only allows free-form replies within 24h of their last "
            "message to this account."
        )

    return call_graph_api(
        f"{ig_user_id}/messages",
        access_token,
        params={
            "recipient": json.dumps({"id": recipient_id}),
            "message": json.dumps({"text": message}),
        },
        method="POST",
    )
