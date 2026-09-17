"""
Manual smoke test against the REAL Instagram Graph API.

This is NOT part of the automated test suite (pytest won't pick it up) —
it's for you to sanity-check that your token/permissions/account ID are
actually wired up correctly. Only calls read-only endpoints; nothing here
posts, replies, deletes, or hides anything.

Usage (either works):
    1) Create a .env file next to this script (see .env.example) containing:
           IG_ACCESS_TOKEN=your-long-lived-token
           IG_USER_ID=your-instagram-business-account-id
       then just run:
           python3 smoke_test.py

    2) Or skip the .env file and export the vars yourself before running:
           export IG_ACCESS_TOKEN="your-long-lived-token"
           export IG_USER_ID="your-instagram-business-account-id"
           python3 smoke_test.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    # Looks for a .env file in the current working directory (and parent
    # directories). Silently does nothing if no .env file is found, so this
    # is safe to leave in even if you're using real exported env vars instead.
    load_dotenv()
except ImportError:
    print("(python-dotenv not installed — skipping .env loading, "
          "run: pip install python-dotenv)")

from instagram_service import media, comments, insights
from instagram_service.exceptions import GraphAPIError


def main():
    token = os.environ.get("IG_ACCESS_TOKEN")
    ig_user_id = os.environ.get("IG_USER_ID")

    if not token or not ig_user_id:
        print("Set IG_ACCESS_TOKEN and IG_USER_ID environment variables first.")
        sys.exit(1)

    try:
        print("\n--- Follower count ---")
        account = insights.get_follower_count(ig_user_id, token)
        print(account)

        print("\n--- Recent media (first page) ---")
        media_page = media.get_media(ig_user_id, token, limit=3)
        items = media_page.get("data", [])
        print(f"Fetched {len(items)} media items")
        for item in items:
            print(f"  - {item.get('id')}: {item.get('caption', '')[:40]!r}")

        if items:
            first_media_id = items[0]["id"]

            print(f"\n--- Media details for {first_media_id} ---")
            details = media.get_media_details(first_media_id, token)
            print(details)

            print(f"\n--- Comments on {first_media_id} ---")
            comment_page = comments.get_comments(first_media_id, token, limit=3)
            print(f"Fetched {len(comment_page.get('data', []))} comments")

            print(f"\n--- Insights for {first_media_id} ---")
            try:
                media_insights = insights.get_media_insights_dict(first_media_id, token)
                print(media_insights)
            except GraphAPIError as e:
                # Common if the metrics don't apply to this media_type
                print(f"Insights call failed (may be expected for this media type): {e}")
        else:
            print("\nNo media found on this account — skipping media-detail checks.")

        print("\nAll smoke test calls completed without raising.")

    except GraphAPIError as e:
        print(f"\nGraph API error: {e!r}")
        print("Check: token validity/expiry, granted scopes, and that IG_USER_ID is correct.")
        sys.exit(1)


if __name__ == "__main__":
    main()
