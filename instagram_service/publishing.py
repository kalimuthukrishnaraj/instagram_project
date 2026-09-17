"""
Publishing media (image/video/reels/carousel posts).

Instagram's publish flow is always two steps:
1. Create a "container" — Meta downloads and processes the media
   (POST {ig-user-id}/media).
2. Once the container's status_code is FINISHED, publish it
   (POST {ig-user-id}/media_publish).

Carousels add a third step below that: create one container per child item
first, then create the parent container with children=[id1, id2, ...].

Publishing is capped on a rolling 24h window — call get_publishing_limit()
to check quota_usage against config before publishing rather than assuming
a fixed number (Meta's own docs are inconsistent between 25 and 50).
"""

import time

from .client import call_graph_api
from .exceptions import MediaContainerError

DEFAULT_POLL_INTERVAL_SECONDS = 2
DEFAULT_POLL_TIMEOUT_SECONDS = 60
CONTAINER_STATUS_FIELDS = "status_code,status"


def create_media_container(
    ig_user_id,
    access_token,
    media_type="IMAGE",
    image_url=None,
    video_url=None,
    caption=None,
    **extra_params,
):
    """
    Create a media container to be published later. Doesn't publish anything.
    media_type: "IMAGE" | "VIDEO" | "REELS" | "CAROUSEL"
    Pass exactly one of image_url/video_url for single-item containers.
    For a CAROUSEL parent container, omit both and pass
    children=[child_container_id, ...] via extra_params instead.
    Returns dict: {"id": "<container_id>"}
    """
    params = {"media_type": media_type}
    if image_url is not None:
        params["image_url"] = image_url
    if video_url is not None:
        params["video_url"] = video_url
    if caption is not None:
        params["caption"] = caption
    params.update(extra_params)

    return call_graph_api(
        f"{ig_user_id}/media",
        access_token,
        params=params,
        method="POST",
    )


def get_container_status(container_id, access_token, fields=CONTAINER_STATUS_FIELDS):
    """Fetch a media container's current processing status (one-shot, no polling)."""
    return call_graph_api(container_id, access_token, params={"fields": fields})


def wait_for_container_ready(
    container_id,
    access_token,
    poll_interval=DEFAULT_POLL_INTERVAL_SECONDS,
    timeout=DEFAULT_POLL_TIMEOUT_SECONDS,
):
    """
    Poll a container's status until status_code is FINISHED.
    Raises MediaContainerError if the container errors out or doesn't finish
    within `timeout` seconds (images usually finish in a few seconds; video/
    reels can take much longer, so callers publishing video should pass a
    larger timeout).
    """
    elapsed = 0
    while True:
        result = get_container_status(container_id, access_token)
        status_code = result.get("status_code")

        if status_code == "FINISHED":
            return result
        if status_code == "ERROR":
            raise MediaContainerError(
                f"Media container {container_id} failed to process: {result.get('status')}",
                raw=result,
            )
        if elapsed >= timeout:
            raise MediaContainerError(
                f"Media container {container_id} did not finish within {timeout}s "
                f"(last status_code={status_code!r})",
                raw=result,
            )

        time.sleep(poll_interval)
        elapsed += poll_interval


def publish_container(ig_user_id, container_id, access_token):
    """
    Publish a container whose status_code is FINISHED.
    Returns dict: {"id": "<new_media_id>"}
    Raises PublishingQuotaExceededError (via parse_graph_error, code 9007) if
    the rolling 24h publishing limit has been reached.
    """
    return call_graph_api(
        f"{ig_user_id}/media_publish",
        access_token,
        params={"creation_id": container_id},
        method="POST",
    )


def get_publishing_limit(ig_user_id, access_token, fields="config,quota_usage"):
    """
    Check the rolling 24h publishing quota. Returns a dict with 'quota_usage'
    (posts published in the current window) and 'config' (the window length
    and quota total) — compare against config['quota_total'] rather than
    hardcoding a number.
    """
    return call_graph_api(
        f"{ig_user_id}/content_publishing_limit",
        access_token,
        params={"fields": fields},
    )
