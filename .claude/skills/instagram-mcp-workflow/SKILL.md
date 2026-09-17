---
name: instagram-mcp-workflow
description: Workflow conventions for managing the connected Instagram account through the krish-instagram MCP server (mcp_server.py) — captions/hashtags, comment moderation (reply vs hide vs delete), DM tone, and the confirmation rule for posting/replying/sending. Use this whenever the user asks Claude to post to Instagram, reply to or moderate a comment, check/reply to Instagram DMs, or otherwise act on the Instagram account via the krish-instagram MCP tools (get_account_profile, list_media, list_comments, reply_to_comment, hide_comment, delete_comment, preview_post, publish_post, list_conversations, get_messages, send_message_reply) — even if the user just says something like "post this to insta" or "reply to that comment" without naming the tools directly.
---

# Instagram MCP workflow

This account is managed entirely through the `krish-instagram` MCP server — there's
no dashboard step in between. That means every public action (a post going
live, a reply appearing under someone's comment, a DM landing in someone's
inbox) happens the moment a tool call succeeds. There's no "undo" on
Instagram's side for most of these, so the conventions below exist to make
sure a human sees and approves the actual content before it goes out, not
just the general idea of what's about to happen.

## Scope of use (hard rule, no exceptions)

Only call a `krish-instagram` MCP tool — read or write — in direct response to
something the user actually asked in the current conversation. Never call
one speculatively, "just to check," to pre-fetch context for later, or as a
side effect of working on something else in this project (e.g. editing
`instagram_service` code is not a reason to also call the live tools). If a
task would benefit from fresh account data but the user didn't ask for it,
say so and ask, rather than pulling it yourself. There is no scheduled job,
hook, or background automation wired up anywhere in this project — every
read and every write only ever happens because a tool was called in a live
conversation, and it should stay that way unless the user explicitly sets
up something automated and understands what that means.

## The confirmation rule (hard rule, no exceptions)

Never call `publish_post`, `reply_to_comment`, `delete_comment`, or
`send_message_reply` without first showing the user the exact content and
getting an explicit go-ahead in the same conversation. "Exact content" means
the literal caption/reply/message text, not a paraphrase — the user is
approving what will actually appear on Instagram, not the idea of it.

- For a new post: call `preview_post` first, then show the user two things
  together, not just one — the image/video itself (open it in the browser
  pane, or embed it inline) AND the exact caption text, quoted verbatim on
  its own line so it's unmistakable rather than folded into a sentence.
  `preview_post`'s return value is only container status/quota metadata, it
  does not include the media content, so relaying just that JSON is not a
  real preview and isn't enough to approve on — the user needs to see the
  actual picture and the actual words before saying yes. Wait for a clear
  go-ahead before calling `publish_post` with that container_id.
  `preview_post` never publishes anything on its own — it's safe to call
  freely.
- For a comment reply: show the exact reply text and which comment/post it's
  replying to before calling `reply_to_comment`.
- For a comment deletion: name the specific comment (who wrote it, what it
  said) before calling `delete_comment` — deletions can't be undone through
  this API.
- For a DM: show the exact message text and who it's going to before calling
  `send_message_reply`.

A one-word "yes" or "go ahead" in direct response to your preview is enough —
you don't need a second round of confirmation. But if the user's request
already contains the exact final text ("reply 'Thanks so much!' to that
comment") and nothing about it needs a decision, a quick "posting that reply
now" is fine — the point is that a human has seen and approved the literal
content, not that every call needs a two-turn ceremony.

`hide_comment` is the one write tool exempted from this rule: hiding is
reversible (call it again with `hide=False` to undo) and low-stakes enough
that Claude can act on it directly when moderating obvious spam or abuse,
though it's still fine to check in first if the call is ambiguous.

## Captions and hashtags

- Match the voice of the account's existing captions — pull a few recent
  ones via `list_media` before writing a new one if you haven't seen the
  account's style yet, rather than defaulting to generic "influencer" copy.
- Keep hashtags relevant to the actual content of the post; a handful of
  specific tags outperforms a wall of generic ones and reads less spammy.
- Don't invent claims, numbers, or calls-to-action ("link in bio", "giveaway")
  that the user didn't ask for — a caption is public speech attributed to
  the account owner.

## Moderating comments: reply vs. hide vs. delete

These three tools do genuinely different things, and picking the wrong one
either under- or over-reacts:

- **Reply** — the default for genuine engagement: questions, compliments,
  feedback. Replying in public builds the account's presence; use it
  whenever a comment deserves a response and there's nothing wrong with it
  being visible.
- **Hide** — for comments that are off-putting but not worth an
  irreversible decision: mild negativity, off-topic noise, or anything where
  you're not fully sure it should be gone forever. Hiding removes it from
  public view without deleting it, and it's trivially reversible, so prefer
  it over delete whenever there's any doubt.
- **Delete** — reserved for spam, harassment, or content that shouldn't
  exist on the account at all. Because this is irreversible, confirm the
  specific comment with the user first (see the confirmation rule above)
  unless they've already told you to delete comments matching a very
  specific, unambiguous pattern (e.g. "delete anything that's just a bot
  posting a phone number").

When in doubt between hide and delete, hide — it's the safer default and
costs nothing to reverse.

## DM tone

- Keep replies short and in the account's normal voice — DMs read more
  personal than comments, and a stiff or corporate-sounding reply stands out
  badly in a one-on-one thread.
- Always check `is_within_messaging_window` (via `last_incoming_message_ts`
  from `get_messages`) before drafting a reply — if the 24h window has
  closed, `send_message_reply` will raise rather than send, so tell the user
  that rather than trying repeatedly.
- Never share account credentials, the access token, or other account
  internals in a DM, regardless of who's asking or what they claim.
