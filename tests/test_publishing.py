import pytest
import responses

from instagram_service import publishing
from instagram_service.exceptions import MediaContainerError, PublishingQuotaExceededError

IG_USER_ID = "17841400000000000"


@responses.activate
def test_create_media_container_sends_image_url_and_caption(base_url, token):
    responses.add(
        responses.POST,
        f"{base_url}/{IG_USER_ID}/media",
        json={"id": "container1"},
        status=200,
    )

    result = publishing.create_media_container(
        IG_USER_ID, token, image_url="https://example.com/pic.jpg", caption="Hello world"
    )

    assert result["id"] == "container1"
    sent_params = responses.calls[0].request.params
    assert sent_params["image_url"] == "https://example.com/pic.jpg"
    assert sent_params["caption"] == "Hello world"
    assert sent_params["media_type"] == "IMAGE"


@responses.activate
def test_create_media_container_carousel_passes_children(base_url, token):
    responses.add(
        responses.POST,
        f"{base_url}/{IG_USER_ID}/media",
        json={"id": "parent1"},
        status=200,
    )

    publishing.create_media_container(
        IG_USER_ID, token, media_type="CAROUSEL", children="child1,child2"
    )

    sent_params = responses.calls[0].request.params
    assert sent_params["media_type"] == "CAROUSEL"
    assert sent_params["children"] == "child1,child2"


@responses.activate
def test_get_container_status(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/container1",
        json={"status_code": "IN_PROGRESS", "status": "In progress"},
        status=200,
    )

    result = publishing.get_container_status("container1", token)

    assert result["status_code"] == "IN_PROGRESS"


@responses.activate
def test_wait_for_container_ready_polls_until_finished(base_url, token, monkeypatch):
    monkeypatch.setattr("instagram_service.publishing.time.sleep", lambda seconds: None)

    responses.add(
        responses.GET,
        f"{base_url}/container1",
        json={"status_code": "IN_PROGRESS"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_url}/container1",
        json={"status_code": "FINISHED"},
        status=200,
    )

    result = publishing.wait_for_container_ready("container1", token, poll_interval=1)

    assert result["status_code"] == "FINISHED"
    assert len(responses.calls) == 2


@responses.activate
def test_wait_for_container_ready_raises_on_error_status(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/container1",
        json={"status_code": "ERROR", "status": "Media download failed"},
        status=200,
    )

    with pytest.raises(MediaContainerError):
        publishing.wait_for_container_ready("container1", token)


@responses.activate
def test_wait_for_container_ready_raises_on_timeout(base_url, token, monkeypatch):
    monkeypatch.setattr("instagram_service.publishing.time.sleep", lambda seconds: None)

    responses.add(
        responses.GET,
        f"{base_url}/container1",
        json={"status_code": "IN_PROGRESS"},
        status=200,
    )

    with pytest.raises(MediaContainerError):
        publishing.wait_for_container_ready("container1", token, poll_interval=1, timeout=0)


@responses.activate
def test_publish_container_sends_creation_id(base_url, token):
    responses.add(
        responses.POST,
        f"{base_url}/{IG_USER_ID}/media_publish",
        json={"id": "media1"},
        status=200,
    )

    result = publishing.publish_container(IG_USER_ID, "container1", token)

    assert result["id"] == "media1"
    sent_params = responses.calls[0].request.params
    assert sent_params["creation_id"] == "container1"


@responses.activate
def test_publish_container_raises_quota_exceeded(base_url, token):
    responses.add(
        responses.POST,
        f"{base_url}/{IG_USER_ID}/media_publish",
        json={"error": {"message": "Publishing limit reached", "code": 9007}},
        status=400,
    )

    with pytest.raises(PublishingQuotaExceededError):
        publishing.publish_container(IG_USER_ID, "container1", token)


@responses.activate
def test_get_publishing_limit(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/{IG_USER_ID}/content_publishing_limit",
        json={"data": [{"config": {"quota_total": 50}, "quota_usage": 3}]},
        status=200,
    )

    result = publishing.get_publishing_limit(IG_USER_ID, token)

    assert result["data"][0]["quota_usage"] == 3
