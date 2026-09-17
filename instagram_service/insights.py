from .client import call_graph_api

# Metric availability depends on media_type (IMAGE / VIDEO / CAROUSEL_ALBUM / REELS)
# and can change between API versions — check Meta's docs for your pinned version
# if you get an "Invalid metric" error for a given media type.
DEFAULT_MEDIA_METRICS = "reach,likes,comments,saved,shares"
DEFAULT_ACCOUNT_METRICS = "reach,accounts_engaged,total_interactions"


def get_media_insights(media_id, access_token, metrics=DEFAULT_MEDIA_METRICS):
    """
    Fetch insights (analytics) for a single media object.
    Returns dict with a "data" list of {"name": metric, "values": [...]}.
    """
    return call_graph_api(
        f"{media_id}/insights",
        access_token,
        params={"metric": metrics},
    )


def get_media_insights_dict(media_id, access_token, metrics=DEFAULT_MEDIA_METRICS):
    """
    Same as get_media_insights, but flattens the response into a simple
    {metric_name: value} dict for easier consumption.
    """
    raw = get_media_insights(media_id, access_token, metrics)
    result = {}
    for item in raw.get("data", []):
        name = item.get("name")
        values = item.get("values", [])
        result[name] = values[0].get("value") if values else None
    return result


def get_account_insights(
    ig_user_id,
    access_token,
    metrics=DEFAULT_ACCOUNT_METRICS,
    period="day",
    since=None,
    until=None,
):
    """
    Fetch account-level insights over a time range.
    period: "day" | "week" | "days_28"
    since/until: Unix timestamps or YYYY-MM-DD strings (optional; defaults to
    the API's own lookback window if omitted).
    """
    params = {"metric": metrics, "period": period}
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    return call_graph_api(f"{ig_user_id}/insights", access_token, params=params)


def get_audience_demographics(
    ig_user_id,
    access_token,
    breakdown="city",
    timeframe="lifetime",
):
    """
    Fetch follower demographic breakdown (e.g. by city, country, age, gender).
    breakdown: "city" | "country" | "age" | "gender"
    Requires a sufficient follower count (Meta enforces a minimum audience
    size before demographic data is returned).
    """
    return call_graph_api(
        f"{ig_user_id}/insights",
        access_token,
        params={
            "metric": "follower_demographics",
            "period": "lifetime",
            "metric_type": "total_value",
            "breakdown": breakdown,
            "timeframe": timeframe,
        },
    )


def get_follower_count(ig_user_id, access_token):
    """
    Current follower count is a field on the account object, not an insights
    metric — fetched separately here for convenience.
    """
    return call_graph_api(
        ig_user_id,
        access_token,
        params={"fields": "followers_count,media_count"},
    )
