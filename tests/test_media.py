import responses

from instagram_service import media


@responses.activate
def test_get_media_returns_one_page(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/17841400000000000/media",
        json={"data": [{"id": "1"}, {"id": "2"}]},
        status=200,
    )

    result = media.get_media("17841400000000000", token)

    assert len(result["data"]) == 2


@responses.activate
def test_get_all_media_flattens_pagination(base_url, token):
    next_url = f"{base_url}/17841400000000000/media?after=CURSOR"

    responses.add(
        responses.GET,
        f"{base_url}/17841400000000000/media",
        json={"data": [{"id": "1"}], "paging": {"next": next_url}},
        status=200,
    )
    responses.add(
        responses.GET,
        next_url,
        json={"data": [{"id": "2"}]},
        status=200,
    )

    items = media.get_all_media("17841400000000000", token)

    assert [item["id"] for item in items] == ["1", "2"]


@responses.activate
def test_get_media_details(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/17900000000000000",
        json={"id": "17900000000000000", "caption": "a caption"},
        status=200,
    )

    result = media.get_media_details("17900000000000000", token)

    assert result["caption"] == "a caption"
