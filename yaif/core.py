"""
core.py — YAIF shared constants, parser, and utility helpers.
Imported by terminal.py and webhook.py.
"""

import re

# ─── Discord API Limits ───────────────────────────────────────────────────────

DISCORD_MESSAGE_LIMIT      = 2000
DISCORD_MAX_EMBEDS         = 10
DISCORD_EMBED_TITLE_LIMIT  = 256
DISCORD_FIELD_NAME_LIMIT   = 256
DISCORD_FIELD_VALUE_LIMIT  = 1024
DISCORD_FOOTER_LIMIT       = 2048


# ─── Parser ───────────────────────────────────────────────────────────────────

def strip_comment(line):
    """Strip inline comments, but preserve # inside quoted strings and hex colors."""
    result = []
    in_quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quote:
            result.append(ch)
            if ch == in_quote:
                in_quote = None
        elif ch in ('"', "'"):
            in_quote = ch
            result.append(ch)
        elif ch == '#':
            # Check if this looks like a hex color (#RGB or #RRGGBB)
            rest = line[i+1:]
            if re.match(r'^[0-9a-fA-F]{3,6}\b', rest):
                result.append(ch)
            else:
                break  # It's a comment
        else:
            result.append(ch)
        i += 1
    return ''.join(result).rstrip()


def parse_value(v):
    v = v.strip()
    if not v:
        return None
    if v.lower() == 'true':
        return True
    if v.lower() == 'false':
        return False
    if re.fullmatch(r'\d+', v):
        return int(v)
    if re.fullmatch(r'0x[0-9a-fA-F]+', v):
        return int(v, 16)
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def parse_dict(lines):
    """
    Parse key: value lines into a dict.
    Supports block scalars:
        key: |
          line one
          line two
    The '|' marker collects all following indented lines as a
    newline-joined string (trailing newline stripped).
    """
    d = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if ':' in stripped:
            k, _, v = stripped.partition(':')
            k = k.strip()
            v = v.strip()

            if v == '|':
                # Block scalar — collect indented lines that follow
                block_lines = []
                i += 1
                # Determine base indent from first non-empty line
                base_indent = None
                while i < len(lines):
                    bl = lines[i]
                    if not bl.strip():
                        block_lines.append('')
                        i += 1
                        continue
                    indent = len(bl) - len(bl.lstrip())
                    if base_indent is None:
                        base_indent = indent
                    if indent < (base_indent or 0):
                        break  # Back-dedented — block is over
                    # Strip exactly base_indent leading spaces
                    block_lines.append(bl[base_indent:].rstrip())
                    i += 1
                # Trim trailing blank lines
                while block_lines and block_lines[-1] == '':
                    block_lines.pop()
                d[k] = '\n'.join(block_lines)
                continue  # i already advanced inside loop above
            else:
                d[k] = parse_value(v)
        i += 1
    return d


def parse_list(lines):
    items = []
    item_stack = []

    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if stripped.startswith('- '):
            content = stripped[2:]

            if ':' in content:
                k, _, v = content.partition(':')
                k = k.strip()
                v = v.strip()
                new_item = {k: parse_value(v) if v else None}
                if v == '':
                    new_item[k] = []
                    sublist_key = k
                else:
                    sublist_key = None
            else:
                if item_stack:
                    parent_indent, parent_item, parent_subkey = item_stack[-1]
                    if parent_subkey and isinstance(parent_item.get(parent_subkey), list):
                        parent_item[parent_subkey].append(parse_value(content))
                continue

            while item_stack and item_stack[-1][0] >= indent:
                item_stack.pop()

            if not item_stack:
                items.append(new_item)
            else:
                parent_indent, parent_item, parent_subkey = item_stack[-1]
                if parent_subkey and isinstance(parent_item.get(parent_subkey), list):
                    parent_item[parent_subkey].append(new_item)

            item_stack.append((indent, new_item, sublist_key))

        elif ':' in stripped:
            k, _, v = stripped.partition(':')
            k = k.strip()
            v = v.strip()

            while item_stack and item_stack[-1][0] >= indent:
                item_stack.pop()

            if item_stack:
                _, current_item, _ = item_stack[-1]
                item_stack.pop()
                if v == '':
                    current_item[k] = []
                    item_stack.append((indent - 2, current_item, k))
                else:
                    current_item[k] = parse_value(v)
                    item_stack.append((indent - 2, current_item, None))

    return items


def parse_yaif(text):
    # NOTE: strip_comment is intentionally NOT applied to block scalar lines —
    # those are collected raw inside parse_dict. We pass raw lines to sections
    # but still strip comments from header/key lines.
    raw_lines  = text.splitlines()
    # We need both: stripped (for section detection) and raw (for parse_dict
    # so block scalar bodies aren't mangled). We tag section boundaries using
    # stripped lines, but hand raw lines to parsers.
    result = {}

    sections = []
    current_path = None
    current_lines = []

    for raw_line in raw_lines:
        stripped = strip_comment(raw_line).strip()
        if stripped.startswith('[') and stripped.endswith(']') and stripped:
            if current_path is not None:
                sections.append((current_path, current_lines))
            current_path = stripped[1:-1]
            current_lines = []
        elif current_path is not None:
            # For dict parsing we need the raw line (preserves indentation
            # in block scalars). Comment-strip the line but keep indent.
            current_lines.append(strip_comment(raw_line))

    if current_path is not None:
        sections.append((current_path, current_lines))

    for path, body_lines in sections:
        body = [l for l in body_lines if l.strip()]
        if not body:
            data = {}
        elif body[0].strip().startswith('- '):
            data = parse_list(body)
        else:
            data = parse_dict(body_lines)  # pass ALL lines (inc. blank) so block scalar indent detection works

        parts = path.split('.')
        node = result
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = data

    return result


# ─── Shared Helpers ───────────────────────────────────────────────────────────

def truncate(text, limit):
    """Truncate to limit chars, breaking at a word boundary, appending ellipsis."""
    if not text or len(text) <= limit:
        return text
    truncated = text[:limit - 1]
    last_space = truncated.rfind(' ')
    if last_space > limit * 0.7:
        truncated = truncated[:last_space]
    return truncated.strip() + '…'


def hex_to_int(hex_str):
    """Convert '#RRGGBB' or 'RRGGBB' to a Discord colour integer."""
    h = str(hex_str).strip().lstrip('#')
    try:
        return int(h, 16)
    except ValueError:
        return 0x5865F2  # Discord blurple fallback