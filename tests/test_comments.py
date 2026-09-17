import responses

from instagram_service import comments


@responses.activate
def test_get_comments(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/17900000000000000/comments",
        json={"data": [{"id": "c1", "text": "nice pic"}]},
        status=200,
    )

    result = comments.get_comments("17900000000000000", token)

    assert result["data"][0]["text"] == "nice pic"


@responses.activate
def test_reply_to_comment_sends_message_param(base_url, token):
    responses.add(
        responses.POST,
        f"{base_url}/c1/replies",
        json={"id": "c2"},
        status=200,
    )

    result = comments.reply_to_comment("c1", "Thanks!", token)

    assert result["id"] == "c2"
    sent_params = responses.calls[0].request.params
    assert sent_params["message"] == "Thanks!"


@responses.activate
def test_delete_comment(base_url, token):
    responses.add(
        responses.DELETE,
        f"{base_url}/c1",
        json={"success": True},
        status=200,
    )

    result = comments.delete_comment("c1", token)

    assert result["success"] is True


@responses.activate
def test_set_comment_visibility_hide(base_url, token):
    responses.add(
        responses.POST,
        f"{base_url}/c1",
        json={"success": True},
        status=200,
    )

    result = comments.set_comment_visibility("c1", token, hide=True)

    assert result["success"] is True
    sent_params = responses.calls[0].request.params
    assert sent_params["hide"] == "true"
