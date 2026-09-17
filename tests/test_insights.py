import responses

from instagram_service import insights


@responses.activate
def test_get_media_insights_dict_flattens_values(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/17900000000000000/insights",
        json={
            "data": [
                {"name": "reach", "values": [{"value": 150}]},
                {"name": "likes", "values": [{"value": 12}]},
            ]
        },
        status=200,
    )

    result = insights.get_media_insights_dict("17900000000000000", token)

    assert result == {"reach": 150, "likes": 12}


@responses.activate
def test_get_media_insights_dict_handles_missing_values(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/17900000000000000/insights",
        json={"data": [{"name": "saved", "values": []}]},
        status=200,
    )

    result = insights.get_media_insights_dict("17900000000000000", token)

    assert result == {"saved": None}


@responses.activate
def test_get_account_insights_passes_period_and_range(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/17841400000000000/insights",
        json={"data": []},
        status=200,
    )

    insights.get_account_insights(
        "17841400000000000", token, period="week", since="2026-08-01", until="2026-09-01"
    )

    sent_params = responses.calls[0].request.params
    assert sent_params["period"] == "week"
    assert sent_params["since"] == "2026-08-01"
    assert sent_params["until"] == "2026-09-01"


@responses.activate
def test_get_follower_count(base_url, token):
    responses.add(
        responses.GET,
        f"{base_url}/17841400000000000",
        json={"followers_count": 4200, "media_count": 87},
        status=200,
    )

    result = insights.get_follower_count("17841400000000000", token)

    assert result["followers_count"] == 4200
