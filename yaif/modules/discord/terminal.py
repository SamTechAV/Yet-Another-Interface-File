"""
terminal.py — YAIF terminal output mode.
Pretty-prints the parsed config to the console. Nothing is sent or created.

When a [message] section is present the full Discord-ready message is printed
inside a clearly labelled box so you can copy-paste it directly into Discord.
"""


# ─── Helpers ──────────────────────────────────────────────────────────────────

def divider(char='─', width=60):
    print(char * width)


# ─── Terminal Output ──────────────────────────────────────────────────────────

def run_terminal(config):
    meta       = config.get('meta', {})
    server     = config.get('server', {})
    roles      = config.get('roles', [])
    categories = config.get('categories', [])
    system     = config.get('system', {})
    emojis     = config.get('emojis', [])
    message    = config.get('message', {})

    divider('═')
    print(f"  YAIF Discord Config — {meta.get('name', 'Unnamed')}")
    print(f"  Version: {meta.get('version', '?')}  |  Target: {meta.get('target', '?')}")
    divider('═')

    if server:
        print("\n📋 SERVER SETTINGS")
        divider()
        for k, v in server.items():
            print(f"  {k:<35} {v}")

    if roles:
        print(f"\n🎭 ROLES ({len(roles)} total)")
        divider()
        for role in roles:
            perms = role.get('permissions', [])
            perm_str    = ', '.join(p for p in perms if isinstance(p, str)) if perms else '—'
            hoisted     = '✔' if role.get('hoist') else '✘'
            mentionable = '✔' if role.get('mentionable') else '✘'
            color       = role.get('color', '—')
            print(f"  {role.get('name','?'):<20} color={color:<10}  hoist={hoisted}  mention={mentionable}")
            print(f"    perms: {perm_str}")

    if categories:
        print(f"\n📁 CATEGORIES & CHANNELS")
        divider()
        for cat in categories:
            private_tag = ' 🔒 [PRIVATE]' if cat.get('private') else ''
            print(f"\n  [{cat.get('name','?')}]{private_tag}  (position {cat.get('position','?')})")
            for ch in cat.get('channels', []):
                icon = '🔊' if ch.get('type') == 'voice' else '💬'
                extras = []
                if ch.get('readonly'):  extras.append('readonly')
                if ch.get('slowmode'): extras.append(f"slowmode={ch['slowmode']}s")
                if ch.get('type') == 'voice':
                    lim = ch.get('user_limit', 0)
                    extras.append(f"limit={'unlimited' if lim == 0 else lim}")
                    if ch.get('bitrate'): extras.append(f"bitrate={ch['bitrate']}")
                extra_str = f"  [{', '.join(extras)}]" if extras else ''
                topic = f"  — {ch['topic']}" if ch.get('topic') else ''
                print(f"    {icon} #{ch.get('name','?')}{topic}{extra_str}")

    if system:
        print(f"\n⚙️  SYSTEM SETTINGS")
        divider()
        for k, v in system.items():
            print(f"  {k:<30} {v}")

    if emojis:
        print(f"\n😄 CUSTOM EMOJIS ({len(emojis)} total)")
        divider()
        for e in emojis:
            print(f"  :{e.get('name','?')}:  →  {e.get('image','?')}")

    # ── Message preview ───────────────────────────────────────────────────────
    if isinstance(message, dict):
        content = message.get('content')
        embed   = message.get('embed', {}) or {}

        has_content = bool(content)
        has_embed   = any(embed.get(k) for k in ('title', 'description'))

        if has_content or has_embed:
            print()
            divider('═')
            print("  💬 MESSAGE PREVIEW  (copy everything between the lines)")
            divider('═')

            if has_content:
                print(str(content))

            if has_embed:
                # Render a plain-text approximation of the embed fields
                # so the terminal output mirrors what Discord will show.
                if embed.get('title'):
                    print(f"\n**{embed['title']}**")
                if embed.get('description'):
                    print(embed['description'])
                if embed.get('footer'):
                    print(f"\n_{embed['footer']}_")

            divider('═')

    print()
    divider('═')
    print("  Done. (terminal mode — nothing was sent or created)")
    divider('═')