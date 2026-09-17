"""
MCP-layer tests: call tools the way an MCP client would (mcp.call_tool),
not by calling the wrapped Python functions directly, so these confirm
what a real client actually sees — including FastMCP's exception wrapping,
which turns any exception raised inside a tool into
ToolError("Error executing tool <name>: <message>"). Our typed
GraphAPIError/MessagingWindowExpiredError/etc. subclasses only pass a plain
message to Exception.__init__, so that wrapped message is exactly what
Claude (or any MCP client) would see as the tool's error text.
"""

import asyncio
import json
import os

# mcp_server reads IG_USER_ID/IG_ACCESS_TOKEN from the environment at import
# time. Set fake values before importing it so this suite doesn't depend on
# a real instagram_service/.env file existing — load_dotenv() never
# overrides variables already set in os.environ.
os.environ["IG_USER_ID"] = "17841400000000000"
os.environ["IG_ACCESS_TOKEN"] = "fake-token-for-tests"

import responses
from mcp.server.fastmcp.exceptions import ToolError

import mcp_server

IG_USER_ID = mcp_server.IG_USER_ID


def call_tool(name, arguments=None):
    """Run an MCP tool call to completion and return the parsed JSON result."""
    result = asyncio.run(mcp_server.mcp.call_tool(name, arguments or {}))
    return json.loads(result[0].text)


@responses.activate
def test_get_account_profile_round_trips(base_url):
    responses.add(
        responses.GET,
        f"{base_url}/{IG_USER_ID}",
        json={"followers_count": 8, "media_count": 4, "id": IG_USER_ID},
        status=200,
    )

    result = call_tool("get_account_profile")

    assert result["followers_count"] == 8


@responses.activate
def test_list_media_maps_token_expired_to_tool_error(base_url):
    responses.add(
        responses.GET,
        f"{base_url}/{IG_USER_ID}/media",
        json={"error": {"message": "Token expired", "code": 190}},
        status=401,
    )

    try:
        asyncio.run(mcp_server.mcp.call_tool("list_media", {}))
        assert False, "expected ToolError"
    except ToolError as exc:
        assert "list_media" in str(exc)
        assert "Token expired" in str(exc)


@responses.activate
def test_publish_post_maps_quota_exceeded_to_tool_error(base_url):
    responses.add(
        responses.POST,
        f"{base_url}/{IG_USER_ID}/media_publish",
        json={"error": {"message": "Publishing limit reached", "code": 9007}},
        status=400,
    )

    try:
        asyncio.run(mcp_server.mcp.call_tool("publish_post", {"container_id": "container1"}))
        assert False, "expected ToolError"
    except ToolError as exc:
        assert "publish_post" in str(exc)
        assert "Publishing limit reached" in str(exc)


@responses.activate
def test_preview_post_maps_container_error_to_tool_error(base_url):
    responses.add(
        responses.GET,
        f"{base_url}/{IG_USER_ID}/content_publishing_limit",
        json={"data": [{"config": {"quota_total": 50}, "quota_usage": 1}]},
        status=200,
    )
    responses.add(
        responses.POST,
        f"{base_url}/{IG_USER_ID}/media",
        json={"id": "container1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_url}/container1",
        json={"status_code": "ERROR", "status": "Media download failed"},
        status=200,
    )

    try:
        asyncio.run(
            mcp_server.mcp.call_tool(
                "preview_post",
                {"caption": "test", "media_type": "IMAGE", "image_url": "https://example.com/pic.jpg"},
            )
        )
        assert False, "expected ToolError"
    except ToolError as exc:
        assert "preview_post" in str(exc)
        assert "container1" in str(exc)


def test_send_message_reply_maps_stale_window_to_tool_error():
    try:
        asyncio.run(
            mcp_server.mcp.call_tool(
                "send_message_reply",
                {
                    "recipient_id": "user1",
                    "message": "hello",
                    "last_incoming_message_ts": "2020-01-01T00:00:00+0000",
                },
            )
        )
        assert False, "expected ToolError"
    except ToolError as exc:
        assert "send_message_reply" in str(exc)
        assert "24h" in str(exc)
