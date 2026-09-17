# Krish Instagram MCP

A local Python service and MCP (Model Context Protocol) server that let
Claude manage an Instagram Business/Creator account conversationally — read
media/comments/insights, publish posts, moderate comments, and read/send
direct messages — via the Instagram Graph API.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how it's built internally, and
[INSTAGRAM_MCP_GUIDE.md](INSTAGRAM_MCP_GUIDE.md) for day-to-day usage
(what the tools do, how to turn the server on/off, and the confirmation
rules Claude follows before posting/replying/sending anything).

## What's included

- **`instagram_service/`** — a Python package wrapping the Graph API: auth
  (token exchange/refresh), media, comments (read/reply/moderate),
  insights, publishing (containers + publish), and direct messages.
- **`mcp_server.py`** — the MCP server (registered as `krish-instagram`)
  that exposes `instagram_service` as 12 tools for a Claude agent.
- **`tests/`** — a pytest suite that mocks the Graph API and the MCP tool
  layer, so it runs with no real token or network access.

This project has no dashboard or web UI — the account is managed entirely
through a Claude session talking to the MCP server.

## Requirements

- Python 3.10+
- An Instagram Business or Creator account, connected via a Meta developer
  app (Business Login for Instagram)
- A long-lived Instagram access token and your numeric Instagram User ID
- Claude Code CLI (the MCP server currently only works there — see
  [INSTAGRAM_MCP_GUIDE.md](INSTAGRAM_MCP_GUIDE.md#where-it-works-today))

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create your credentials file:
   ```bash
   cd instagram_service
   cp .env.example .env
   ```
   Then edit `.env` and fill in your real `IG_ACCESS_TOKEN` and
   `IG_USER_ID`. This file is git-ignored — never commit it.

   If you're not sure how to get a token or account ID, or you hit a
   "Cannot parse access token" error, run:
   ```bash
   python3 instagram_service/diagnose_env.py
   ```
   from inside `instagram_service/` to check what's actually being loaded
   (it never prints your actual secret values).

3. Register the MCP server: this project's `.mcp.json` already points at
   `mcp_server.py`. Run `claude` from this project's root, approve the
   `krish-instagram` server when prompted, and the tools are available in
   that session. Full details in
   [INSTAGRAM_MCP_GUIDE.md](INSTAGRAM_MCP_GUIDE.md).

## Testing

```bash
python3 -m pytest tests/ -v
```

All tests mock the Graph API's HTTP layer and the MCP tool-calling layer,
so this runs without a real token or internet access. Run this from the
project root (not from inside `tests/`), and use `python3 -m pytest`
rather than a bare `pytest` command so the `instagram_service` package
resolves correctly.

To test against your *real* account (read-only, safe operations only):
```bash
python3 instagram_service/smoke_test.py
```

## Notes

- Write operations (publishing, replying, moderating comments, sending
  DMs) are exposed as MCP tools with a hard confirmation rule enforced by
  the companion skill ([.claude/skills/instagram-mcp-workflow/SKILL.md](.claude/skills/instagram-mcp-workflow/SKILL.md)) —
  Claude always shows the exact content and gets explicit go-ahead before
  anything goes out.
- Long-lived tokens expire after ~60 days and need refreshing via
  `instagram_service/auth.py`'s `refresh_long_lived_token` — there's no UI
  for this anymore, it's a manual/scriptable step.
