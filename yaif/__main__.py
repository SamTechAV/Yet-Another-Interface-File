#!/usr/bin/env python3
"""
YAIF Runner — entry point.

Usage:
  yaif <file.yaif>
  python -m yaif <file.yaif>

The file itself determines what runs — no flags needed.

  Has [theme] / [page]     → HTML generator  (writes <filename>.html)
  Has [config.bot]         → Discord bot     (create roles, channels, etc.)
  Has [config.webhook]     → Discord webhook (post message/embed)
  Neither                  → Terminal preview / debug
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from yaif.core import parse_yaif
from yaif.modules.discord import run_terminal, run_webhook, run_bot


def _is_html_file(text: str) -> bool:
    """Return True if the file contains [theme] or any [page ...] block."""
    import re
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in ('[theme]', '[Theme]'):
            return True
        if re.fullmatch(r'\[page\s+\S+\]', stripped, re.I):
            return True
    return False


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

    # ── HTML generator ────────────────────────────────────────────────────
    if _is_html_file(text):
        from yaif.modules.html import generate

        out_path = filepath.rsplit('.', 1)[0] + '.html'
        html = generate(text)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f'✔  HTML written → {out_path}')
        return

    # ── Discord ───────────────────────────────────────────────────────────
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