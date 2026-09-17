import os

# Pin the API version explicitly. Bump this one line when you upgrade.
GRAPH_API_VERSION = "v21.0"

# Which host to call depends on how your token was issued:
# - Tokens starting with "IGAA" come from Business Login for Instagram
#   (Instagram Login) -> use graph.instagram.com
# - Tokens starting with "EAA" come from Facebook Login for Business
#   -> use graph.facebook.com
# If you ever switch login flows, change this one line.
GRAPH_API_HOST = "https://graph.instagram.com"
GRAPH_API_BASE_URL = f"{GRAPH_API_HOST}/{GRAPH_API_VERSION}"

# App credentials (needed for long-lived token exchange/refresh).
# For Instagram Login, only the app secret is required — there's no
# client_id/app_id param in that flow's exchange/refresh calls.
APP_ID = os.environ.get("FB_APP_ID")          # only used if you switch to Facebook Login
APP_SECRET = os.environ.get("FB_APP_SECRET")  # required for token exchange either way

# Request behavior
DEFAULT_TIMEOUT = 15          # seconds
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2       # exponential: 2, 4, 8...
