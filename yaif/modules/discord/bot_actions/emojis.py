"""
bot_actions/emojis.py — Upload custom emojis from [emojis] config.
Images are fetched from URLs and uploaded to the guild.
"""

import urllib.request
import urllib.error
import discord
from ..bot_actions.conflict import SKIP, OVERWRITE, ABORT


def fetch_image(url):
    """Fetch image bytes from a URL. Returns bytes or None on failure."""
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        print(f"    ✘ Failed to fetch image '{url}': {e.reason}")
        return None


async def apply_emojis(guild, emojis_cfg, resolver):
    """
    Upload custom emojis from the [emojis] list.
    Returns False if the user chose Abort, True otherwise.
    """
    if not emojis_cfg:
        return True

    existing = {e.name: e for e in guild.emojis}

    for emoji_cfg in emojis_cfg:
        name  = emoji_cfg.get('name', '').strip()
        image = emoji_cfg.get('image', '').strip()

        if not name:
            print("  ⚠️  Emoji entry missing 'name' — skipped.")
            continue
        if not image:
            print(f"  ⚠️  Emoji '{name}' missing 'image' URL — skipped.")
            continue

        if name in existing:
            resolution = resolver.resolve('emoji', f':{name}:')

            if resolution == ABORT:
                print("  Aborted.")
                return False
            elif resolution == SKIP:
                print(f"  — Skipped emoji ':{name}:'.")
                continue
            elif resolution == OVERWRITE:
                if resolver.dry_run:
                    print(f"  [dry run] Would overwrite emoji ':{name}:'.")
                    continue
                # Discord doesn't support editing emoji images — delete and recreate
                try:
                    await existing[name].delete()
                except discord.Forbidden:
                    print(f"  ✘ Missing permissions to delete emoji ':{name}:'.")
                    continue
                except discord.HTTPException as e:
                    print(f"  ✘ Failed to delete emoji ':{name}:': {e}")
                    continue
        else:
            if resolver.dry_run:
                print(f"  [dry run] Would upload emoji ':{name}:'.")
                continue

        image_bytes = fetch_image(image)
        if image_bytes is None:
            continue

        try:
            await guild.create_custom_emoji(name=name, image=image_bytes)
            print(f"  ✔ Uploaded emoji ':{name}:'.")
        except discord.Forbidden:
            print(f"  ✘ Missing permissions to upload emoji ':{name}:'.")
        except discord.HTTPException as e:
            print(f"  ✘ Failed to upload emoji ':{name}:': {e}")

    return True