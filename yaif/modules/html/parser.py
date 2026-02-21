"""
yaif/modules/html/parser.py

Parses YAIF v2 HTML syntax into a clean Python structure.

Section types recognised
------------------------
[theme]           — app-wide visual tokens
[page Name]       — declares a page  (type: form|table|dashboard|chat)
[field Name]      — input field attached to the most-recent page
[column Name]     — table column header attached to the most-recent table page
[row]             — data row attached to the most-recent table page
[stat]            — metric card attached to the most-recent dashboard page
[message]         — chat bubble attached to the most-recent chat page
"""

from __future__ import annotations
import re
from typing import Any


# ─── Low-level helpers ────────────────────────────────────────────────────────

def _strip_comment(line: str) -> str:
    """Strip # comments but preserve # inside quoted strings and hex colours."""
    result, in_q, i = [], None, 0
    while i < len(line):
        ch = line[i]
        if in_q:
            result.append(ch)
            if ch == in_q:
                in_q = None
        elif ch in ('"', "'"):
            in_q = ch
            result.append(ch)
        elif ch == '#':
            rest = line[i + 1:]
            if re.match(r'^[0-9a-fA-F]{3,6}\b', rest):
                result.append(ch)   # hex colour — keep it
            else:
                break               # comment — discard rest
        else:
            result.append(ch)
        i += 1
    return ''.join(result).rstrip()


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] in ('"', "'") and s[-1] == s[0]:
        return s[1:-1]
    return s


def _coerce(raw: str) -> Any:
    """Convert a raw string value to int / bool / str as appropriate."""
    v = _unquote(raw.strip())
    if v.lower() == 'true':  return True
    if v.lower() == 'false': return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


def _parse_kv(lines: list[str]) -> dict:
    """Parse key: value lines into a dict, coercing values."""
    d: dict = {}
    for raw in lines:
        s = _strip_comment(raw).strip()
        if not s:
            continue
        colon = s.find(':')
        if colon == -1:
            continue
        k = s[:colon].strip()
        v = _coerce(s[colon + 1:])
        d[k] = v
    return d


# ─── Section splitter ─────────────────────────────────────────────────────────

def _split_sections(text: str) -> list[tuple[str, list[str]]]:
    """
    Split text into (header, body_lines) pairs.
    Header is the raw content inside [...], body_lines are the following lines.
    """
    sections: list[tuple[str, list[str]]] = []
    current_header: str | None = None
    current_body:   list[str]  = []

    for raw in text.splitlines():
        stripped = _strip_comment(raw).strip()
        m = re.fullmatch(r'\[(.+?)\]', stripped)
        if m:
            if current_header is not None:
                sections.append((current_header, current_body))
            current_header = m.group(1).strip()
            current_body   = []
        elif current_header is not None:
            current_body.append(_strip_comment(raw))

    if current_header is not None:
        sections.append((current_header, current_body))

    return sections


# ─── Public parse function ────────────────────────────────────────────────────

def parse(text: str) -> dict:
    """
    Parse a YAIF HTML document and return a structured dict:

    {
      "theme": { ... },
      "pages": [
        {
          "name":     "PageName",
          "type":     "form" | "table" | "dashboard" | "chat",
          "props":    { ... },          # title, subtitle, submit, etc.
          "fields":   [ { name, ...kv } ],   # form
          "columns":  [ { name, ...kv } ],   # table
          "rows":     [ { col: val, ... } ],  # table
          "stats":    [ { label, value, ... } ],  # dashboard
          "messages": [ { author, text, ... } ],  # chat
        },
        ...
      ]
    }
    """
    sections = _split_sections(text)

    theme: dict          = {}
    pages: list[dict]    = []
    current_page: dict | None = None

    def _flush_page():
        if current_page is not None:
            pages.append(current_page)

    for header, body_lines in sections:
        kv = _parse_kv(body_lines)

        # ── [theme] ───────────────────────────────────────────────────────────
        if header.lower() == 'theme':
            theme = kv
            continue

        # ── [page Name] ───────────────────────────────────────────────────────
        pm = re.fullmatch(r'page\s+(\S+)', header, re.I)
        if pm:
            _flush_page()
            current_page = {
                'name':     pm.group(1),
                'type':     str(kv.pop('type', 'form')).lower(),
                'props':    kv,
                'fields':   [],
                'columns':  [],
                'rows':     [],
                'stats':    [],
                'messages': [],
            }
            continue

        # ── [field Name] ──────────────────────────────────────────────────────
        fm = re.fullmatch(r'field\s+(\S+)', header, re.I)
        if fm and current_page is not None:
            entry = {'name': fm.group(1)}
            entry.update(kv)
            current_page['fields'].append(entry)
            continue

        # ── [column Name] ─────────────────────────────────────────────────────
        cm = re.fullmatch(r'column\s+(\S+)', header, re.I)
        if cm and current_page is not None:
            entry = {'name': cm.group(1)}
            entry.update(kv)
            current_page['columns'].append(entry)
            continue

        # ── [row] ─────────────────────────────────────────────────────────────
        if header.lower() == 'row' and current_page is not None:
            current_page['rows'].append(kv)
            continue

        # ── [stat] ────────────────────────────────────────────────────────────
        if header.lower() == 'stat' and current_page is not None:
            current_page['stats'].append(kv)
            continue

        # ── [message] ─────────────────────────────────────────────────────────
        if header.lower() == 'message' and current_page is not None:
            current_page['messages'].append(kv)
            continue

    _flush_page()

    return {'theme': theme, 'pages': pages}