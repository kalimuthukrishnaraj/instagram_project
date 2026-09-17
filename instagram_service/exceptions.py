class GraphAPIError(Exception):
    """Base exception for all Graph API errors."""

    def __init__(self, message, code=None, error_subcode=None, fbtrace_id=None, raw=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_subcode = error_subcode
        self.fbtrace_id = fbtrace_id
        self.raw = raw or {}

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(message={self.message!r}, "
            f"code={self.code}, error_subcode={self.error_subcode})"
        )


class TokenExpiredError(GraphAPIError):
    """Access token is invalid or has expired (code 190)."""


class RateLimitError(GraphAPIError):
    """App or user hit a rate limit (code 4, 17, 32, or 613)."""


class PermissionError_(GraphAPIError):
    """Missing scope/permission for this call (code 10 or 200-series)."""


class MediaContainerError(GraphAPIError):
    """A media container failed to finish processing, or never finished in time."""


class PublishingQuotaExceededError(GraphAPIError):
    """Rolling 24h content-publishing limit reached (code 9007)."""


class MessagingWindowExpiredError(Exception):
    """The 24h standard-messaging window for this recipient has closed."""


def parse_graph_error(response_json, http_status=None):
    """
    Turn a Graph API error JSON body into the right exception type.
    Graph API errors look like:
    {"error": {"message": "...", "type": "...", "code": 190,
               "error_subcode": 463, "fbtrace_id": "..."}}
    """
    err = response_json.get("error", {})
    message = err.get("message", "Unknown Graph API error")
    code = err.get("code")
    subcode = err.get("error_subcode")
    fbtrace_id = err.get("fbtrace_id")

    if code == 190:
        return TokenExpiredError(message, code, subcode, fbtrace_id, raw=err)
    if code in (4, 17, 32, 613):
        return RateLimitError(message, code, subcode, fbtrace_id, raw=err)
    if code == 9007:
        return PublishingQuotaExceededError(message, code, subcode, fbtrace_id, raw=err)
    if code == 10 or (code is not None and 200 <= code < 300):
        return PermissionError_(message, code, subcode, fbtrace_id, raw=err)
    return GraphAPIError(message, code, subcode, fbtrace_id, raw=err)
