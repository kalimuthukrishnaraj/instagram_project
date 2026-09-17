from .client import call_graph_api, call_graph_api_paginated

DEFAULT_MEDIA_FIELDS = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"

# Used for single-item detail views where we want to actually render the
# media: adds thumbnail_url (video poster frame) and the children edge
# (carousel/album posts don't have a top-level media_url — each slide does).
DETAIL_MEDIA_FIELDS = DEFAULT_MEDIA_FIELDS + ",thumbnail_url,children{media_type,media_url,thumbnail_url}"


def get_media(ig_user_id, access_token, fields=DEFAULT_MEDIA_FIELDS, limit=25):
    """Fetch one page of media for an IG business/creator account."""
    return call_graph_api(
        f"{ig_user_id}/media",
        access_token,
        params={"fields": fields, "limit": limit},
    )


def get_all_media(ig_user_id, access_token, fields=DEFAULT_MEDIA_FIELDS, max_pages=None):
    """Fetch ALL media, following pagination automatically. Returns a flat list."""
    items = []
    for page in call_graph_api_paginated(
        f"{ig_user_id}/media",
        access_token,
        params={"fields": fields, "limit": 50},
        max_pages=max_pages,
    ):
        items.extend(page.get("data", []))
    return items


def get_media_details(media_id, access_token, fields=DETAIL_MEDIA_FIELDS):
    """Fetch a single media object by ID, with enough fields to render it
    (image/video/carousel), not just list-view metadata."""
    return call_graph_api(media_id, access_token, params={"fields": fields})
