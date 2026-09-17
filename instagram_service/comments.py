from .client import call_graph_api, call_graph_api_paginated

# Graph API's top-level "username" field is unreliable — it's populated for
# the account's own comments but often comes back empty for other
# commenters. "from" (id + username) is the field that's actually populated
# for everyone, so it's included by default here rather than as an opt-in.
DEFAULT_COMMENT_FIELDS = "id,text,username,from,timestamp,like_count,replies"


def get_comments(media_id, access_token, fields=DEFAULT_COMMENT_FIELDS, limit=25):
    """Fetch one page of top-level comments on a media object."""
    return call_graph_api(
        f"{media_id}/comments",
        access_token,
        params={"fields": fields, "limit": limit},
    )


def get_all_comments(media_id, access_token, fields=DEFAULT_COMMENT_FIELDS, max_pages=None):
    """Fetch ALL comments on a media object, following pagination. Returns a flat list."""
    items = []
    for page in call_graph_api_paginated(
        f"{media_id}/comments",
        access_token,
        params={"fields": fields, "limit": 50},
        max_pages=max_pages,
    ):
        items.extend(page.get("data", []))
    return items


def get_comment_details(comment_id, access_token, fields=DEFAULT_COMMENT_FIELDS):
    """Fetch a single comment by ID (e.g. to inspect its replies)."""
    return call_graph_api(comment_id, access_token, params={"fields": fields})


def get_replies(comment_id, access_token, fields=DEFAULT_COMMENT_FIELDS, limit=25):
    """Fetch replies to a specific comment (comments are only one level deep on IG)."""
    return call_graph_api(
        f"{comment_id}/replies",
        access_token,
        params={"fields": fields, "limit": limit},
    )


def reply_to_comment(comment_id, message, access_token):
    """
    Reply to a comment. Requires instagram_manage_comments scope.
    Returns dict: {"id": "<new_comment_id>"}
    """
    return call_graph_api(
        f"{comment_id}/replies",
        access_token,
        params={"message": message},
        method="POST",
    )


def reply_to_media(media_id, message, access_token):
    """
    Post a new top-level comment on a media object.
    Requires instagram_manage_comments scope.
    """
    return call_graph_api(
        f"{media_id}/comments",
        access_token,
        params={"message": message},
        method="POST",
    )


def delete_comment(comment_id, access_token):
    """
    Delete (or hide) a comment. Requires instagram_manage_comments scope.
    Returns dict: {"success": true}
    """
    return call_graph_api(comment_id, access_token, method="DELETE")


def set_comment_visibility(comment_id, access_token, hide=True):
    """
    Hide or unhide a comment without deleting it.
    Requires instagram_manage_comments scope.
    """
    return call_graph_api(
        comment_id,
        access_token,
        params={"hide": "true" if hide else "false"},
        method="POST",
    )
