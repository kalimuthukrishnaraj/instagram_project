"""
MCP server exposing instagram_service as tools for a Claude agent.

Every tool here is a thin wrapper over instagram_service's existing modules
— no business logic lives here.

Read tools (get_account_profile, list_media, ...) are safe to call freely.
Write tools that post/reply/send publicly or irreversibly are called out in
their own docstrings — callers (Claude) must show the user what will happen
and get explicit go-ahead before invoking them. publish_post in particular
is split from preview_post: preview_post only builds a container and reports
its status/quota, publish_post is the one call that actually goes live.

Run directly for local testing:
    python3 mcp_server.py
Or register it with an MCP client (Claude Desktop / Claude Code) to point
at this file — see the project's MCP_Integration_Plan.md, Phase 6.
"""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from instagram_service import comments as comments_service
from instagram_service import media as media_service
from instagram_service import insights as insights_service
from instagram_service import publishing as publishing_service
from instagram_service import messaging as messaging_service

# instagram_service/.env holds the real secrets; this file lives at the
# project root, one level up, so point load_dotenv at it explicitly rather
# than relying on its default upward search.
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram_service", ".env")
load_dotenv(_ENV_PATH)

IG_USER_ID = os.environ["IG_USER_ID"]
ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]

# Video/reels containers take much longer to process than images.
IMAGE_CONTAINER_TIMEOUT_SECONDS = 60
VIDEO_CONTAINER_TIMEOUT_SECONDS = 180

mcp = FastMCP("krish-instagram")


# ---------------------------------------------------------------------------
# Reads: account, media, insights
# ---------------------------------------------------------------------------

@mcp.tool()
def get_account_profile() -> dict:
    """Get the connected Instagram account's current follower count and media count."""
    return insights_service.get_follower_count(IG_USER_ID, ACCESS_TOKEN)


@mcp.tool()
def list_media(limit: int = 25) -> dict:
    """List recent media posts (id, caption, media_type, media_url, permalink,
    timestamp, like_count, comments_count) on the connected account."""
    return media_service.get_media(IG_USER_ID, ACCESS_TOKEN, limit=limit)


@mcp.tool()
def get_media_insights(media_id: str) -> dict:
    """Get insights (reach, likes, comments, saved, shares) for one media item, as a flat {metric: value} dict."""
    return insights_service.get_media_insights_dict(media_id, ACCESS_TOKEN)


# ---------------------------------------------------------------------------
# Comments: read + moderate
# ---------------------------------------------------------------------------

@mcp.tool()
def list_comments(media_id: str, limit: int = 25) -> dict:
    """List top-level comments (id, text, username, timestamp, like_count) on a media item."""
    return comments_service.get_comments(media_id, ACCESS_TOKEN, limit=limit)


@mcp.tool()
def reply_to_comment(comment_id: str, message: str) -> dict:
    """Post a public reply to a specific comment. This posts immediately and
    is visible to everyone — show the exact reply text and get explicit
    go-ahead from the user before calling this."""
    return comments_service.reply_to_comment(comment_id, message, ACCESS_TOKEN)


@mcp.tool()
def hide_comment(comment_id: str, hide: bool = True) -> dict:
    """Hide or unhide a comment without deleting it. Reversible — confirm
    with the user which comment and direction (hide vs unhide) first."""
    return comments_service.set_comment_visibility(comment_id, ACCESS_TOKEN, hide=hide)


@mcp.tool()
def delete_comment(comment_id: str) -> dict:
    """Permanently delete a comment. This is irreversible — confirm the
    exact comment_id with the user before calling this."""
    return comments_service.delete_comment(comment_id, ACCESS_TOKEN)


# ---------------------------------------------------------------------------
# Publishing: preview (build container) / publish (go live) pair
# ---------------------------------------------------------------------------

@mcp.tool()
def preview_post(caption: str = "", media_type: str = "IMAGE", image_url: str = None, video_url: str = None) -> dict:
    """Build a media container for a new post and wait for it to finish
    processing. Does NOT publish anything — nothing goes live from this
    call. Returns the container_id plus current publishing quota usage.
    Show the caller the caption/media preview and current quota, and only
    call publish_post with this container_id once the user explicitly
    confirms. media_type: IMAGE | VIDEO | REELS. Pass exactly one of
    image_url/video_url."""
    quota = publishing_service.get_publishing_limit(IG_USER_ID, ACCESS_TOKEN)
    container = publishing_service.create_media_container(
        IG_USER_ID,
        ACCESS_TOKEN,
        media_type=media_type,
        image_url=image_url,
        video_url=video_url,
        caption=caption,
    )
    container_id = container["id"]
    timeout = (
        VIDEO_CONTAINER_TIMEOUT_SECONDS
        if media_type in ("VIDEO", "REELS")
        else IMAGE_CONTAINER_TIMEOUT_SECONDS
    )
    status = publishing_service.wait_for_container_ready(container_id, ACCESS_TOKEN, timeout=timeout)
    return {
        "container_id": container_id,
        "container_status": status,
        "caption": caption,
        "media_type": media_type,
        "publishing_quota": quota,
    }


@mcp.tool()
def publish_post(container_id: str) -> dict:
    """Publish a container previously built by preview_post. This makes the
    post public immediately and cannot be undone through this API — only
    call this after the user has explicitly confirmed the preview_post
    result."""
    return publishing_service.publish_container(IG_USER_ID, container_id, ACCESS_TOKEN)


# ---------------------------------------------------------------------------
# Direct messages
# ---------------------------------------------------------------------------

@mcp.tool()
def list_conversations(limit: int = 25) -> dict:
    """List Instagram DM conversations for this account."""
    return messaging_service.list_conversations(IG_USER_ID, ACCESS_TOKEN, limit=limit)


@mcp.tool()
def get_messages(conversation_id: str, limit: int = 25) -> dict:
    """Get messages within one DM conversation (newest first). Use the
    sender's most recent created_time from here as last_incoming_message_ts
    when calling send_message_reply."""
    return messaging_service.get_messages(conversation_id, ACCESS_TOKEN, limit=limit)


@mcp.tool()
def send_message_reply(recipient_id: str, message: str, last_incoming_message_ts: str = None) -> dict:
    """Send a DM reply to recipient_id. This sends immediately — show the
    exact message text and get explicit go-ahead from the user before
    calling this. Pass last_incoming_message_ts (from get_messages) so the
    24h messaging window is checked locally before sending; if it's closed
    this raises instead of letting Meta reject the call."""
    return messaging_service.send_message(
        IG_USER_ID, recipient_id, message, ACCESS_TOKEN, last_incoming_message_ts=last_incoming_message_ts
    )


if __name__ == "__main__":
    mcp.run()
