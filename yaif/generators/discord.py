"""
Discord generator - outputs copy-paste-ready Discord formatted text.

All output is wrapped in monospace code blocks so box-drawing characters
render perfectly. No output file needed; pipe straight to stdout.

Interface annotations that control Discord output:
    @discord=table      render records as a box-drawing table (default)
    @discord=kv         render as key: value pairs
    @discord=list       render as a bullet list
    @discord_title="My Title"   override the section header (default: interface name)
    @discord_icon="📊"          emoji prefix on the section header

Field annotations respected:
    @label="Name"       column/key header (falls back to field name)
    @hidden             skip field entirely
    @discord_width=12   force a minimum column width

Run with:
    python -m yaif myfile.yaif -t discord
"""

from .base import BaseGenerator
from ..models import YAIFInterface, YAIFEnum, YAIFConfig


# ── Box-drawing character sets ───────────────────────────────────────────────

BOX = {
    "tl": "╔",
    "tr": "╗",
    "bl": "╚",
    "br": "╝",
    "h": "═",
    "v": "║",
    "tee_d": "╦",
    "tee_u": "╩",
    "tee_r": "╠",
    "tee_l": "╣",
    "cross": "╬",
}

EMPTY = "-"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _label(f) -> str:
    """Display label for a field - @label annotation or field name."""
    return f.ann("label", "") or f.name


def _visible_fields(iface: YAIFInterface, inherited=True) -> list:
    """Fields that should appear in Discord output (not @hidden)."""
    fields = []
    # walk inheritance if needed
    if inherited and hasattr(iface, "_resolved_fields"):
        source = iface._resolved_fields
    else:
        source = iface.fields
    return [f for f in source if not f.ann("hidden", False)]


def _resolve_fields(iface: YAIFInterface, iface_map: dict) -> list:
    """Flatten inherited fields onto an interface."""
    parent_fields = []
    if iface.parent and iface.parent in iface_map:
        parent_fields = _resolve_fields(iface_map[iface.parent], iface_map)
    return parent_fields + list(iface.fields)


def _fmt_value(v) -> str:
    """Format a single cell value."""
    if v is None or v == "":
        return EMPTY
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, list):
        if not v:
            return EMPTY
        return ", ".join(str(x) for x in v)
    if isinstance(v, dict):
        if not v:
            return EMPTY
        return ", ".join(f"{k}: {val}" for k, val in v.items())
    return str(v)


# ── Table renderer ───────────────────────────────────────────────────────────


def _render_table(title: str, icon: str, fields: list, sample_rows: list) -> str:
    """
    Render a full box-drawing table.

    fields    - list of YAIFField
    sample_rows - list of dicts (field_name -> display string), used to size columns.
                  If empty, renders a header-only skeleton so you can see the shape.
    """
    labels = [_label(f) for f in fields]

    # Determine column widths - max of header length, min_width annotation, and any sample data
    col_widths = []
    for i, f in enumerate(fields):
        min_w = int(f.ann("discord_width", 0) or 0)
        w = max(len(labels[i]), min_w)
        for row in sample_rows:
            cell = _fmt_value(row.get(f.name))
            w = max(w, len(cell))
        col_widths.append(w + 2)  # +2 padding

    def pad(text, width):
        return f" {text:<{width - 1}}"

    def hline(left, mid, right, fill):
        return left + mid.join(fill * w for w in col_widths) + right

    lines = []

    # Section header above the box
    prefix = f"{icon} " if icon else ""
    lines.append(f"**{prefix}{title}**")
    lines.append("```")

    # Top border
    lines.append(hline(BOX["tl"], BOX["tee_d"], BOX["tr"], BOX["h"]))

    # Header row
    header_cells = (
        BOX["v"]
        + BOX["v"].join(pad(labels[i], col_widths[i]) for i in range(len(fields)))
        + BOX["v"]
    )
    lines.append(header_cells)

    # Header/body divider
    lines.append(hline(BOX["tee_r"], BOX["cross"], BOX["tee_l"], BOX["h"]))

    if sample_rows:
        for row in sample_rows:
            cells = (
                BOX["v"]
                + BOX["v"].join(
                    pad(_fmt_value(row.get(f.name)), col_widths[i])
                    for i, f in enumerate(fields)
                )
                + BOX["v"]
            )
            lines.append(cells)
    else:
        # Empty placeholder row
        empty_cells = (
            BOX["v"] + BOX["v"].join(pad(EMPTY, w) for w in col_widths) + BOX["v"]
        )
        lines.append(empty_cells)

    # Bottom border
    lines.append(hline(BOX["bl"], BOX["tee_u"], BOX["br"], BOX["h"]))
    lines.append("```")

    return "\n".join(lines)


# ── Key-value renderer ───────────────────────────────────────────────────────


def _render_kv(title: str, icon: str, fields: list, row: dict) -> str:
    """Render a single record as aligned key: value pairs."""
    prefix = f"{icon} " if icon else ""
    max_key = max((len(_label(f)) for f in fields), default=8)

    lines = []
    lines.append(f"**{prefix}{title}**")
    lines.append("```")
    for f in fields:
        key = _label(f)
        val = _fmt_value(row.get(f.name) if row else None)
        lines.append(f"{key:<{max_key}}  {val}")
    lines.append("```")
    return "\n".join(lines)


# ── List renderer ────────────────────────────────────────────────────────────


def _render_list(title: str, icon: str, fields: list, rows: list) -> str:
    """Render records as a bulleted list, primary field bolded."""
    prefix = f"{icon} " if icon else ""
    lines = []
    lines.append(f"**{prefix}{title}**")
    lines.append("```")

    if not rows:
        lines.append("  (no entries)")
    else:
        for row in rows:
            # First field is the "primary" - rest are secondary
            primary_val = _fmt_value(row.get(fields[0].name)) if fields else EMPTY
            rest = [f"{_label(f)}: {_fmt_value(row.get(f.name))}" for f in fields[1:]]
            if rest:
                lines.append(f"  • {primary_val}  -  {',  '.join(rest)}")
            else:
                lines.append(f"  • {primary_val}")

    lines.append("```")
    return "\n".join(lines)


# ── Enum renderer ────────────────────────────────────────────────────────────


def _render_enum(enum: YAIFEnum) -> str:
    """Render an enum as a compact inline block."""
    values = " │ ".join(enum.values)
    lines = [
        f"**{enum.name}**",
        "```",
        f"  {values}",
        "```",
    ]
    return "\n".join(lines)


# ── Main generator ───────────────────────────────────────────────────────────


class DiscordGenerator(BaseGenerator):
    """
    Generates Discord-ready copy-paste output from YAIF definitions.
    Uses box-drawing characters inside ``` code blocks for clean rendering.
    """

    def generate(
        self,
        interfaces: list[YAIFInterface],
        enums: list[YAIFEnum],
        config: YAIFConfig,
    ) -> str:
        iface_map = {i.name: i for i in interfaces}

        # Resolve inherited fields onto each interface
        for iface in interfaces:
            iface._resolved_fields = _resolve_fields(iface, iface_map)

        sections = []

        # App title from config
        if config.title:
            sections.append(f"# {config.title}")
            if config.description:
                sections.append(f"> {config.description}")
            sections.append("")

        # Enums section (if any)
        if enums:
            sections.append("**Enums**")
            for enum in enums:
                sections.append(_render_enum(enum))
            sections.append("")

        # Interfaces
        for iface in interfaces:
            fields = [f for f in iface._resolved_fields if not f.ann("hidden", False)]
            if not fields:
                continue

            discord_mode = (
                iface.fields[0].ann("discord", "table") if iface.fields else "table"
            )
            # Check if any field on the interface itself carries the discord mode annotation
            # (we store it as a special interface-level hint on the first non-inherited field)
            for f in iface.fields:
                mode_ann = f.ann("discord", None)
                if mode_ann:
                    discord_mode = mode_ann
                    break

            title = iface.fields[0].ann("discord_title", "") if iface.fields else ""
            icon = iface.fields[0].ann("discord_icon", "") if iface.fields else ""
            for f in iface.fields:
                if f.ann("discord_title", ""):
                    title = f.ann("discord_title", "")
                if f.ann("discord_icon", ""):
                    icon = f.ann("discord_icon", "")

            title = title or iface.name

            if discord_mode == "kv":
                sections.append(_render_kv(title, icon, fields, {}))
            elif discord_mode == "list":
                sections.append(_render_list(title, icon, fields, []))
            else:
                # Default: table
                # Build a sample row from field defaults so the table isn't just dashes
                sample = {}
                for f in fields:
                    if f.default:
                        sample[f.name] = f.default
                sections.append(
                    _render_table(
                        title, icon, fields, [sample] if any(sample.values()) else []
                    )
                )

            sections.append("")

        return "\n".join(sections).rstrip()
