"""
webhook.py — YAIF webhook output mode.
Builds and POSTs Discord messages/embeds to a webhook URL.
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

from yaif.core import (
    DISCORD_MESSAGE_LIMIT,
    DISCORD_MAX_EMBEDS,
    DISCORD_EMBED_TITLE_LIMIT,
    DISCORD_FOOTER_LIMIT,
    truncate,
    hex_to_int,
)


# ─── Webhook Limitation Checker ───────────────────────────────────────────────

WEBHOOK_UNSUPPORTED_SECTIONS = {
    'roles':      'Creating/managing roles requires a bot with Manage Roles permission.',
    'categories': 'Creating channels and categories requires a bot with Manage Channels permission.',
    'emojis':     'Adding custom emojis requires a bot with Manage Expressions permission.',
    'system':     'Changing system/server settings requires a bot with Manage Guild permission.',
    'server':     '[server] settings cannot be applied via webhook. Use [message] and [message.embed] instead.',
}

def check_webhook_limitations(config):
    warnings = []
    for section, reason in WEBHOOK_UNSUPPORTED_SECTIONS.items():
        value = config.get(section)
        if value and value != {} and value != []:
            warnings.append((section, reason))

    if warnings:
        print()
        print("⚠️  WEBHOOK LIMITATION WARNING")
        print("─" * 60)
        print("  Webhooks can only POST messages — they cannot create,")
        print("  modify, or delete Discord server structures.")
        print()
        print("  The following sections in your config will be IGNORED:")
        print()
        for section, reason in warnings:
            print(f"  ✘ [{section}]")
            print(f"      {reason}")
        print()
        print("  To use these features you need a Discord Bot Token.")
        print("  Set [output] mode: bot")
        print("─" * 60)
        print()


# ─── Embed Builder ────────────────────────────────────────────────────────────

def build_embed(embed_cfg):
    """
    Turn a [message.embed] config dict into a Discord API embed object.
    Enforces Discord field length limits. All fields are optional.
    """
    embed = {}

    if embed_cfg.get('title'):
        embed['title'] = truncate(str(embed_cfg['title']), DISCORD_EMBED_TITLE_LIMIT)

    if embed_cfg.get('description'):
        embed['description'] = embed_cfg['description']

    # Color: accept integer directly, or a hex string like #5865F2 or 0x5865F2
    color = embed_cfg.get('color')
    if color is not None:
        embed['color'] = color if isinstance(color, int) else hex_to_int(color)

    if embed_cfg.get('url'):
        embed['url'] = embed_cfg['url']

    if embed_cfg.get('image'):
        embed['image'] = {'url': embed_cfg['image']}

    if embed_cfg.get('thumbnail'):
        embed['thumbnail'] = {'url': embed_cfg['thumbnail']}

    # Footer
    footer_text = embed_cfg.get('footer')
    if footer_text:
        embed['footer'] = {'text': truncate(str(footer_text), DISCORD_FOOTER_LIMIT)}
        if embed_cfg.get('footer_icon'):
            embed['footer']['icon_url'] = embed_cfg['footer_icon']

    # Author
    if embed_cfg.get('author'):
        embed['author'] = {'name': embed_cfg['author']}
        if embed_cfg.get('author_url'):
            embed['author']['url'] = embed_cfg['author_url']
        if embed_cfg.get('author_icon'):
            embed['author']['icon_url'] = embed_cfg['author_icon']

    # Timestamp: auto UTC unless suppressed with timestamp: false
    ts = embed_cfg.get('timestamp', True)
    if ts is False:
        pass  # suppressed
    elif ts is True or ts is None:
        embed['timestamp'] = datetime.now(timezone.utc).isoformat()
    else:
        embed['timestamp'] = str(ts)  # user-supplied ISO 8601 string

    return embed


# ─── Message Splitter ─────────────────────────────────────────────────────────

def split_message(text, limit=DISCORD_MESSAGE_LIMIT):
    """Split a long string into chunks that each fit within Discord's limit."""
    if len(text) <= limit:
        return [text]

    chunks = []
    current = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        if current_len + len(line) > limit and current:
            chunks.append(''.join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append(''.join(current))

    return chunks


# ─── Webhook Error ────────────────────────────────────────────────────────────

class WebhookError(Exception):
    pass


# ─── HTTP Sender ──────────────────────────────────────────────────────────────

def send_webhook(url, payload):
    """
    POST a JSON payload to a Discord webhook.
    Raises WebhookError on failure.
    Discord returns 204 No Content on success — both 200 and 204 are accepted.
    """
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, data=data,
        headers={'Content-Type': 'application/json', 'User-Agent': 'YAIF/1.0'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 204):
                raise WebhookError(f"Unexpected HTTP {resp.status} from Discord")
            return resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise WebhookError(f"HTTP {e.code} — {e.reason}\n  Discord says: {body}") from e
    except urllib.error.URLError as e:
        raise WebhookError(f"Network error: {e.reason}") from e


# ─── Webhook Runner ───────────────────────────────────────────────────────────

def run_webhook(config):
    config_cfg = config.get('config', {}) or {}
    has_bot = isinstance(config_cfg.get('bot'), dict) and bool(config_cfg['bot'])

    if not has_bot:
        check_webhook_limitations(config)

    webhook_cfg = config.get('config', {}).get('webhook', {})
    if not isinstance(webhook_cfg, dict):
        webhook_cfg = {}

    url = webhook_cfg.get('url', '')
    if not url or 'YOUR_WEBHOOK' in str(url):
        print("✘ Error: No valid webhook URL found in [config.webhook] url")
        print("  Replace YOUR_WEBHOOK_URL_HERE with your actual Discord webhook URL.")
        sys.exit(1)

    message_cfg = config.get('message', {})
    if not isinstance(message_cfg, dict):
        message_cfg = {}

    embed_cfg = message_cfg.get('embed', {})
    if not isinstance(embed_cfg, dict):
        embed_cfg = {}

    content   = message_cfg.get('content')
    has_embed = any(embed_cfg.get(k) for k in ('title', 'description', 'image', 'thumbnail'))

    if not content and not has_embed:
        print("✘ Error: Nothing to send.")
        print("  Add [message] content: and/or a [message.embed] section to your config.")
        sys.exit(1)

    # Identity overrides applied to every payload
    base_payload = {}
    if webhook_cfg.get('username'):
        base_payload['username'] = webhook_cfg['username']
    if webhook_cfg.get('avatar_url'):
        base_payload['avatar_url'] = webhook_cfg['avatar_url']

    try:
        # ── Plain text — chunked if over 2000 chars ──
        if content:
            chunks = split_message(str(content))
            for i, chunk in enumerate(chunks):
                payload = {**base_payload, 'content': chunk}
                status = send_webhook(url, payload)
                label = f" ({i+1}/{len(chunks)})" if len(chunks) > 1 else ""
                print(f"✔ Message{label} sent (HTTP {status})")

        # ── Embed — batched if over 10 embeds ──
        if has_embed:
            embed   = build_embed(embed_cfg)
            embeds  = [embed]
            batches = [embeds[i:i + DISCORD_MAX_EMBEDS] for i in range(0, len(embeds), DISCORD_MAX_EMBEDS)]
            for i, batch in enumerate(batches):
                payload = {**base_payload, 'embeds': batch}
                status = send_webhook(url, payload)
                label = f" batch {i+1}/{len(batches)}" if len(batches) > 1 else ""
                print(f"✔ Embed{label} sent (HTTP {status})")

    except WebhookError as e:
        print(f"✘ Webhook error: {e}")
        sys.exit(1)