"""
yaif/modules/html/generator.py

Entry point for the YAIF HTML generator.

    from yaif.modules.html.generator import generate

    html_string = generate(yaif_text)

Or from the file system:

    from yaif.modules.html.generator import generate_file
    generate_file("myapp.yaif", "myapp.html")
"""

from __future__ import annotations
import html as _h

from .parser             import parse
from .theme              import resolve as resolve_theme, css_vars, google_fonts_link
from .renderers          import RENDERERS


def _esc(s) -> str:
    return _h.escape(str(s)) if s is not None else ''


# ─── Shared CSS ───────────────────────────────────────────────────────────────

_BASE_CSS = """
  /* ── Reset ──────────────────────────────────────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }

  body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--ink);
    min-height: 100vh;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  .sr-only {
    position: absolute; width: 1px; height: 1px;
    padding: 0; margin: -1px; overflow: hidden;
    clip: rect(0,0,0,0); white-space: nowrap; border: 0;
  }

  /* ── App shell ───────────────────────────────────────────────────────── */
  .shell {
    display: grid;
    grid-template-columns: 220px 1fr;
    grid-template-rows: 56px 1fr;
    min-height: 100vh;
  }

  /* ── Top bar ─────────────────────────────────────────────────────────── */
  .topbar {
    grid-column: 1 / -1;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 1.5rem;
    gap: 0.75rem;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow);
  }

  .app-name {
    font-size: 0.95rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--ink);
  }

  .topbar-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
  }

  /* ── Sidebar nav ─────────────────────────────────────────────────────── */
  .sidebar {
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 1.25rem 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow-y: auto;
  }

  .nav-label {
    font-family: var(--mono);
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    padding: 0.25rem 1.25rem 0.5rem;
    margin-top: 0.5rem;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.45rem 1.25rem;
    font-size: 0.85rem;
    color: var(--muted);
    text-decoration: none;
    border-radius: 0;
    transition: color 0.12s, background 0.12s;
    cursor: pointer;
    border: none;
    background: none;
    width: 100%;
    text-align: left;
  }

  .nav-item:hover {
    color: var(--ink);
    background: color-mix(in srgb, var(--ink) 5%, transparent);
  }

  .nav-item.active {
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
    font-weight: 500;
  }

  .nav-icon {
    font-size: 0.9rem;
    width: 1.1rem;
    text-align: center;
    flex-shrink: 0;
  }

  /* ── Main content ────────────────────────────────────────────────────── */
  .content {
    padding: 2rem 2.5rem;
    overflow-y: auto;
  }

  /* ── Page sections ───────────────────────────────────────────────────── */
  .page { display: none; }
  .page.active { display: block; }

  .page-header {
    margin-bottom: 1.75rem;
  }

  .page-title {
    font-size: 1.4rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }

  .page-sub {
    font-size: 0.85rem;
    color: var(--muted);
    margin-top: 0.3rem;
  }

  /* ── Forms ───────────────────────────────────────────────────────────── */
  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.25rem 1.75rem;
    max-width: 900px;
  }

  .field { display: flex; flex-direction: column; gap: 5px; }
  .field-wide { grid-column: 1 / -1; }

  .field-label {
    font-family: var(--mono);
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 3px;
  }

  .req { color: var(--accent); line-height: 1; }

  .hint {
    font-size: 0.72rem;
    color: var(--muted);
    font-style: italic;
    margin-top: 1px;
  }

  /* inputs */
  input[type="text"],
  input[type="email"],
  input[type="password"],
  input[type="number"],
  input[type="date"],
  input[type="time"],
  input[type="datetime-local"],
  input[type="url"],
  input[type="search"],
  textarea {
    width: 100%;
    font-family: var(--font);
    font-size: 0.875rem;
    color: var(--ink);
    background: var(--bg);
    border: 1.5px solid var(--border);
    border-radius: var(--r-sm);
    padding: 8px 11px;
    outline: none;
    transition: border-color 0.14s, box-shadow 0.14s;
    resize: vertical;
  }

  input:focus,
  textarea:focus,
  select:focus {
    border-color: var(--accent);
    box-shadow: var(--focus);
  }

  input:disabled,
  textarea:disabled,
  select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* select */
  .select-wrap { position: relative; }

  .select-wrap select {
    width: 100%;
    font-family: var(--font);
    font-size: 0.875rem;
    color: var(--ink);
    background: var(--bg);
    border: 1.5px solid var(--border);
    border-radius: var(--r-sm);
    padding: 8px 30px 8px 11px;
    appearance: none;
    outline: none;
    cursor: pointer;
    transition: border-color 0.14s, box-shadow 0.14s;
  }

  .chevron {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
    color: var(--muted);
    font-size: 1rem;
    line-height: 1;
  }

  /* toggle */
  .toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 0;
  }

  .toggle {
    position: relative;
    display: inline-block;
    width: 38px;
    height: 21px;
    flex-shrink: 0;
  }

  .toggle input { opacity: 0; width: 0; height: 0; }

  .knob {
    position: absolute;
    inset: 0;
    background: var(--border);
    border-radius: 21px;
    cursor: pointer;
    transition: background 0.18s;
  }

  .knob::before {
    content: '';
    position: absolute;
    width: 15px; height: 15px;
    left: 3px; bottom: 3px;
    background: #fff;
    border-radius: 50%;
    transition: transform 0.18s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }

  .toggle input:checked + .knob { background: var(--accent); }
  .toggle input:checked + .knob::before { transform: translateX(17px); }

  /* range */
  .range-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .range-val {
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--accent);
    background: none;
    border: none;
    padding: 0;
    min-width: 2ch;
    text-align: right;
  }

  input[type="range"] {
    width: 100%;
    height: 4px;
    accent-color: var(--accent);
    cursor: pointer;
    border: none;
    box-shadow: none;
    padding: 0;
    background: none;
  }

  /* color */
  .color-wrap {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 4px 0;
  }

  input[type="color"] {
    width: 36px; height: 36px;
    padding: 2px;
    border: 1.5px solid var(--border);
    border-radius: var(--r-sm);
    background: var(--bg);
    cursor: pointer;
    outline: none;
    box-shadow: none;
  }

  input[type="color"]:focus { box-shadow: var(--focus); }

  .color-val {
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--muted);
  }

  /* file */
  .file-drop {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 1.5rem;
    border: 1.5px dashed var(--border);
    border-radius: var(--r-sm);
    cursor: pointer;
    transition: border-color 0.14s, background 0.14s;
    text-align: center;
  }

  .file-drop:hover {
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 5%, transparent);
  }

  .file-icon { font-size: 1.6rem; line-height: 1; }

  .file-text {
    font-size: 0.8rem;
    color: var(--muted);
  }

  /* form actions */
  .form-actions {
    padding-top: 0.5rem;
  }

  /* ── Buttons ─────────────────────────────────────────────────────────── */
  .btn-primary {
    font-family: var(--mono);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    padding: 9px 20px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: var(--r-sm);
    cursor: pointer;
    transition: filter 0.14s, transform 0.1s;
  }

  .btn-primary:hover { filter: brightness(1.1); transform: translateY(-1px); }
  .btn-primary:active { transform: translateY(0); }

  /* ── Tables ──────────────────────────────────────────────────────────── */
  .table-wrap {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: var(--r);
    box-shadow: var(--shadow);
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.855rem;
    background: var(--surface);
  }

  .data-table thead {
    background: color-mix(in srgb, var(--ink) 4%, var(--surface));
    border-bottom: 1px solid var(--border);
  }

  .data-table th {
    font-family: var(--mono);
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    padding: 10px 14px;
    text-align: left;
    white-space: nowrap;
  }

  .data-table td {
    padding: 10px 14px;
    border-top: 1px solid var(--border);
    color: var(--ink);
    vertical-align: middle;
  }

  .data-table.striped tbody tr:nth-child(even) td {
    background: color-mix(in srgb, var(--ink) 2%, transparent);
  }

  .data-table.bordered th,
  .data-table.bordered td {
    border: 1px solid var(--border);
  }

  .data-table tbody tr:hover td {
    background: color-mix(in srgb, var(--accent) 5%, transparent);
  }

  .empty-row {
    text-align: center;
    color: var(--muted);
    font-style: italic;
    padding: 2rem !important;
  }

  /* badges */
  .badge {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.65rem;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 100px;
    letter-spacing: 0.04em;
    white-space: nowrap;
  }

  /* ── Dashboard ───────────────────────────────────────────────────────── */
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(var(--cols, 3), 1fr);
    gap: 1.25rem;
  }

  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    transition: box-shadow 0.15s;
  }

  .stat-card:hover {
    box-shadow: 0 4px 24px color-mix(in srgb, var(--ink) 14%, transparent);
  }

  .stat-wide { grid-column: span 2; }

  .stat-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
  }

  .stat-label {
    font-family: var(--mono);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .stat-icon { font-size: 1.2rem; line-height: 1; }

  .stat-value {
    font-size: 1.9rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    line-height: 1;
    color: var(--ink);
  }

  .stat-delta {
    font-family: var(--mono);
    font-size: 0.72rem;
    display: flex;
    align-items: center;
    gap: 3px;
  }

  .delta-up   { color: #16a34a; }
  .delta-down { color: #dc2626; }

  .arrow { font-size: 0.6rem; }

  /* ── Chat ────────────────────────────────────────────────────────────── */
  .chat-window {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 260px);
    min-height: 400px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    box-shadow: var(--shadow);
    overflow: hidden;
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .message {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    max-width: 72%;
    animation: msgIn 0.2s ease;
  }

  @keyframes msgIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .msg-left  { align-self: flex-start; }
  .msg-right { align-self: flex-end; flex-direction: row-reverse; }

  .avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    color: #fff;
    flex-shrink: 0;
    user-select: none;
  }

  .msg-body { display: flex; flex-direction: column; gap: 3px; }

  .msg-meta {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }

  .msg-author {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--ink);
  }

  .msg-time {
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--muted);
  }

  .bubble {
    font-size: 0.875rem;
    line-height: 1.5;
    padding: 9px 13px;
    border-radius: var(--r);
    word-break: break-word;
  }

  .bubble-left {
    background: color-mix(in srgb, var(--ink) 7%, var(--bg));
    border-bottom-left-radius: 3px;
  }

  .bubble-right {
    background: var(--accent);
    color: #fff;
    border-bottom-right-radius: 3px;
  }

  .chat-input-bar {
    display: flex;
    gap: 0.5rem;
    padding: 0.875rem 1.25rem;
    border-top: 1px solid var(--border);
    background: var(--surface);
  }

  .chat-input {
    flex: 1;
    font-family: var(--font);
    font-size: 0.875rem;
    color: var(--ink);
    background: var(--bg);
    border: 1.5px solid var(--border);
    border-radius: var(--r-sm);
    padding: 8px 12px;
    outline: none;
    transition: border-color 0.14s, box-shadow 0.14s;
  }

  .chat-input:focus {
    border-color: var(--accent);
    box-shadow: var(--focus);
  }

  /* ── Empty state ─────────────────────────────────────────────────────── */
  .empty-state {
    color: var(--muted);
    font-style: italic;
    font-size: 0.85rem;
    padding: 2rem 0;
  }

  /* ── Responsive ──────────────────────────────────────────────────────── */
  @media (max-width: 768px) {
    .shell {
      grid-template-columns: 1fr;
      grid-template-rows: 56px auto 1fr;
    }

    .sidebar {
      grid-column: 1;
      flex-direction: row;
      overflow-x: auto;
      padding: 0.5rem;
      border-right: none;
      border-bottom: 1px solid var(--border);
    }

    .nav-label { display: none; }

    .nav-item { padding: 0.4rem 0.75rem; white-space: nowrap; }

    .content { padding: 1.25rem; }

    .stat-grid { grid-template-columns: repeat(2, 1fr); }
    .stat-wide { grid-column: span 2; }

    .form-grid { grid-template-columns: 1fr; }

    .message { max-width: 90%; }
  }

  @media (max-width: 480px) {
    .stat-grid { grid-template-columns: 1fr; }
    .stat-wide { grid-column: span 1; }
  }
"""

# Page type → sidebar icon
_ICONS = {
    'form':      '&#9998;',   # ✎
    'table':     '&#9776;',   # ☰
    'dashboard': '&#9632;',   # ■
    'chat':      '&#9993;',   # ✉
}


# ─── Main generate function ───────────────────────────────────────────────────

def generate(yaif_text: str) -> str:
    """
    Parse a YAIF document and return a complete, self-contained HTML string.
    """
    doc    = parse(yaif_text)
    theme  = resolve_theme(doc['theme'])
    pages  = doc['pages']

    title       = _esc(theme.get('title', 'App'))
    fonts_link  = google_fonts_link(theme)
    root_css    = css_vars(theme)

    # ── Sidebar nav ───────────────────────────────────────────────────────
    nav_items = ''
    for i, page in enumerate(pages):
        active_cls = 'active' if i == 0 else ''
        icon       = _ICONS.get(page['type'], '&#9632;')
        label      = _esc(page.get('props', {}).get('title') or page['name'].replace('_', ' '))
        nav_items += (
            f'<button class="nav-item {active_cls}" '
            f'onclick="showPage(\'{page["name"]}\')" '
            f'id="nav-{_esc(page["name"])}">'
            f'<span class="nav-icon" aria-hidden="true">{icon}</span>'
            f'{label}</button>\n'
        )

    # ── Page sections ─────────────────────────────────────────────────────
    sections_html = ''
    for i, page in enumerate(pages):
        renderer = RENDERERS.get(page['type'])
        if renderer is None:
            continue
        rendered = renderer(page)
        active_cls = 'active' if i == 0 else ''
        # Wrap in a visibility div that generator.js will show/hide
        sections_html += (
            f'<div class="page {active_cls}" id="page-wrap-{_esc(page["name"])}">'
            f'{rendered}</div>\n'
        )

    # ── Minimal nav JS (no framework, pure DOM) ───────────────────────────
    nav_js = """
  function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    var wrap = document.getElementById('page-wrap-' + name);
    var nav  = document.getElementById('nav-' + name);
    if (wrap) wrap.classList.add('active');
    if (nav)  nav.classList.add('active');
  }
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
  {fonts_link}
  <style>
  {root_css}
{_BASE_CSS}
  </style>
</head>
<body>

<div class="shell">

  <header class="topbar">
    <span class="topbar-dot" aria-hidden="true"></span>
    <span class="app-name">{title}</span>
  </header>

  <nav class="sidebar" aria-label="Pages">
    {nav_items}
  </nav>

  <main class="content">
    {sections_html}
  </main>

</div>

<script>{nav_js}</script>
</body>
</html>"""


# ─── File helpers ─────────────────────────────────────────────────────────────

def generate_file(in_path: str, out_path: str | None = None) -> str:
    """Read a .yaif file, generate HTML, optionally write it, return the string."""
    with open(in_path, 'r', encoding='utf-8') as f:
        text = f.read()

    result = generate(text)

    if out_path is None:
        out_path = in_path.rsplit('.', 1)[0] + '.html'

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f'✔  {in_path}  →  {out_path}  ({len(result):,} bytes)')
    return result