"""
YAIF parser — reads .yaif source text and produces model objects.

Syntax additions in this version:
  [config]         — key: value pairs for theme / metadata / generator hints
  @annotation      — field-level hints, e.g. @label="Name" @hidden @rows=4
"""

import re
from pathlib import Path
from typing import Optional, Any

from .models import YAIFField, YAIFInterface, YAIFEnum, YAIFConfig


class YAIFParseError(Exception):
    """Raised when the parser hits invalid syntax."""
    def __init__(self, message: str, line_num: int = None):
        self.line_num = line_num
        prefix = f"Line {line_num}: " if line_num else ""
        super().__init__(f"{prefix}{message}")


# ── Annotation parsing ──────────────────────────────────────────────────────

# Matches:  @key  or  @key="value"  or  @key=42
_ANN_RE = re.compile(r'@(\w+)(?:=(?:"([^"]*)"|([\w.#-]+)))?')


def _parse_annotations(text: str) -> tuple[str, dict[str, Any]]:
    """
    Split a raw 'type_and_default_and_annotations' string into
    (clean_type_default, annotations_dict).

    Annotation formats:
        @hidden              → {"hidden": True}
        @label="My Label"    → {"label": "My Label"}
        @rows=5              → {"rows": "5"}   (strings; callers cast if needed)
    """
    annotations: dict[str, Any] = {}
    clean = text

    for m in _ANN_RE.finditer(text):
        key = m.group(1)
        quoted_val = m.group(2)   # inside "..."
        bare_val   = m.group(3)   # bare word / number
        if quoted_val is not None:
            annotations[key] = quoted_val
        elif bare_val is not None:
            annotations[key] = bare_val
        else:
            annotations[key] = True  # flag-style @hidden
        clean = clean.replace(m.group(0), "")

    return clean.strip(), annotations


# ── Main parser ─────────────────────────────────────────────────────────────

class YAIFParser:
    """Parses .yaif source into interfaces, enums, and config."""

    INTERFACE_HEADER = re.compile(
        r'^\[interface\s+([A-Z][A-Za-z0-9_]*)(?:\s+extends\s+([A-Z][A-Za-z0-9_]*))?\]\s*$'
    )
    ENUM_HEADER    = re.compile(r'^\[enum\s+([A-Z][A-Za-z0-9_]*)\]\s*$')
    CONFIG_HEADER  = re.compile(r'^\[config\]\s*$', re.IGNORECASE)
    FIELD_LINE     = re.compile(r'^(\w+)\s*:\s*(.+)$')
    ENUM_VALUES    = re.compile(r'^[\w\s,]+$')
    COMMENT        = re.compile(r'^\s*#')

    PRIMITIVE_TYPES = {'string', 'int', 'float', 'bool'}

    def __init__(self):
        self.interfaces: list[YAIFInterface] = []
        self.enums:      list[YAIFEnum]      = []
        self.config:     YAIFConfig          = YAIFConfig()
        self._known_names: set[str]          = set()

    # ── Public API ──────────────────────────────────────────────────

    def parse(self, source: str) -> tuple[list[YAIFInterface], list[YAIFEnum], YAIFConfig]:
        """Parse YAIF source. Returns (interfaces, enums, config)."""
        self.interfaces    = []
        self.enums         = []
        self.config        = YAIFConfig()
        self._known_names  = set()

        current_iface: Optional[YAIFInterface] = None
        current_enum:  Optional[YAIFEnum]      = None
        in_config = False

        # First pass — collect all names for type validation
        for line in source.splitlines():
            line = line.strip()
            m = self.INTERFACE_HEADER.match(line)
            if m:
                self._known_names.add(m.group(1))
                continue
            m = self.ENUM_HEADER.match(line)
            if m:
                self._known_names.add(m.group(1))

        # Second pass — full parse
        for line_num, raw in enumerate(source.splitlines(), start=1):
            line = raw.strip()

            if not line or self.COMMENT.match(line):
                continue

            # Config header
            if self.CONFIG_HEADER.match(line):
                current_iface = None
                current_enum  = None
                in_config     = True
                continue

            # Interface header
            m = self.INTERFACE_HEADER.match(line)
            if m:
                current_enum = None
                in_config    = False
                name, parent = m.group(1), m.group(2)
                if parent and parent not in self._known_names:
                    raise YAIFParseError(f"Unknown parent interface: '{parent}'", line_num)
                current_iface = YAIFInterface(name=name, parent=parent)
                self.interfaces.append(current_iface)
                continue

            # Enum header
            m = self.ENUM_HEADER.match(line)
            if m:
                current_iface = None
                in_config     = False
                current_enum  = YAIFEnum(name=m.group(1))
                self.enums.append(current_enum)
                continue

            # Inside config block — key: value pairs
            if in_config:
                m = self.FIELD_LINE.match(line)
                if m:
                    val = m.group(2).strip()
                    # Strip only a matching pair of outer quotes, preserving inner quotes
                    # e.g. "'Fraunces', serif" -> 'Fraunces', serif  (CSS font stack stays intact)
                    if len(val) >= 2 and (
                        (val[0] == '"' and val[-1] == '"') or
                        (val[0] == "'" and val[-1] == "'")
                    ):
                        val = val[1:-1]
                    self.config.raw[m.group(1).strip()] = val
                    continue
                else:
                    raise YAIFParseError(f"Invalid config syntax: '{line}'", line_num)

            # Inside enum block — comma-separated values
            if current_enum is not None:
                if self.ENUM_VALUES.match(line):
                    values = [v.strip() for v in line.split(',') if v.strip()]
                    current_enum.values.extend(values)
                    continue
                else:
                    raise YAIFParseError(f"Invalid enum value syntax: '{line}'", line_num)

            # Field line inside an interface
            m = self.FIELD_LINE.match(line)
            if m:
                if current_iface is None:
                    raise YAIFParseError("Field defined outside of an interface block", line_num)

                field_name = m.group(1)
                raw_rest   = m.group(2).strip()

                # Strip annotations before splitting type/default
                clean_rest, annotations = _parse_annotations(raw_rest)

                default_val = None
                if '=' in clean_rest:
                    parts       = clean_rest.split('=', 1)
                    type_str    = parts[0].strip()
                    default_val = parts[1].strip()
                else:
                    type_str = clean_rest

                # Allow @default annotation as alternative to = syntax
                if 'default' in annotations and default_val is None:
                    default_val = str(annotations.pop('default'))

                self._validate_type(type_str, line_num)

                current_iface.fields.append(YAIFField(
                    name=field_name,
                    type_str=type_str,
                    default=default_val,
                    annotations=annotations,
                ))
                continue

            raise YAIFParseError(f"Unexpected syntax: '{line}'", line_num)

        self._validate_inheritance()
        return self.interfaces, self.enums, self.config

    def parse_file(self, filepath: str) -> tuple[list[YAIFInterface], list[YAIFEnum], YAIFConfig]:
        """Parse a .yaif file from disk."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        if path.suffix != '.yaif':
            raise ValueError(f"Expected a .yaif file, got: {path.suffix}")
        return self.parse(path.read_text(encoding="utf-8"))

    # ── Validation helpers ──────────────────────────────────────────

    def _validate_type(self, type_str: str, line_num: int):
        """Recursively validate a type string."""
        generic = re.match(r'^(list|optional|dict)\[(.+)\]$', type_str, re.IGNORECASE)
        if generic:
            kind  = generic.group(1).lower()
            inner = generic.group(2)
            if kind == 'dict':
                parts = [p.strip() for p in inner.split(',')]
                if len(parts) != 2:
                    raise YAIFParseError(f"dict expects 2 type params, got: {inner}", line_num)
                for p in parts:
                    self._validate_type(p, line_num)
            else:
                self._validate_type(inner, line_num)
            return

        if type_str.lower() in self.PRIMITIVE_TYPES:
            return
        if type_str in self._known_names:
            return

        raise YAIFParseError(f"Unknown type: '{type_str}'", line_num)

    def _validate_inheritance(self):
        """Check for circular inheritance and missing parents."""
        name_map = {i.name: i for i in self.interfaces}
        for iface in self.interfaces:
            if not iface.parent:
                continue
            visited = set()
            current = iface
            while current and current.parent:
                if current.name in visited:
                    raise YAIFParseError(
                        f"Circular inheritance detected: {current.name} -> {current.parent}"
                    )
                visited.add(current.name)
                current = name_map.get(current.parent)