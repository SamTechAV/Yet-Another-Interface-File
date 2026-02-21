"""
bot_actions/roles.py — Create or overwrite roles from [roles] config.
"""

import discord
from ..bot_actions.conflict import SKIP, OVERWRITE, ABORT


# ─── Permission name → discord.Permissions flag ───────────────────────────────

PERMISSION_MAP = {
    'administrator':            'administrator',
    'manage_guild':             'manage_guild',
    'manage_roles':             'manage_roles',
    'manage_channels':          'manage_channels',
    'manage_messages':          'manage_messages',
    'manage_nicknames':         'manage_nicknames',
    'manage_emojis':            'manage_emojis',
    'manage_webhooks':          'manage_webhooks',
    'kick_members':             'kick_members',
    'ban_members':              'ban_members',
    'mention_everyone':         'mention_everyone',
    'send_messages':            'send_messages',
    'read_messages':            'read_messages',
    'view_channel':             'view_channel',
    'embed_links':              'embed_links',
    'attach_files':             'attach_files',
    'read_message_history':     'read_message_history',
    'connect':                  'connect',
    'speak':                    'speak',
    'mute_members':             'mute_members',
    'deafen_members':           'deafen_members',
    'move_members':             'move_members',
    'use_voice_activation':     'use_voice_activation',
    'change_nickname':          'change_nickname',
    'add_reactions':            'add_reactions',
    'use_application_commands': 'use_application_commands',
}


def build_permissions(perm_list):
    """Convert a list of permission name strings into a discord.Permissions object."""
    kwargs = {}
    for perm in (perm_list or []):
        key = str(perm).lower().strip()
        if key in PERMISSION_MAP:
            kwargs[PERMISSION_MAP[key]] = True
        else:
            print(f"    ⚠️  Unknown permission '{perm}' — skipped.")
    return discord.Permissions(**kwargs)


def parse_color(color_val):
    """Accept an int, 0xRRGGBB string, or #RRGGBB string."""
    if color_val is None:
        return discord.Color.default()
    if isinstance(color_val, int):
        return discord.Color(color_val)
    s = str(color_val).strip().lstrip('#')
    try:
        return discord.Color(int(s, 16))
    except ValueError:
        print(f"    ⚠️  Invalid color '{color_val}' — using default.")
        return discord.Color.default()


# ─── Main Action ─────────────────────────────────────────────────────────────

async def apply_roles(guild, roles_cfg, resolver):
    """
    Create or overwrite roles from the [roles] list.
    Returns False if the user chose Abort, True otherwise.
    """
    if not roles_cfg:
        return True

    existing = {r.name: r for r in guild.roles}

    for role_cfg in roles_cfg:
        name = role_cfg.get('name', '').strip()
        if not name:
            print("  ⚠️  Role entry missing 'name' — skipped.")
            continue

        color       = parse_color(role_cfg.get('color'))
        hoist       = bool(role_cfg.get('hoist', False))
        mentionable = bool(role_cfg.get('mentionable', False))
        permissions = build_permissions(role_cfg.get('permissions', []))

        if name in existing:
            resolution = resolver.resolve('role', name)

            if resolution == ABORT:
                print("  Aborted.")
                return False
            elif resolution == SKIP:
                print(f"  — Skipped role '{name}'.")
                continue
            elif resolution == OVERWRITE:
                if resolver.dry_run:
                    print(f"  [dry run] Would overwrite role '{name}'.")
                    continue
                try:
                    await existing[name].edit(
                        color=color,
                        hoist=hoist,
                        mentionable=mentionable,
                        permissions=permissions,
                    )
                    print(f"  ✔ Overwrote role '{name}'.")
                except discord.Forbidden:
                    print(f"  ✘ Missing permissions to edit role '{name}'.")
                except discord.HTTPException as e:
                    print(f"  ✘ Failed to edit role '{name}': {e}")
        else:
            if resolver.dry_run:
                print(f"  [dry run] Would create role '{name}'.")
                continue
            try:
                await guild.create_role(
                    name=name,
                    color=color,
                    hoist=hoist,
                    mentionable=mentionable,
                    permissions=permissions,
                )
                print(f"  ✔ Created role '{name}'.")
            except discord.Forbidden:
                print(f"  ✘ Missing permissions to create role '{name}'.")
            except discord.HTTPException as e:
                print(f"  ✘ Failed to create role '{name}': {e}")

    return True