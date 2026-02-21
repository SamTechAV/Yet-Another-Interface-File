"""
modules/discord/bot.py — YAIF bot output mode.
Connects to Discord via a bot token and applies server configuration.

Execution order:
  1. Server settings
  2. Roles
  3. Categories + channels
  4. Emojis
"""

import sys
import asyncio
import discord

from .bot_actions import (
    ConflictResolver,
    apply_server,
    apply_roles,
    apply_channels,
    apply_emojis,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def divider(char='─', width=60):
    print(char * width)


# ─── Bot Client ───────────────────────────────────────────────────────────────

async def _run(token, guild_id, config, resolver):
    """Internal async runner — connects, applies config, disconnects."""

    intents = discord.Intents.default()
    intents.guilds = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            guild = client.get_guild(guild_id)
            if guild is None:
                print(f"✘ Bot is not a member of guild ID {guild_id}.")
                print("  Invite the bot to your server first.")
                await client.close()
                return

            divider('═')
            print(f"  YAIF Bot — connected as {client.user}")
            print(f"  Guild: {guild.name} ({guild.id})")
            if resolver.dry_run:
                print("  ⚠️  DRY RUN — no changes will be made.")
            divider('═')
            print()

            # ── Execute in order ──────────────────────────────────────────────

            print("📋 Applying server settings...")
            ok = await apply_server(guild, config.get('server', {}), resolver)
            if not ok:
                await client.close()
                return

            print("\n🎭 Applying roles...")
            ok = await apply_roles(guild, config.get('roles', []), resolver)
            if not ok:
                await client.close()
                return

            print("\n📁 Applying categories & channels...")
            ok = await apply_channels(guild, config.get('categories', []), resolver)
            if not ok:
                await client.close()
                return

            print("\n😄 Applying emojis...")
            ok = await apply_emojis(guild, config.get('emojis', []), resolver)
            if not ok:
                await client.close()
                return

            print()
            divider('═')
            if resolver.dry_run:
                print("  Dry run complete — no changes were made.")
            else:
                print("  ✔ Bot setup complete.")
            divider('═')

        except Exception as e:
            print(f"✘ Unexpected error: {e}")
        finally:
            await client.close()

    await client.start(token)


# ─── Public Entry Point ───────────────────────────────────────────────────────

def run_bot(config):
    bot_cfg = config.get('config', {}).get('bot', {})
    if not isinstance(bot_cfg, dict):
        bot_cfg = {}

    token = bot_cfg.get('token', '').strip()
    if not token or 'YOUR_TOKEN' in token:
        print("✘ Error: No valid bot token found in [config.bot] token.")
        sys.exit(1)

    guild_id = bot_cfg.get('guild_id')
    if not guild_id:
        print("✘ Error: No guild_id found in [config.bot] guild_id.")
        print("  Set it to your Discord server's ID (right-click server → Copy Server ID).")
        sys.exit(1)

    dry_run  = bool(bot_cfg.get('dry_run', False))
    resolver = ConflictResolver(dry_run=dry_run)

    try:
        asyncio.run(_run(str(token), int(guild_id), config, resolver))
    except discord.LoginFailure:
        print("✘ Invalid bot token — login failed.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)