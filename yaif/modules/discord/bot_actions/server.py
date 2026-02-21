"""
bot_actions/server.py — Apply [server] settings to a Discord guild.
"""

import discord
from ..bot_actions.conflict import ABORT


async def apply_server(guild, server_cfg, resolver):
    """
    Apply top-level server settings from [server] config.
    Supported keys: name, description, verification_level.
    """
    if not server_cfg:
        return True

    dry_run = resolver.dry_run

    edit_kwargs = {}

    if server_cfg.get('name') and server_cfg['name'] != guild.name:
        edit_kwargs['name'] = server_cfg['name']

    if server_cfg.get('description') is not None:
        edit_kwargs['description'] = server_cfg['description']

    level_map = {
        'none':    discord.VerificationLevel.none,
        'low':     discord.VerificationLevel.low,
        'medium':  discord.VerificationLevel.medium,
        'high':    discord.VerificationLevel.high,
        'highest': discord.VerificationLevel.highest,
    }
    if server_cfg.get('verification_level'):
        level = level_map.get(str(server_cfg['verification_level']).lower())
        if level:
            edit_kwargs['verification_level'] = level

    if not edit_kwargs:
        print("  ✔ Server settings — nothing to change.")
        return True

    if dry_run:
        for k, v in edit_kwargs.items():
            print(f"  [dry run] Would update server {k} → {v}")
        return True

    try:
        await guild.edit(**edit_kwargs)
        for k, v in edit_kwargs.items():
            print(f"  ✔ Server {k} → {v}")
    except discord.Forbidden:
        print("  ✘ Missing permissions to edit server settings.")
    except discord.HTTPException as e:
        print(f"  ✘ Failed to edit server: {e}")

    return True