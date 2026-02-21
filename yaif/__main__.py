#!/usr/bin/env python3
"""
YAIF Runner — entry point.
Usage:
  yaif <file.yaif>
  python -m yaif <file.yaif>

Execution order (when both are present):
  1. [config.bot]     — create roles, channels, server settings, emojis
  2. [config.webhook] — post message/embed once server is set up

If neither is present, falls back to terminal mode for preview/debugging.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from yaif.core import parse_yaif
from yaif.modules.discord import run_terminal, run_webhook, run_bot


def main():
    if len(sys.argv) < 2:
        print("Usage: yaif <file.yaif>")
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"✘ Error: File '{filepath}' not found.")
        sys.exit(1)

    config     = parse_yaif(text)
    config_cfg = config.get('config', {}) or {}

    has_bot     = isinstance(config_cfg.get('bot'),     dict) and bool(config_cfg['bot'])
    has_webhook = isinstance(config_cfg.get('webhook'), dict) and bool(config_cfg['webhook'])

    # No [config.bot] or [config.webhook] — fall back to terminal preview
    if not has_bot and not has_webhook:
        run_terminal(config)
        return

    # Bot always runs first (build the server), then webhook (announce it)
    if has_bot:
        run_bot(config)

    if has_webhook:
        run_webhook(config)


if __name__ == '__main__':
    main()