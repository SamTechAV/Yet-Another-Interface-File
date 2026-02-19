"""
YAIF Discord Webhook Sender

Sends generated YAIF output to a Discord webhook. Supports both:
  - Plain text mode: wraps the existing discord generator output in a message
  - Embed mode: builds rich Discord embeds from interface data

Config keys recognised in [config] block:
    webhook_url         Required. The Discord webhook URL to POST to.
    webhook_username    Optional. Override the bot's display name.
    webhook_avatar_url  Optional. Override the bot's avatar.
    embed_color         Optional. Hex colour for embed sidebar (e.g. #c84b31). Default: #5865F2 (Discord blurple).
    embed_mode          Optional. "true" to send as embeds instead of plain text. Default: false.

CLI usage:
    python -m yaif myfile.yaif -t discord --send
    python -m yaif myfile.yaif -t discord --send --webhook-url https://discord.com/api/webhooks/...

Per-interface embed annotations (on any field):
    @embed_color="#ff0000"    Override embed sidebar colour for this interface's embed
    @embed_thumbnail          Use the field's default value as a thumbnail URL
    @embed_image              Use the field's default value as the embed image URL
    @embed_url="https://..."  Make the embed title a hyperlink
    @embed_footer="text"      Custom footer text for this embed
    @embed_inline             Render this field as an inline embed field (side by side)
    @embed_timestamp          Use this field's default as the ISO 8601 timestamp shown in footer
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional

from .models import YAIFInterface, YAIFEnum, YAIFConfig


# ── Colour helper ────────────────────────────────────────────────────────────


def _hex_to_int(hex_str: str) -> int:
    """Convert '#RRGGBB' or 'RRGGBB' to a Discord colour integer."""
    h = hex_str.strip().lstrip("#")
    try:
        return int(h, 16)
    except ValueError:
        return 0x5865F2  # Discord blurple fallback


# ── Field helpers ────────────────────────────────────────────────────────────


def _label(f) -> str:
    return f.ann("label", "") or f.name


def _resolve_fields(iface: YAIFInterface, iface_map: dict) -> list:
    """Flatten inherited fields onto an interface."""
    parent_fields = []
    if iface.parent and iface.parent in iface_map:
        parent_fields = _resolve_fields(iface_map[iface.parent], iface_map)
    return parent_fields + list(iface.fields)


def _fmt_value(v) -> str:
    if v is None or v == "":
        return "-"
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "-"
    if isinstance(v, dict):
        return ", ".join(f"{k}: {val}" for k, val in v.items()) if v else "-"
    return str(v)


# ── Embed builder ────────────────────────────────────────────────────────────


def build_embed(iface: YAIFInterface, iface_map: dict, config: YAIFConfig) -> dict:
    """
    Build a single Discord embed dict for one YAIF interface.

    The embed title comes from @discord_title (or interface name).
    Each non-hidden field becomes an embed field (inline if @embed_inline).
    Special annotations (@embed_thumbnail, @embed_image, @embed_url,
    @embed_footer, @embed_color, @embed_timestamp) control embed metadata.
    """
    fields = _resolve_fields(iface, iface_map)

    # Pull interface-level display hints from the first annotated field
    title = iface.name
    icon = ""
    color_hex = config.get("embed_color", "#5865F2")
    thumbnail_url = None
    image_url = None
    embed_url = None
    footer_text = config.description or ""
    timestamp_val = None

    for f in iface.fields:
        if f.ann("discord_title"):
            title = f.ann("discord_title")
        if f.ann("discord_icon"):
            icon = f.ann("discord_icon")
        if f.ann("embed_color"):
            color_hex = f.ann("embed_color")
        if f.ann("embed_thumbnail") and f.default:
            thumbnail_url = f.default
        if f.ann("embed_image") and f.default:
            image_url = f.default
        if f.ann("embed_url"):
            embed_url = f.ann("embed_url")
        if f.ann("embed_footer"):
            footer_text = f.ann("embed_footer")
        if f.ann("embed_timestamp") and f.default:
            timestamp_val = f.default

    prefix = f"{icon} " if icon else ""
    embed: dict = {
        "title": f"{prefix}{title}",
        "color": _hex_to_int(color_hex),
        "fields": [],
    }

    if embed_url:
        embed["url"] = embed_url
    if config.description and not footer_text:
        footer_text = config.description
    if footer_text:
        embed["footer"] = {"text": footer_text}
    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}
    if image_url:
        embed["image"] = {"url": image_url}
    if timestamp_val:
        embed["timestamp"] = timestamp_val
    else:
        # Auto-add current UTC timestamp if not suppressed
        embed["timestamp"] = datetime.now(timezone.utc).isoformat()

    for f in fields:
        if f.ann("hidden"):
            continue
        # Skip fields that were only used as metadata carriers
        if any(
            f.ann(k)
            for k in (
                "embed_thumbnail",
                "embed_image",
                "embed_url",
                "embed_footer",
                "embed_timestamp",
            )
        ):
            if not f.default or f.ann("hidden"):
                continue

        name = _label(f)
        value = _fmt_value(f.default) if f.default else _fmt_value(None)
        inline = bool(f.ann("embed_inline", False))

        embed["fields"].append(
            {
                "name": name,
                "value": value or "-",
                "inline": inline,
            }
        )

    return embed


def build_embed_payload(
    interfaces: list[YAIFInterface],
    enums: list[YAIFEnum],
    config: YAIFConfig,
    username: str = None,
    avatar_url: str = None,
) -> dict:
    """Build a full webhook payload with one embed per interface."""
    iface_map = {i.name: i for i in interfaces}

    embeds = []
    for iface in interfaces:
        visible = [f for f in _resolve_fields(iface, iface_map) if not f.ann("hidden")]
        if not visible:
            continue
        embeds.append(build_embed(iface, iface_map, config))

    # Discord allows max 10 embeds per message - batch if needed
    payload = {"embeds": embeds[:10]}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url

    return payload


def build_text_payload(
    content: str,
    username: str = None,
    avatar_url: str = None,
) -> dict:
    """Build a plain-text webhook payload (wraps the discord generator output)."""
    # Discord messages max out at 2000 chars; trim gracefully if needed
    if len(content) > 2000:
        content = content[:1994] + "\n…"
    payload: dict = {"content": content}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url
    return payload


# ── HTTP sender ──────────────────────────────────────────────────────────────


class WebhookError(Exception):
    """Raised when a webhook POST fails."""


def send_webhook(
    webhook_url: str,
    payload: dict,
) -> None:
    """
    POST a JSON payload to a Discord webhook URL.
    Raises WebhookError on HTTP errors or network failures.
    """
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "yaif-webhook/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            # 204 No Content is the normal Discord success response
            if resp.status not in (200, 204):
                raise WebhookError(
                    f"Unexpected HTTP {resp.status} from Discord webhook"
                )
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise WebhookError(f"HTTP {e.code} from Discord webhook: {body}") from e
    except urllib.error.URLError as e:
        raise WebhookError(
            f"Network error sending to Discord webhook: {e.reason}"
        ) from e


# ── High-level send function ─────────────────────────────────────────────────


def send(
    interfaces: list[YAIFInterface],
    enums: list[YAIFEnum],
    config: YAIFConfig,
    webhook_url: str = None,
    embed_mode: bool = None,
    username: str = None,
    avatar_url: str = None,
    plain_text_content: str = None,
) -> None:
    """
    Send parsed YAIF data to a Discord webhook.

    Args:
        interfaces:          Parsed interface list.
        enums:               Parsed enum list.
        config:              Parsed config block.
        webhook_url:         Webhook URL. Falls back to config key 'webhook_url'.
        embed_mode:          True → rich embeds, False → plain text. Falls back
                             to config key 'embed_mode'. Default: False.
        username:            Override display name. Falls back to config key
                             'webhook_username', then config.title.
        avatar_url:          Override avatar URL. Falls back to config key
                             'webhook_avatar_url'.
        plain_text_content:  Pre-rendered text (from DiscordGenerator). Required
                             when embed_mode is False.
    """
    url = webhook_url or config.get("webhook_url")
    if not url:
        raise WebhookError(
            "No webhook URL provided. Pass --webhook-url or set 'webhook_url' in [config]."
        )

    if embed_mode is None:
        embed_mode = config.get_bool("embed_mode", False)

    display_name = username or config.get("webhook_username") or config.title or None
    avatar = avatar_url or config.get("webhook_avatar_url") or None

    if embed_mode:
        payload = build_embed_payload(interfaces, enums, config, display_name, avatar)
        if not payload.get("embeds"):
            raise WebhookError("No embeds were generated - nothing to send.")
        # If there are more than 10 interfaces, we need multiple requests
        iface_map = {i.name: i for i in interfaces}
        all_embeds = [
            build_embed(i, iface_map, config)
            for i in interfaces
            if any(not f.ann("hidden") for f in _resolve_fields(i, iface_map))
        ]
        batches = [all_embeds[i : i + 10] for i in range(0, len(all_embeds), 10)]
        for batch in batches:
            batch_payload: dict = {"embeds": batch}
            if display_name:
                batch_payload["username"] = display_name
            if avatar:
                batch_payload["avatar_url"] = avatar
            send_webhook(url, batch_payload)
    else:
        if not plain_text_content:
            raise WebhookError(
                "plain_text_content is required when embed_mode is False."
            )
        # Split into 2000-char chunks on newlines
        chunks = _split_message(plain_text_content, limit=2000)
        for chunk in chunks:
            send_webhook(url, build_text_payload(chunk, display_name, avatar))


def _split_message(text: str, limit: int = 2000) -> list[str]:
    """Split a long message into chunks that fit within Discord's limit."""
    if len(text) <= limit:
        return [text]

    chunks = []
    current = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        if current_len + len(line) > limit and current:
            chunks.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("".join(current))

    return chunks
