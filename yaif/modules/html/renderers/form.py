"""
yaif/modules/html/renderers/form.py

Renders a [page type: form] into an HTML <section>.

Supported field types
---------------------
text        plain text input
email       email input
password    password input
number      numeric input  (min, max, step supported)
date        date picker
time        time picker
datetime    datetime-local picker
select      dropdown       (options: A, B, C  or  A=a, B=b)
textarea    multi-line     (rows: N)
toggle      checkbox rendered as a toggle switch
color       colour swatch picker
file        file upload
range       slider         (min, max, step, value)
hidden      not rendered

Field properties
----------------
label       Human-readable label (defaults to name with _ → space, title-cased)
type        (see above, default: text)
placeholder Input placeholder string
hint        Small helper text shown below input
value       Default / pre-filled value
options     Comma-separated list for select, e.g. "Red, Blue" or "Red=red, Blue=blue"
min         min attribute (number / range)
max         max attribute (number / range)
step        step attribute (number / range)
rows        textarea row count (default 4)
wide        true → field spans full row width
readonly    true → disabled input
required    true → required marker (*) shown
"""

from __future__ import annotations
import html as _h
import re


def _esc(s) -> str:
    return _h.escape(str(s)) if s is not None else ''


def _label(field: dict) -> str:
    return str(field.get('label') or field['name'].replace('_', ' ').title())


def _parse_options(raw: str) -> list[tuple[str, str]]:
    """
    Parse "Red, Green=green, Blue" into [(label, value), ...].
    If no explicit value, value = label.
    """
    pairs = []
    for tok in re.split(r',\s*', raw.strip()):
        tok = tok.strip()
        if '=' in tok:
            lbl, _, val = tok.partition('=')
            pairs.append((_h.escape(lbl.strip()), _h.escape(val.strip())))
        else:
            pairs.append((_h.escape(tok), _h.escape(tok)))
    return pairs


def _render_field(field: dict) -> str:
    ftype    = str(field.get('type', 'text')).lower()
    if ftype == 'hidden':
        return ''

    name     = field['name']
    fid      = f'f_{name}'
    label    = _esc(_label(field))
    ph       = _esc(field.get('placeholder', ''))
    hint     = _esc(field.get('hint', ''))
    value    = _esc(field.get('value', ''))
    readonly = field.get('readonly', False)
    required = field.get('required', False)
    wide     = field.get('wide', False)

    ro_attr  = 'disabled' if readonly else ''
    req_mark = ' <span class="req" aria-hidden="true">*</span>' if required else ''
    wide_cls = 'field-wide' if wide else ''

    # ── toggle ────────────────────────────────────────────────────────────────
    if ftype == 'toggle':
        checked = 'checked' if str(field.get('value', '')).lower() == 'true' else ''
        return f'''
      <div class="field {wide_cls}">
        <div class="toggle-row">
          <label class="field-label" for="{fid}">{label}{req_mark}</label>
          <label class="toggle" aria-label="{label}">
            <input type="checkbox" id="{fid}" name="{name}" {checked} {ro_attr}>
            <span class="knob"></span>
          </label>
        </div>
        {f'<p class="hint">{hint}</p>' if hint else ''}
      </div>'''

    # ── select ────────────────────────────────────────────────────────────────
    if ftype == 'select':
        raw_opts = str(field.get('options', ''))
        pairs    = _parse_options(raw_opts) if raw_opts else []
        opts_html = ''
        for lbl, val in pairs:
            sel = 'selected' if val == value or lbl == value else ''
            opts_html += f'<option value="{val}" {sel}>{lbl}</option>\n'
        return f'''
      <div class="field {wide_cls}">
        <label class="field-label" for="{fid}">{label}{req_mark}</label>
        <div class="select-wrap">
          <select id="{fid}" name="{name}" {ro_attr}>
            {opts_html}
          </select>
          <span class="chevron" aria-hidden="true">&#8964;</span>
        </div>
        {f'<p class="hint">{hint}</p>' if hint else ''}
      </div>'''

    # ── textarea ──────────────────────────────────────────────────────────────
    if ftype == 'textarea':
        rows = int(field.get('rows', 4))
        return f'''
      <div class="field {wide_cls}">
        <label class="field-label" for="{fid}">{label}{req_mark}</label>
        <textarea id="{fid}" name="{name}" rows="{rows}"
                  placeholder="{ph}" {ro_attr}>{value}</textarea>
        {f'<p class="hint">{hint}</p>' if hint else ''}
      </div>'''

    # ── range ─────────────────────────────────────────────────────────────────
    if ftype == 'range':
        mn   = field.get('min', 0)
        mx   = field.get('max', 100)
        step = field.get('step', 1)
        val  = field.get('value', mn)
        return f'''
      <div class="field {wide_cls}">
        <div class="range-row">
          <label class="field-label" for="{fid}">{label}{req_mark}</label>
          <output class="range-val" id="{fid}_out">{val}</output>
        </div>
        <input type="range" id="{fid}" name="{name}"
               min="{mn}" max="{mx}" step="{step}" value="{val}" {ro_attr}
               oninput="document.getElementById('{fid}_out').value=this.value">
        {f'<p class="hint">{hint}</p>' if hint else ''}
      </div>'''

    # ── color ─────────────────────────────────────────────────────────────────
    if ftype == 'color':
        col_val = value or '#000000'
        return f'''
      <div class="field {wide_cls}">
        <label class="field-label" for="{fid}">{label}{req_mark}</label>
        <div class="color-wrap">
          <input type="color" id="{fid}" name="{name}" value="{col_val}" {ro_attr}>
          <span class="color-val">{col_val}</span>
        </div>
        {f'<p class="hint">{hint}</p>' if hint else ''}
      </div>'''

    # ── file ──────────────────────────────────────────────────────────────────
    if ftype == 'file':
        return f'''
      <div class="field {wide_cls}">
        <label class="field-label" for="{fid}">{label}{req_mark}</label>
        <label class="file-drop" for="{fid}">
          <span class="file-icon">&#128194;</span>
          <span class="file-text">{ph or 'Choose a file or drag & drop'}</span>
          <input type="file" id="{fid}" name="{name}" class="sr-only" {ro_attr}>
        </label>
        {f'<p class="hint">{hint}</p>' if hint else ''}
      </div>'''

    # ── all remaining input types ─────────────────────────────────────────────
    html_type_map = {
        'text':     'text',
        'email':    'email',
        'password': 'password',
        'number':   'number',
        'date':     'date',
        'time':     'time',
        'datetime': 'datetime-local',
    }
    html_type = html_type_map.get(ftype, 'text')

    extras = ''
    if ftype in ('number', 'range'):
        if 'min'  in field: extras += f' min="{field["min"]}"'
        if 'max'  in field: extras += f' max="{field["max"]}"'
        if 'step' in field: extras += f' step="{field["step"]}"'

    return f'''
      <div class="field {wide_cls}">
        <label class="field-label" for="{fid}">{label}{req_mark}</label>
        <input type="{html_type}" id="{fid}" name="{name}"
               placeholder="{ph}" value="{value}" {extras} {ro_attr}>
        {f'<p class="hint">{hint}</p>' if hint else ''}
      </div>'''


def render(page: dict) -> str:
    props    = page.get('props', {})
    title    = _esc(props.get('title', page['name'].replace('_', ' ')))
    subtitle = _esc(props.get('subtitle', ''))
    submit   = _esc(props.get('submit', 'Submit'))
    fields   = page.get('fields', [])

    fields_html = ''.join(_render_field(f) for f in fields)

    return f'''
  <section class="page page-form" id="page-{_esc(page['name'])}">
    <div class="page-header">
      <div>
        <h2 class="page-title">{title}</h2>
        {f'<p class="page-sub">{subtitle}</p>' if subtitle else ''}
      </div>
    </div>
    <form class="form-grid" novalidate>
      {fields_html}
      <div class="field-wide form-actions">
        <button type="submit" class="btn-primary">{submit}</button>
      </div>
    </form>
  </section>'''