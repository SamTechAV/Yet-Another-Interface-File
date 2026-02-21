"""
bot_actions/channels.py — Create categories and channels from [categories] config.
"""

import discord
from ..bot_actions.conflict import SKIP, OVERWRITE, ABORT


async def apply_channels(guild, categories_cfg, resolver):
    """
    Create categories and their child channels.
    Returns False if the user chose Abort, True otherwise.
    """
    if not categories_cfg:
        return True

    existing_categories = {c.name: c for c in guild.categories}
    existing_channels   = {c.name: c for c in guild.channels}

    for cat_cfg in categories_cfg:
        cat_name = cat_cfg.get('name', '').strip()
        if not cat_name:
            print("  ⚠️  Category entry missing 'name' — skipped.")
            continue

        position = cat_cfg.get('position', 0)
        overwrites = {}

        if cat_cfg.get('private'):
            overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)

        # ── Category ──────────────────────────────────────────────────────────
        if cat_name in existing_categories:
            resolution = resolver.resolve('category', cat_name)

            if resolution == ABORT:
                print("  Aborted.")
                return False
            elif resolution == SKIP:
                print(f"  — Skipped category '{cat_name}' and its channels.")
                continue
            elif resolution == OVERWRITE:
                category = existing_categories[cat_name]
                if not resolver.dry_run:
                    try:
                        await category.edit(position=position, overwrites=overwrites)
                        print(f"  ✔ Updated category '{cat_name}'.")
                    except discord.Forbidden:
                        print(f"  ✘ Missing permissions to edit category '{cat_name}'.")
                        continue
                    except discord.HTTPException as e:
                        print(f"  ✘ Failed to edit category '{cat_name}': {e}")
                        continue
                else:
                    print(f"  [dry run] Would update category '{cat_name}'.")
        else:
            if resolver.dry_run:
                print(f"  [dry run] Would create category '{cat_name}'.")
                category = None
            else:
                try:
                    category = await guild.create_category(
                        name=cat_name,
                        position=position,
                        overwrites=overwrites,
                    )
                    print(f"  ✔ Created category '{cat_name}'.")
                except discord.Forbidden:
                    print(f"  ✘ Missing permissions to create category '{cat_name}'.")
                    continue
                except discord.HTTPException as e:
                    print(f"  ✘ Failed to create category '{cat_name}': {e}")
                    continue

        # ── Channels inside category ──────────────────────────────────────────
        for ch_cfg in cat_cfg.get('channels', []):
            ch_name = ch_cfg.get('name', '').strip()
            if not ch_name:
                print("    ⚠️  Channel entry missing 'name' — skipped.")
                continue

            ch_type     = ch_cfg.get('type', 'text')
            topic       = ch_cfg.get('topic')
            readonly    = ch_cfg.get('readonly', False)
            slowmode    = ch_cfg.get('slowmode', 0)
            user_limit  = ch_cfg.get('user_limit', 0)
            bitrate     = ch_cfg.get('bitrate', 64000)

            ch_overwrites = dict(overwrites)
            if readonly:
                ch_overwrites[guild.default_role] = discord.PermissionOverwrite(
                    send_messages=False,
                    view_channel=True,
                )

            if ch_name in existing_channels:
                resolution = resolver.resolve('channel', f'#{ch_name}')

                if resolution == ABORT:
                    print("  Aborted.")
                    return False
                elif resolution == SKIP:
                    print(f"    — Skipped channel '#{ch_name}'.")
                    continue
                elif resolution == OVERWRITE:
                    if resolver.dry_run:
                        print(f"    [dry run] Would overwrite channel '#{ch_name}'.")
                        continue
                    ch = existing_channels[ch_name]
                    try:
                        if ch_type == 'voice':
                            await ch.edit(user_limit=user_limit, bitrate=bitrate)
                        else:
                            await ch.edit(
                                topic=topic,
                                slowmode_delay=slowmode,
                                overwrites=ch_overwrites,
                            )
                        print(f"    ✔ Updated channel '#{ch_name}'.")
                    except discord.Forbidden:
                        print(f"    ✘ Missing permissions to edit '#{ch_name}'.")
                    except discord.HTTPException as e:
                        print(f"    ✘ Failed to edit '#{ch_name}': {e}")
            else:
                if resolver.dry_run:
                    print(f"    [dry run] Would create {'voice' if ch_type == 'voice' else 'text'} channel '#{ch_name}'.")
                    continue
                try:
                    if ch_type == 'voice':
                        await guild.create_voice_channel(
                            name=ch_name,
                            category=category,
                            user_limit=user_limit,
                            bitrate=bitrate,
                            overwrites=ch_overwrites,
                        )
                    else:
                        await guild.create_text_channel(
                            name=ch_name,
                            category=category,
                            topic=topic,
                            slowmode_delay=slowmode,
                            overwrites=ch_overwrites,
                        )
                    print(f"    ✔ Created channel '#{ch_name}'.")
                except discord.Forbidden:
                    print(f"    ✘ Missing permissions to create '#{ch_name}'.")
                except discord.HTTPException as e:
                    print(f"    ✘ Failed to create '#{ch_name}': {e}")

    return True