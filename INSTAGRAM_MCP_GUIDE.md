# Krish Instagram MCP — User Guide

This is the practical "how do I actually use this" guide. For the original
build plan and phase history, see
[MCP_Integration_Plan.md](MCP_Integration_Plan.md); for how the codebase is
put together, see [ARCHITECTURE.md](ARCHITECTURE.md). This doc is about
day-to-day use.

## What this is

Your Instagram Business/Creator account is managed conversationally through
a local **MCP (Model Context Protocol) server** named **`krish-instagram`**
(`mcp_server.py`) that wraps the `instagram_service` Python package. When
you talk to Claude in a session inside this project, Claude can call that
server's tools to read your account data and, when you approve it,
post/reply/send on your behalf.

There's no dashboard step in between and no separate app to open — it's
just this project's Claude session, talking to your real Instagram account
through Meta's Graph API.

## Where it works today

**Claude Code CLI only.** Run `claude` from this project's folder
(`C:\krish\Claude\Meta Graph API\instagram_project`) and the `krish-instagram`
server loads automatically via this project's `.mcp.json`.

This desktop app's Connectors UI (Settings → Connectors → Add custom
connector) does **not** support it — that UI only accepts a remote HTTPS
MCP server URL, and this server runs locally on your machine. There's no
current plan to change that (it would mean exposing a server that can post/
DM/delete on a real account to the public internet, which isn't worth the
convenience).

## Turning it on/off

- **First time in a project session:** Claude Code will ask you to trust
  the server — approve it once.
- **Check it's connected:** run `claude mcp list` from a terminal, or type
  `/mcp` inside a session.
- **Turn it off for just this session:** `/mcp` → select `krish-instagram` →
  disable for this session.
- **Turn it off persistently:** edit `.claude/settings.local.json` — set
  `"enabledMcpjsonServers": []` or add `"disabledMcpjsonServers": ["krish-instagram"]`.
  `.mcp.json` itself is untouched, so turning it back on later is just
  re-enabling it, not reconfiguring anything.

**Important:** the server only ever does something when a tool is actually
called in a live conversation — there's no scheduled job, hook, or
background automation wired up anywhere in this project. It doesn't read or
send anything unless you ask for it in that session.

## What you can ask it to do

You don't need to name tools — plain requests work ("what's my follower
count", "show me comments on my last post", "reply to that comment",
"post this to insta"). Under the hood, these are the 12 tools available:

**Reading your account**
| Tool | What it does |
|---|---|
| `get_account_profile` | Current follower count and media count |
| `list_media` | Your recent posts (caption, type, likes, comments, permalink) |
| `get_media_insights` | Reach/likes/comments/saved/shares for one post |

**Comments**
| Tool | What it does |
|---|---|
| `list_comments` | Top-level comments on a post, with commenter usernames |
| `reply_to_comment` | Post a public reply to a comment |
| `hide_comment` | Hide/unhide a comment without deleting it (reversible) |
| `delete_comment` | Permanently delete a comment (irreversible) |

**Publishing**
| Tool | What it does |
|---|---|
| `preview_post` | Builds a media container and reports its status/quota — nothing goes live |
| `publish_post` | Publishes a container built by `preview_post` — goes live immediately |

**Direct messages**
| Tool | What it does |
|---|---|
| `list_conversations` | Your DM conversations |
| `get_messages` | Messages within one conversation |
| `send_message_reply` | Send a DM reply (checks the 24h messaging window first) |

## What the companion skill does

Alongside the tools, this project has a skill —
[.claude/skills/instagram-mcp-workflow/SKILL.md](.claude/skills/instagram-mcp-workflow/SKILL.md)
— that Claude automatically loads whenever a request touches these tools.
It's the ruleset that governs *how* the tools get used, not what they do.
Four things it enforces:

1. **Scope of use** — tools only get called in direct response to something
   you actually asked in that conversation. No proactive checks, no
   pre-fetching "just in case."
2. **The confirmation rule** — before `publish_post`, `reply_to_comment`,
   `delete_comment`, or `send_message_reply` are called, you get shown the
   *exact* content first: for a post, the actual image/video (not just a
   link) plus the caption quoted verbatim; for a reply or DM, the literal
   text; for a deletion, which specific comment. Nothing goes out until you
   say yes. `preview_post` and `hide_comment` are the two exceptions —
   preview never publishes anything, and hiding is trivially reversible.
3. **Caption/comment/DM conventions** — match your account's existing
   voice, prefer hiding over deleting when in doubt, keep DMs short and
   personal, and always check the 24h messaging window before a DM reply.
4. It's checked into the repo (not personal memory), so it applies the same
   way in any session working in this project.

## Posting an image: what actually works

`publish_post`/`preview_post` need a **public HTTPS URL** that Meta's
servers can fetch directly — not a file on your computer, and not just any
share link:

- **Imgur works reliably** — upload the image, then use the direct link
  (`https://i.imgur.com/HASH.jpeg`, found by opening the image itself, not
  the album page).
- **Google Drive does not work reliably** — even a corrected direct-image
  URL from Drive gets rejected by Meta's fetcher in practice (Google's CDN
  appears to treat Meta's servers differently). Don't spend time on Drive
  URL formats — go straight to Imgur or another host.
- A local file needs to be uploaded somewhere public first — there's no way
  around this, it's a Graph API requirement, not a limitation of this
  project's code.

## Other things worth knowing

- **Publishing quota**: Meta caps posts to a rolling 24h window (~100 in
  this account's case, but check live via the quota Claude shows in a
  preview rather than assuming a fixed number).
- **DM window**: you can only send a free-form DM reply within 24h of the
  other person's last message to you — `send_message_reply` checks this
  and refuses rather than letting Meta reject it silently.
- **Token expiry**: the long-lived access token in `instagram_service/.env`
  expires roughly every 60 days and needs refreshing (see `auth.py` /
  `README.md`) — Claude can't do this on its own, since it requires your
  Meta app credentials.
- **Comment usernames**: Graph API's plain `username` field is only
  reliably populated for your own comments; the code was fixed to also
  request the `from` field so other commenters' usernames show up too.

## If something looks wrong

- Tools missing or erroring in a session → run `/mcp` and check the
  `krish-instagram` server's status; reconnect if needed. Note: if you've just
  edited `instagram_service/*.py`, the running server won't see the change
  until it's reconnected or the session is restarted — it's a long-lived
  process, not re-read on every call.
- A publish/reply/send didn't happen even though you expected it → that's
  the confirmation rule working as intended; it only fires after an
  explicit yes.
