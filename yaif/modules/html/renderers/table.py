"""
yaif/modules/html/renderers/table.py

Renders a [page type: table] into an HTML <section>.

Page props
----------
title       Page heading
subtitle    Optional subheading
striped     true → alternating row background (default false)
bordered    true → cell borders (default false)

[column ColName]
  label     Header display text (defaults to ColName)
  width     Suggested px width hint (rendered as inline style)

[row]
  ColName: value
  ...       One key-value pair per column

Row values support a simple badge syntax:
  status: published::badge-green
  status: draft::badge-yellow
  status: archived::badge-red
  status: pending::badge-blue
  status: default::badge      (grey)

The ::badge-COLOR suffix is stripped from display and used to apply
a colour class to a <span class="badge badge-COLOR"> wrapper.
"""

from __future__ import annotations
import html as _h
import re


def _esc(s) -> str:
    return _h.escape(str(s)) if s is not None else ''


_BADGE_RE = re.compile(r'^(.*?)::badge(-\w+)?$', re.I)

_BADGE_COLOURS = {
    '-green':  ('badge-green',  '#16a34a', '#dcfce7'),
    '-red':    ('badge-red',    '#dc2626', '#fee2e2'),
    '-yellow': ('badge-yellow', '#ca8a04', '#fef9c3'),
    '-blue':   ('badge-blue',   '#2563eb', '#dbeafe'),
    '-purple': ('badge-purple', '#7c3aed', '#ede9fe'),
    None:      ('badge-grey',   '#6b7280', '#f3f4f6'),
}


def _render_cell(raw_val) -> str:
    text = str(raw_val)
    m = _BADGE_RE.match(text)
    if m:
        label    = m.group(1).strip()
        colour   = (m.group(2) or '').lower() or None
        cls, fg, bg = _BADGE_COLOURS.get(colour, _BADGE_COLOURS[None])
        return (
            f'<span class="badge {cls}" '
            f'style="color:{fg};background:{bg}">'
            f'{_esc(label)}</span>'
        )
    return _esc(text)


def render(page: dict) -> str:
    props    = page.get('props', {})
    title    = _esc(props.get('title', page['name'].replace('_', ' ')))
    subtitle = _esc(props.get('subtitle', ''))
    striped  = props.get('striped', False)
    bordered = props.get('bordered', False)

    columns  = page.get('columns', [])
    rows     = page.get('rows',    [])

    # If no explicit [column] blocks, derive columns from row keys
    if not columns and rows:
        seen: list[str] = []
        for row in rows:
            for k in row:
                if k not in seen:
                    seen.append(k)
        columns = [{'name': k} for k in seen]

    # Table modifier classes
    tbl_cls = 'data-table'
    if striped:  tbl_cls += ' striped'
    if bordered: tbl_cls += ' bordered'

    # Header row
    thead_cells = ''
    for col in columns:
        label = _esc(col.get('label') or col['name'].replace('_', ' ').title())
        width = col.get('width')
        style = f' style="width:{width}px"' if width else ''
        thead_cells += f'<th{style}>{label}</th>\n'

    # Data rows
    tbody_rows = ''
    for row in rows:
        cells = ''
        for col in columns:
            val = row.get(col['name'], row.get(col.get('label', ''), ''))
            cells += f'<td>{_render_cell(val)}</td>\n'
        tbody_rows += f'<tr>{cells}</tr>\n'

    if not tbody_rows:
        colspan = len(columns) or 1
        tbody_rows = f'<tr><td colspan="{colspan}" class="empty-row">No data</td></tr>'

    return f'''
  <section class="page page-table" id="page-{_esc(page['name'])}">
    <div class="page-header">
      <div>
        <h2 class="page-title">{title}</h2>
        {f'<p class="page-sub">{subtitle}</p>' if subtitle else ''}
      </div>
    </div>
    <div class="table-wrap">
      <table class="{tbl_cls}">
        <thead>
          <tr>{thead_cells}</tr>
        </thead>
        <tbody>
          {tbody_rows}
        </tbody>
      </table>
    </div>
  </section>'''