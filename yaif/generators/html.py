"""
HTML GUI generator for YAIF.
Generates a self-contained CRUD prototype from .yaif definitions.

All visual configuration (colors, fonts, app title, etc.) comes from the
[config] block in the .yaif file. Field annotations (@label, @placeholder,
@hint, @hidden, @readonly, @wide, @rows, @group, @order) drive form behavior.

Run with: python -m yaif example.yaif -t html -o output.html
"""

import json
from .base import BaseGenerator
from ..models import YAIFInterface, YAIFEnum, YAIFConfig


def _is_optional(type_str: str) -> bool:
    return type_str.lower().startswith("optional[")


def _unwrap(type_str: str) -> str:
    if _is_optional(type_str):
        return type_str[9:-1]
    return type_str


def _get_all_fields(iface: YAIFInterface, iface_map: dict) -> list[dict]:
    """Resolve all fields including inherited ones, flattened."""
    parent_fields = []
    if iface.parent and iface.parent in iface_map:
        parent_fields = [
            {**f, "inherited": True}
            for f in _get_all_fields(iface_map[iface.parent], iface_map)
        ]
    own_fields = [
        {
            "name":        f.name,
            "type_str":    _unwrap(f.type_str),
            "optional":    _is_optional(f.type_str),
            "default":     f.default,
            "inherited":   False,
            # annotations
            "label":       f.ann("label", ""),
            "placeholder": f.ann("placeholder", ""),
            "hint":        f.ann("hint", ""),
            "hidden":      bool(f.ann("hidden", False)),
            "readonly":    bool(f.ann("readonly", False)),
            "wide":        bool(f.ann("wide", False)),
            "rows":        f.ann("rows", ""),
            "group":       f.ann("group", ""),
            "order":       f.ann("order", ""),
        }
        for f in iface.fields
    ]

    all_fields = parent_fields + own_fields

    # Sort by @order if any field has it (stable sort so unordered fields keep position)
    def sort_key(f):
        o = f.get("order", "")
        try:
            return (0, int(o))
        except (TypeError, ValueError):
            return (1, 0)

    all_fields.sort(key=sort_key)
    return all_fields


class HTMLGenerator(BaseGenerator):
    """Generates a self-contained HTML CRUD prototype from YAIF definitions."""

    def generate(
        self,
        interfaces: list[YAIFInterface],
        enums: list[YAIFEnum],
        config: YAIFConfig,
    ) -> str:
        iface_map = {i.name: i for i in interfaces}
        enum_map  = {e.name: e.values for e in enums}

        iface_data = [
            {"name": i.name, "fields": _get_all_fields(i, iface_map)}
            for i in interfaces
        ]

        schema = json.dumps({"interfaces": iface_data, "enums": enum_map}, indent=2)

        # Build CSS variables from config — generators do zero styling themselves
        css_vars = _build_css_vars(config)

        # Google Fonts — build from config or use defaults
        font_url = config.get("font_url", "")
        if not font_url:
            font_url = (
                "https://fonts.googleapis.com/css2?"
                "family=DM+Mono:ital,wght@0,400;0,500;1,400"
                "&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,400"
                "&display=swap"
            )

        return (
            HTML_TEMPLATE
            .replace("__SCHEMA__",   schema)
            .replace("__CSS_VARS__", css_vars)
            .replace("__FONT_URL__", font_url)
            .replace("__TITLE__",    config.title)
        )


def _build_css_vars(c: YAIFConfig) -> str:
    """Turn config values into CSS custom properties — single line, no extra whitespace."""
    pairs = [
        ("--ink",     c.ink),
        ("--paper",   c.background),
        ("--cream",   c.cream),
        ("--line",    c.line),
        ("--accent",  c.accent),
        ("--accent2", c.accent2),
        ("--muted",   c.muted),
        ("--surface", c.surface),
        ("--mono",    c.mono),
        ("--serif",   c.font),
    ]
    return "".join(f"{k}:{v};" for k, v in pairs)


# ── HTML template ────────────────────────────────────────────────────────────
# __CSS_VARS__, __FONT_URL__, __TITLE__, __SCHEMA__ are replaced at generation time.

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<link href="__FONT_URL__" rel="stylesheet">
<style>
:root{__CSS_VARS__}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--paper);color:var(--ink);font-family:var(--serif);min-height:100vh;display:flex;flex-direction:column;}
.topbar{background:var(--ink);color:var(--paper);display:flex;align-items:center;padding:0 24px;height:52px;gap:20px;flex-shrink:0;}
.topbar-logo{font-family:var(--serif);font-size:1.3rem;font-weight:700;font-style:italic;color:#f5c17a;}
.topbar-sep{width:1px;height:22px;background:#ffffff30;}
.topbar-hint{font-family:var(--mono);font-size:0.65rem;color:#ffffff60;}
.topbar-actions{margin-left:auto;display:flex;gap:8px;}
.btn{font-family:var(--mono);font-size:0.72rem;padding:6px 14px;border:none;cursor:pointer;border-radius:2px;transition:all 0.15s;font-weight:500;}
.btn-primary{background:#f5c17a;color:var(--ink);}.btn-primary:hover{background:#f7cc90;}
.btn-ghost{background:transparent;color:#ffffff90;border:1px solid #ffffff30;}.btn-ghost:hover{background:#ffffff15;color:#fff;}
.btn-dark{background:transparent;color:var(--muted);border:1px solid var(--line);}.btn-dark:hover{background:var(--cream);color:var(--ink);}
.btn-danger{background:var(--accent);color:#fff;}.btn-danger:hover{filter:brightness(1.1);}
.btn-sm{padding:4px 10px;font-size:0.65rem;}
.app-nav{background:var(--ink);display:flex;align-items:center;overflow-x:auto;flex-shrink:0;}
.nav-tab{padding:10px 20px;font-family:var(--mono);font-size:0.72rem;cursor:pointer;white-space:nowrap;color:#ffffff70;border-right:1px solid #ffffff15;transition:all 0.15s;}
.nav-tab:hover{background:#ffffff15;color:#fff;}.nav-tab.active{background:var(--paper);color:var(--ink);font-weight:500;}
.app-content{flex:1;overflow-y:auto;padding:28px 32px;}
.iface-view{display:none;flex-direction:column;gap:24px;}.iface-view.active{display:flex;}
.section-card{background:var(--surface);border:1.5px solid var(--line);border-radius:3px;}
.section-card-head{padding:12px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;}
.section-card-title{font-family:var(--serif);font-size:1rem;font-weight:700;}
.section-card-body{padding:20px 18px;}
.group-label{grid-column:1/-1;font-family:var(--mono);font-size:0.62rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:6px;margin-top:8px;}
.form-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px 20px;}
.form-group{display:flex;flex-direction:column;gap:5px;}.form-group.full-width{grid-column:1/-1;}
label{font-family:var(--mono);font-size:0.65rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);}
.field-hint{font-family:var(--mono);font-size:0.62rem;color:var(--muted);margin-top:2px;font-style:italic;}
.req{color:var(--accent);margin-left:2px;}.opt-tag,.inh-tag{font-size:0.58rem;background:var(--cream);padding:1px 5px;border-radius:2px;color:var(--muted);margin-left:4px;}
input[type=text],input[type=number],textarea.field-ta,select{background:var(--paper);border:1.5px solid var(--line);border-radius:2px;padding:8px 10px;font-family:var(--mono);font-size:0.78rem;color:var(--ink);outline:none;transition:border-color 0.15s;width:100%;}
input:focus,textarea.field-ta:focus,select:focus{border-color:var(--accent2);}
input:disabled,textarea.field-ta:disabled,select:disabled{opacity:0.5;cursor:not-allowed;}
textarea.field-ta{resize:vertical;min-height:80px;}
.checkbox-row{display:flex;align-items:center;gap:8px;}
input[type=checkbox]{width:16px;height:16px;accent-color:var(--accent2);cursor:pointer;}
.checkbox-label{font-family:var(--mono);font-size:0.75rem;cursor:pointer;}
.list-field{display:flex;flex-direction:column;gap:6px;}
.list-item{display:flex;align-items:center;gap:6px;}.list-item input,.list-item select{flex:1;}
.list-remove{background:none;border:1px solid var(--line);color:var(--accent);cursor:pointer;border-radius:2px;width:26px;height:26px;font-size:0.9rem;flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:all 0.1s;}.list-remove:hover{background:var(--accent);color:#fff;}
.list-add{background:none;border:1.5px dashed var(--line);color:var(--muted);cursor:pointer;border-radius:2px;padding:5px 10px;font-family:var(--mono);font-size:0.68rem;transition:all 0.15s;text-align:left;}.list-add:hover{border-color:var(--accent2);color:var(--accent2);}
.nested-field{border:1.5px solid var(--line);border-radius:3px;background:var(--cream);}
.nested-head{padding:7px 12px;font-family:var(--mono);font-size:0.65rem;color:var(--muted);border-bottom:1px solid var(--line);text-transform:uppercase;letter-spacing:1px;}
.nested-body{padding:14px 12px;}
.form-actions{display:flex;gap:10px;margin-top:18px;justify-content:flex-end;}
.table-wrap{overflow-x:auto;}
table.records{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:0.72rem;}
table.records th{text-align:left;padding:8px 12px;border-bottom:2px solid var(--ink);font-size:0.62rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);white-space:nowrap;}
table.records td{padding:9px 12px;border-bottom:1px solid var(--line);max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
table.records tr:hover td{background:var(--cream);}
.td-actions{display:flex;gap:5px;white-space:nowrap;}
.no-records{text-align:center;color:var(--muted);font-family:var(--mono);font-size:0.75rem;padding:28px 0;}
.modal-backdrop{display:none;position:fixed;inset:0;background:#00000060;z-index:100;align-items:center;justify-content:center;}.modal-backdrop.open{display:flex;}
.modal{background:var(--paper);border:2px solid var(--ink);border-radius:4px;width:min(640px,90vw);max-height:80vh;display:flex;flex-direction:column;box-shadow:8px 8px 0 var(--ink);}
.modal-head{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;}
.modal-title{font-weight:700;font-size:1rem;}
.modal-close{background:none;border:none;font-size:1.2rem;cursor:pointer;color:var(--muted);padding:2px 6px;border-radius:2px;}.modal-close:hover{background:var(--cream);}
.modal-body{flex:1;overflow-y:auto;padding:18px;}
pre.json-out{font-family:var(--mono);font-size:0.72rem;line-height:1.6;background:var(--ink);color:#a8d8b0;padding:18px;border-radius:3px;overflow-x:auto;white-space:pre;}
.modal-foot{padding:12px 18px;border-top:1px solid var(--line);display:flex;gap:8px;justify-content:flex-end;}
.toast{position:fixed;bottom:24px;right:24px;background:var(--ink);color:var(--paper);font-family:var(--mono);font-size:0.72rem;padding:10px 18px;border-radius:3px;transform:translateY(60px);opacity:0;transition:all 0.25s;z-index:200;pointer-events:none;}.toast.show{transform:translateY(0);opacity:1;}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
.iface-view.active>*{animation:fadeIn 0.2s ease both;}.iface-view.active>*:nth-child(2){animation-delay:0.05s;}
</style>
</head>
<body>
<div class="topbar">
  <span class="topbar-logo">__TITLE__</span>
  <div class="topbar-sep"></div>
  <span class="topbar-hint" id="topbar-hint">GUI Prototype</span>
  <div class="topbar-actions">
    <button class="btn btn-ghost btn-sm" onclick="clearAll()">Clear records</button>
    <button class="btn btn-primary btn-sm" onclick="exportAllJSON()">Export all JSON</button>
  </div>
</div>
<div style="display:flex;flex-direction:column;flex:1;overflow:hidden;height:calc(100vh - 52px);">
  <div class="app-nav" id="app-nav"></div>
  <div class="app-content" id="app-content"></div>
</div>
<div class="modal-backdrop" id="json-modal">
  <div class="modal">
    <div class="modal-head">
      <span class="modal-title">JSON Output</span>
      <button class="modal-close" onclick="closeModal()">&#x2715;</button>
    </div>
    <div class="modal-body"><pre class="json-out" id="json-out"></pre></div>
    <div class="modal-foot">
      <button class="btn btn-dark btn-sm" onclick="closeModal()">Close</button>
      <button class="btn btn-primary btn-sm" onclick="copyJSON()">Copy JSON</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
const SCHEMA = __SCHEMA__;
const records = {};
const editingIdx = {};
let activeIface = null;

(function init() {
  const names = SCHEMA.interfaces.map(i => i.name);
  names.forEach(n => { records[n] = []; editingIdx[n] = null; });
  document.getElementById('topbar-hint').textContent =
    names.length + ' interface' + (names.length !== 1 ? 's' : '');
  const nav = document.getElementById('app-nav');
  nav.innerHTML = names.map((n,i) =>
    `<div class="nav-tab${i===0?' active':''}" data-iface="${n}" onclick="switchIface('${n}')">${n}</div>`
  ).join('');
  document.getElementById('app-content').innerHTML = SCHEMA.interfaces.map(buildView).join('');
  activeIface = names[0];
  if (activeIface) document.querySelector(`.iface-view[data-iface="${activeIface}"]`).classList.add('active');
})();

function switchIface(name) {
  activeIface = name;
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.iface === name));
  document.querySelectorAll('.iface-view').forEach(v => v.classList.toggle('active', v.dataset.iface === name));
}

function buildView(iface) {
  return `<div class="iface-view" data-iface="${iface.name}">
    <div class="section-card">
      <div class="section-card-head">
        <span class="section-card-title">${iface.name}</span>
        <span style="font-family:var(--mono);font-size:0.65rem;color:var(--muted)" id="rec-count-${iface.name}">0 records</span>
      </div>
      <div class="section-card-body">
        <div class="form-grid">${buildFields(iface.fields,'')}</div>
        <div class="form-actions">
          <button class="btn btn-dark btn-sm" onclick="cancelEdit('${iface.name}')">Cancel</button>
          <button class="btn btn-primary" id="submit-btn-${iface.name}" onclick="submitForm('${iface.name}')">Add Record</button>
        </div>
      </div>
    </div>
    <div class="section-card">
      <div class="section-card-head">
        <span class="section-card-title">Records</span>
        <button class="btn btn-dark btn-sm" onclick="viewJSON('${iface.name}')">View JSON</button>
      </div>
      <div class="section-card-body" style="padding:0">
        <div class="table-wrap">
          <table class="records">
            <thead><tr id="thead-${iface.name}"></tr></thead>
            <tbody id="tbody-${iface.name}"><tr><td colspan="99" class="no-records">No records yet. Fill the form above.</td></tr></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>`;
}

function fid(prefix, name) { return ('field-'+prefix+name).replace(/[^a-zA-Z0-9_-]/g,'_'); }

function buildFields(fields, prefix) {
  // Inject group headers when group label changes
  let lastGroup = null;
  const parts = [];
  for (const f of fields) {
    if (f.hidden) continue;
    const g = f.group || '';
    if (g && g !== lastGroup) {
      parts.push(`<div class="group-label">${g}</div>`);
      lastGroup = g;
    }
    parts.push(buildField(f, prefix));
  }
  return parts.join('');
}

function buildField(f, prefix) {
  const id   = fid(prefix, f.name);
  const t    = f.type_str;
  const inh  = f.inherited ? '<span class="inh-tag">inherited</span>' : '';
  const mark = f.optional ? '<span class="opt-tag">optional</span>' : '<span class="req">*</span>';
  const displayLabel = f.label || f.name;
  const lbl  = `<label for="${id}">${displayLabel}${mark}${inh}</label>`;
  const hint = f.hint ? `<span class="field-hint">${f.hint}</span>` : '';
  const ph   = f.placeholder || f.name;
  const ro   = f.readonly ? ' disabled' : '';

  const longText  = f.rows || ['body','content','bio','description','text','notes'].includes(f.name);
  const fullWidth = f.wide || longText || t.startsWith('list[') || t.startsWith('dict[') || ifaceExists(t);
  const wClass    = fullWidth ? ' full-width' : '';

  if (t === 'bool') {
    return `<div class="form-group${wClass}">
      ${lbl}<div class="checkbox-row">
        <input type="checkbox" id="${id}"${f.default==='true'?' checked':''}${ro}>
        <label class="checkbox-label" for="${id}" style="text-transform:none;letter-spacing:0;font-size:0.78rem;">${displayLabel}</label>
      </div>${hint}</div>`;
  }
  if (enumExists(t)) {
    const opts = (f.optional?['']:[] ).concat(SCHEMA.enums[t]||[]);
    return `<div class="form-group${wClass}">
      ${lbl}<select id="${id}"${ro}>${opts.map(v=>`<option value="${v}">${v||'&#8212; none &#8212;'}</option>`).join('')}</select>${hint}</div>`;
  }
  if (t==='int'||t==='float') {
    return `<div class="form-group${wClass}">
      ${lbl}<input type="number" id="${id}" step="${t==='float'?'0.01':'1'}" value="${f.default??''}" placeholder="0"${ro}>${hint}</div>`;
  }
  if (ifaceExists(t)) {
    const nested = SCHEMA.interfaces.find(i=>i.name===t);
    return `<div class="form-group full-width">
      ${lbl}<div class="nested-field">
        <div class="nested-head">${t}</div>
        <div class="nested-body"><div class="form-grid">${buildFields(nested.fields, prefix+f.name+'.')}</div></div>
      </div>${hint}</div>`;
  }
  if (t.startsWith('list[')) {
    const inner = t.replace(/^list\[(.+)\]$/,'$1');
    return `<div class="form-group full-width">
      ${lbl}<div class="list-field">
        <div class="list-items" id="li-${id}"></div>
        <button class="list-add" onclick="addListItem('${id}','${inner}')">+ Add item</button>
      </div>${hint}</div>`;
  }
  if (t.startsWith('dict[')) {
    return `<div class="form-group full-width">
      ${lbl}<div class="list-field">
        <div class="list-items" id="li-${id}"></div>
        <button class="list-add" onclick="addDictItem('${id}')">+ Add key/value</button>
      </div>${hint}</div>`;
  }
  if (longText) {
    const rows = f.rows ? ` rows="${f.rows}"` : '';
    return `<div class="form-group full-width">
      ${lbl}<textarea class="field-ta" id="${id}" placeholder="${ph}..."${rows}${ro}></textarea>${hint}</div>`;
  }
  return `<div class="form-group${wClass}">
    ${lbl}<input type="text" id="${id}" value="${f.default??''}" placeholder="${ph}"${ro}>${hint}</div>`;
}

function enumExists(t) { return Object.prototype.hasOwnProperty.call(SCHEMA.enums, t); }
function ifaceExists(t) { return SCHEMA.interfaces.some(i=>i.name===t); }

function addListItem(listId, inner) {
  const c = document.getElementById('li-'+listId);
  const idx = c.children.length;
  const div = document.createElement('div'); div.className='list-item';
  let inp = enumExists(inner)
    ? `<select id="${listId}-i-${idx}">${(SCHEMA.enums[inner]||[]).map(v=>`<option>${v}</option>`).join('')}</select>`
    : (inner==='int'||inner==='float')
      ? `<input type="number" id="${listId}-i-${idx}" step="${inner==='float'?'0.01':'1'}" placeholder="0">`
      : `<input type="text" id="${listId}-i-${idx}" placeholder="value">`;
  div.innerHTML = inp + `<button class="list-remove" onclick="this.parentElement.remove()">&#xd7;</button>`;
  c.appendChild(div);
}

function addDictItem(listId) {
  const c = document.getElementById('li-'+listId);
  const idx = c.children.length;
  const div = document.createElement('div'); div.className='list-item';
  div.innerHTML = `<input type="text" id="${listId}-k-${idx}" placeholder="key" style="flex:0.4">
    <input type="text" id="${listId}-v-${idx}" placeholder="value" style="flex:0.6">
    <button class="list-remove" onclick="this.parentElement.remove()">&#xd7;</button>`;
  c.appendChild(div);
}

function collectFields(fields, prefix) {
  const obj = {};
  for (const f of fields) {
    if (f.hidden) continue;
    const id = fid(prefix, f.name);
    const t  = f.type_str;
    if (t==='bool') { obj[f.name] = document.getElementById(id)?.checked??false; }
    else if (enumExists(t)) { obj[f.name] = document.getElementById(id)?.value||null; }
    else if (t==='int')   { const v=document.getElementById(id)?.value; obj[f.name]=v!=null&&v!==''?parseInt(v):null; }
    else if (t==='float') { const v=document.getElementById(id)?.value; obj[f.name]=v!=null&&v!==''?parseFloat(v):null; }
    else if (ifaceExists(t)) {
      const nested=SCHEMA.interfaces.find(i=>i.name===t);
      obj[f.name]=collectFields(nested.fields, prefix+f.name+'.');
    }
    else if (t.startsWith('list[')) {
      const inner=t.replace(/^list\[(.+)\]$/,'$1');
      const c=document.getElementById('li-'+id); const items=[];
      if(c) c.querySelectorAll('.list-item').forEach((_,i)=>{
        const inp=c.children[i]?.querySelector(`[id$="-i-${i}"]`);
        if(inp){ const v=inp.value; items.push(inner==='int'?parseInt(v):inner==='float'?parseFloat(v):v); }
      });
      obj[f.name]=items;
    }
    else if (t.startsWith('dict[')) {
      const c=document.getElementById('li-'+id); const dict={};
      if(c) c.querySelectorAll('.list-item').forEach((_,i)=>{
        const k=c.children[i]?.querySelector(`[id$="-k-${i}"]`)?.value;
        const v=c.children[i]?.querySelector(`[id$="-v-${i}"]`)?.value;
        if(k) dict[k]=v;
      });
      obj[f.name]=dict;
    }
    else { obj[f.name]=document.getElementById(id)?.value??''; }
  }
  return obj;
}

function submitForm(name) {
  const iface=SCHEMA.interfaces.find(i=>i.name===name);
  const obj=collectFields(iface.fields,'');
  const idx=editingIdx[name];
  if(idx!==null){ records[name][idx]=obj; editingIdx[name]=null; document.getElementById('submit-btn-'+name).textContent='Add Record'; }
  else { records[name].push(obj); }
  clearForm(name); refreshTable(name); toast('Record saved \u2713');
}

function cancelEdit(name) {
  editingIdx[name]=null; clearForm(name);
  document.getElementById('submit-btn-'+name).textContent='Add Record';
}

function clearForm(name) {
  const iface=SCHEMA.interfaces.find(i=>i.name===name);
  for(const f of iface.fields){
    const id=fid('',f.name); const el=document.getElementById(id);
    if(!el) continue;
    if(f.type_str==='bool') el.checked=f.default==='true';
    else if(el.tagName==='SELECT') el.selectedIndex=0;
    else el.value=f.default??'';
    const lc=document.getElementById('li-'+id); if(lc) lc.innerHTML='';
  }
}

function editRecord(name, idx) {
  editingIdx[name]=idx;
  const obj=records[name][idx];
  const iface=SCHEMA.interfaces.find(i=>i.name===name);
  function fill(fields,data,prefix){
    for(const f of fields){
      const id=fid(prefix,f.name); const val=data[f.name]; if(val==null) continue;
      const t=f.type_str;
      if(t==='bool'){const el=document.getElementById(id);if(el)el.checked=val;}
      else if(ifaceExists(t)){const n=SCHEMA.interfaces.find(i=>i.name===t);fill(n.fields,val,prefix+f.name+'.');}
      else if(t.startsWith('list[')){
        const inner=t.replace(/^list\[(.+)\]$/,'$1');
        const lc=document.getElementById('li-'+id);
        if(lc){lc.innerHTML='';(val||[]).forEach((v,i)=>{addListItem(id,inner);const inp=lc.children[i]?.querySelector(`[id$="-i-${i}"]`);if(inp)inp.value=v;});}
      }
      else if(t.startsWith('dict[')){
        const lc=document.getElementById('li-'+id);
        if(lc){lc.innerHTML='';Object.entries(val||{}).forEach(([k,v],i)=>{addDictItem(id);const ki=lc.children[i]?.querySelector(`[id$="-k-${i}"]`);const vi=lc.children[i]?.querySelector(`[id$="-v-${i}"]`);if(ki)ki.value=k;if(vi)vi.value=v;});}
      }
      else{const el=document.getElementById(id);if(el)el.value=val;}
    }
  }
  fill(iface.fields,obj,'');
  document.getElementById('submit-btn-'+name).textContent='Update Record';
  document.querySelector(`.iface-view[data-iface="${name}"] .section-card`).scrollIntoView({behavior:'smooth'});
}

function deleteRecord(name, idx) { records[name].splice(idx,1); refreshTable(name); toast('Record deleted'); }

function refreshTable(name) {
  const iface=SCHEMA.interfaces.find(i=>i.name===name);
  const recs=records[name];
  document.getElementById('rec-count-'+name).textContent=recs.length+' record'+(recs.length!==1?'s':'');
  const cols=iface.fields.filter(f=>!f.hidden&&!ifaceExists(f.type_str)&&!f.type_str.startsWith('list[')&&!f.type_str.startsWith('dict[')).slice(0,6);
  document.getElementById('thead-'+name).innerHTML=cols.map(f=>`<th>${f.label||f.name}</th>`).join('')+'<th></th>';
  if(!recs.length){
    document.getElementById('tbody-'+name).innerHTML=`<tr><td colspan="${cols.length+1}" class="no-records">No records yet.</td></tr>`;
    return;
  }
  document.getElementById('tbody-'+name).innerHTML=recs.map((r,i)=>{
    const cells=cols.map(f=>{let v=r[f.name];if(typeof v==='boolean')v=v?'\u2713':'\u2717';if(v==null)v='\u2014';return `<td title="${String(v)}">${String(v).slice(0,40)}</td>`;}).join('');
    return `<tr>${cells}<td class="td-actions">
      <button class="btn btn-dark btn-sm" onclick="editRecord('${name}',${i})">Edit</button>
      <button class="btn btn-danger btn-sm" onclick="deleteRecord('${name}',${i})">Del</button>
    </td></tr>`;
  }).join('');
}

function viewJSON(name){ document.getElementById('json-out').textContent=JSON.stringify(records[name],null,2); document.getElementById('json-modal').classList.add('open'); }
function exportAllJSON(){ const out={}; SCHEMA.interfaces.forEach(i=>{out[i.name]=records[i.name];}); document.getElementById('json-out').textContent=JSON.stringify(out,null,2); document.getElementById('json-modal').classList.add('open'); }
function closeModal(){ document.getElementById('json-modal').classList.remove('open'); }
function copyJSON(){ navigator.clipboard.writeText(document.getElementById('json-out').textContent); toast('Copied \u2713'); }
function clearAll(){ SCHEMA.interfaces.forEach(i=>{records[i.name]=[];refreshTable(i.name);}); toast('All records cleared'); }

let _tt;
function toast(msg){ const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); clearTimeout(_tt); _tt=setTimeout(()=>t.classList.remove('show'),2200); }
document.getElementById('json-modal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeModal();});
</script>
</body>
</html>"""