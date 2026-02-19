"""
CLI entry point — run with: python -m yaif
"""

import sys
import io
import argparse
from pathlib import Path

# Force UTF-8 output on Windows (charmap can't handle box-drawing chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf_8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf_8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from .parser import YAIFParser, YAIFParseError
from .generators import GENERATORS, FILE_EXTENSIONS
from .watcher import watch


def main():
    parser = argparse.ArgumentParser(
        description='YAIF - Yet Another Interface File processor',
        epilog=(
            'Examples:\n'
            '  python -m yaif example.yaif --target html -o out.html\n'
            '  python -m yaif release.yaif -t discord --send\n'
            '  python -m yaif release.yaif -t discord --send --embed\n'
            '  python -m yaif release.yaif -t discord --send --webhook-url https://discord.com/api/webhooks/...\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('file', help='Path to a .yaif file')
    parser.add_argument(
        '--target', '-t',
        choices=list(GENERATORS.keys()),
        default='python',
        help='Output target language (default: python)',
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: print to stdout)',
    )
    parser.add_argument(
        '--validate-only', '-v',
        action='store_true',
        help="Only validate the .yaif file, don't generate code",
    )
    parser.add_argument(
        '--watch', '-w',
        action='store_true',
        help='Watch the file for changes and regenerate automatically',
    )

    # ── Webhook flags ──────────────────────────────────────────────────────────
    webhook_group = parser.add_argument_group(
        'Discord webhook',
        'Send output directly to a Discord channel via webhook.',
    )
    webhook_group.add_argument(
        '--send',
        action='store_true',
        help=(
            'Send generated output to a Discord webhook. '
            'The webhook URL must be set via --webhook-url or the webhook_url key in [config].'
        ),
    )
    webhook_group.add_argument(
        '--webhook-url',
        metavar='URL',
        help='Discord webhook URL. Overrides the webhook_url key in [config].',
    )
    webhook_group.add_argument(
        '--embed',
        action='store_true',
        default=None,
        help=(
            'Send as Discord rich embeds instead of plain text. '
            'Overrides the embed_mode key in [config].'
        ),
    )
    webhook_group.add_argument(
        '--webhook-username',
        metavar='NAME',
        help='Override the webhook bot display name.',
    )
    webhook_group.add_argument(
        '--webhook-avatar',
        metavar='URL',
        help='Override the webhook bot avatar URL.',
    )

    args = parser.parse_args()

    if args.watch:
        watch(args.file, args.target, args.output)
        return

    yaif_parser = YAIFParser()
    try:
        interfaces, enums, config = yaif_parser.parse_file(args.file)
    except (YAIFParseError, FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(interfaces)} interface(s), {len(enums)} enum(s) from {args.file}")
    if config.raw:
        print(f"  Config: {', '.join(f'{k}={v!r}' for k, v in config.raw.items())}")
    for iface in interfaces:
        ext = f" (extends {iface.parent})" if iface.parent else ""
        print(f"  - {iface.name}{ext} ({len(iface.fields)} fields)")
    for enum in enums:
        print(f"  - {enum.name} (enum: {len(enum.values)} values)")

    if args.validate_only:
        print("Validation passed!")
        sys.exit(0)

    generator = GENERATORS[args.target]
    output = generator.generate(interfaces, enums, config)

    # ── Webhook send ───────────────────────────────────────────────────────────
    if args.send:
        from .discord_webhook import send, WebhookError

        # --embed flag overrides config; if neither set, defaults to False inside send()
        embed_mode = True if args.embed else None

        try:
            send(
                interfaces=interfaces,
                enums=enums,
                config=config,
                webhook_url=args.webhook_url,
                embed_mode=embed_mode,
                username=args.webhook_username,
                avatar_url=args.webhook_avatar,
                plain_text_content=output if args.target == 'discord' else None,
            )
            mode_label = "embeds" if (embed_mode or config.get_bool("embed_mode")) else "text"
            print(f"✓ Sent to Discord webhook ({mode_label} mode).")
        except WebhookError as e:
            print(f"Webhook error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # ── Normal file / stdout output ────────────────────────────────────────────
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Generated {args.target} code -> {args.output}")
    else:
        print(f"\n--- Generated {args.target} ---\n")
        print(output)


if __name__ == '__main__':
    main()