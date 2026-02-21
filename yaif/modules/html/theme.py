"""
yaif/modules/html/theme.py

Converts a parsed [theme] block into CSS custom properties and
a <link> tag for Google Fonts.

Supported theme keys
--------------------
title       App name shown in <title> and header
accent      Primary colour  (buttons, focus rings, highlights)
bg          Page background
surface     Card / panel background
ink         Primary text
muted       Secondary / hint text
border      Border colour (auto-derived from muted if omitted)
font        CSS font-family string for body text
mono        CSS font-family string for monospace
radius      Border radius in px (default 8)
dark        true | false  — adds a data-theme attr for potential overrides

Google Fonts are auto-requested for a curated set of known font names.
"""

from __future__ import annotations

# Fonts we know are on Google Fonts — maps first family name → import slug
_GFONTS: dict[str, str] = {
    'Instrument Serif':  'Instrument+Serif:ital@0;1',
    'Lora':              'Lora:ital,wght@0,400;0,600;1,400',
    'Fraunces':          'Fraunces:opsz,wght@9..144,300;9..144,600;9..144,800',
    'Playfair Display':  'Playfair+Display:wght@400;600;700',
    'DM Serif Display':  'DM+Serif+Display:ital@0;1',
    'Libre Baskerville': 'Libre+Baskerville:ital,wght@0,400;0,700;1,400',
    'Crimson Pro':       'Crimson+Pro:ital,wght@0,400;0,600;1,400',
    'DM Mono':           'DM+Mono:wght@400;500',
    'Fira Code':         'Fira+Code:wght@400;500',
    'JetBrains Mono':    'JetBrains+Mono:wght@400;500',
    'IBM Plex Mono':     'IBM+Plex+Mono:wght@400;500',
}

# Sensible defaults — warm editorial light theme
_DEFAULTS = {
    'title':   'App',
    'accent':  '#c84b31',
    'bg':      '#faf8f4',
    'surface': '#ffffff',
    'ink':     '#1c1917',
    'muted':   '#78716c',
    'font':    "'Lora', Georgia, serif",
    'mono':    "'DM Mono', monospace",
    'radius':  8,
    'dark':    False,
}

# Dark-mode defaults (used when dark: true)
_DARK_DEFAULTS = {
    'accent':  '#e8724a',
    'bg':      '#0f0e0d',
    'surface': '#1c1917',
    'ink':     '#f5f0eb',
    'muted':   '#a8a29e',
}


def _extract_family(font_str: str) -> str:
    """Pull the first font family name out of a CSS font-family string."""
    # strip quotes, take first comma-separated name
    first = font_str.split(',')[0].strip().strip("'\"")
    return first


def resolve(raw: dict) -> dict:
    """
    Merge raw theme values with defaults and return a complete theme dict.
    """
    dark = raw.get('dark', _DEFAULTS['dark'])
    if isinstance(dark, str):
        dark = dark.lower() in ('true', '1', 'yes')

    base = dict(_DEFAULTS)
    if dark:
        base.update(_DARK_DEFAULTS)
    base.update(raw)
    base['dark'] = dark
    return base


def google_fonts_link(theme: dict) -> str:
    """Return a <link> tag for Google Fonts, or '' if nothing needed."""
    slugs = []
    for key in ('font', 'mono'):
        family = _extract_family(str(theme.get(key, '')))
        if family in _GFONTS:
            slugs.append(_GFONTS[family])

    if not slugs:
        return ''

    families = '&family='.join(slugs)
    url = f'https://fonts.googleapis.com/css2?family={families}&display=swap'
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
        f'  <link href="{url}" rel="stylesheet"/>'
    )


def css_vars(theme: dict) -> str:
    """Return a :root { ... } block of CSS custom properties."""
    r = theme.get('radius', _DEFAULTS['radius'])
    return f""":root {{
    --accent:   {theme['accent']};
    --bg:       {theme['bg']};
    --surface:  {theme['surface']};
    --ink:      {theme['ink']};
    --muted:    {theme['muted']};
    --border:   color-mix(in srgb, {theme['muted']} 35%, transparent);
    --font:     {theme['font']};
    --mono:     {theme['mono']};
    --r:        {r}px;
    --r-sm:     {max(2, r - 4)}px;
    --shadow:   0 1px 3px color-mix(in srgb, {theme['ink']} 12%, transparent),
                0 4px 16px color-mix(in srgb, {theme['ink']} 8%, transparent);
    --focus:    0 0 0 3px color-mix(in srgb, {theme['accent']} 25%, transparent);
  }}"""