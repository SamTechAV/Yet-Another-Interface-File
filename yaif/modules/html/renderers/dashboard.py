"""
yaif/modules/html/renderers/dashboard.py

Renders a [page type: dashboard] into an HTML <section>.

Page props
----------
title       Page heading
subtitle    Optional subheading
columns     Number of stat card columns (default 3)

[stat]
  label       Card label / metric name
  value       Big display number / text  e.g. "$12,400"
  delta       Change indicator e.g. "+8.2%" or "-3 users"
  delta_up    true = green (positive), false = red (negative)  (default true)
  icon        Emoji or short text shown in corner  e.g. "📈"
  wide        true → spans 2 columns
"""

from __future__ import annotations
import html as _h


def _esc(s) -> str:
    return _h.escape(str(s)) if s is not None else ''


def _render_stat(stat: dict) -> str:
    label    = _esc(stat.get('label', '—'))
    value    = _esc(stat.get('value', '—'))
    delta    = _esc(stat.get('delta', ''))
    delta_up = stat.get('delta_up', True)
    icon     = _esc(stat.get('icon', ''))
    wide     = stat.get('wide', False)

    delta_cls = 'delta-up' if delta_up else 'delta-down'
    delta_arrow = '▲' if delta_up else '▼'

    wide_cls = 'stat-wide' if wide else ''

    delta_html = ''
    if delta:
        delta_html = (
            f'<div class="stat-delta {delta_cls}">'
            f'<span class="arrow">{delta_arrow}</span> {delta}'
            f'</div>'
        )

    icon_html = f'<div class="stat-icon" aria-hidden="true">{icon}</div>' if icon else ''

    return f'''
      <div class="stat-card {wide_cls}">
        <div class="stat-top">
          <span class="stat-label">{label}</span>
          {icon_html}
        </div>
        <div class="stat-value">{value}</div>
        {delta_html}
      </div>'''


def render(page: dict) -> str:
    props    = page.get('props', {})
    title    = _esc(props.get('title', page['name'].replace('_', ' ')))
    subtitle = _esc(props.get('subtitle', ''))
    columns  = int(props.get('columns', 3))
    stats    = page.get('stats', [])

    stats_html = ''.join(_render_stat(s) for s in stats)

    if not stats_html:
        stats_html = '<p class="empty-state">No stats defined.</p>'

    return f'''
  <section class="page page-dashboard" id="page-{_esc(page['name'])}">
    <div class="page-header">
      <div>
        <h2 class="page-title">{title}</h2>
        {f'<p class="page-sub">{subtitle}</p>' if subtitle else ''}
      </div>
    </div>
    <div class="stat-grid" style="--cols:{columns}">
      {stats_html}
    </div>
  </section>'''