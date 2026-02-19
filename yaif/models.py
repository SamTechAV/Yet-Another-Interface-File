"""
YAIF data models — the internal representation of parsed .yaif files.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class YAIFField:
    """A single field in an interface."""
    name: str
    type_str: str
    default: Optional[str] = None
    annotations: dict[str, Any] = field(default_factory=dict)

    def has_default(self) -> bool:
        return self.default is not None

    def ann(self, key: str, fallback=None):
        """Convenience getter for an annotation value."""
        return self.annotations.get(key, fallback)

    def __repr__(self):
        d = f" = {self.default}" if self.default else ""
        a = f" {self.annotations}" if self.annotations else ""
        return f"{self.name}: {self.type_str}{d}{a}"


@dataclass
class YAIFEnum:
    """An enum definition with named values."""
    name: str
    values: list[str] = field(default_factory=list)

    def __repr__(self):
        return f"[enum {self.name}] {', '.join(self.values)}"


@dataclass
class YAIFInterface:
    """An interface definition, optionally extending a parent."""
    name: str
    fields: list[YAIFField] = field(default_factory=list)
    parent: Optional[str] = None

    def __repr__(self):
        ext = f" extends {self.parent}" if self.parent else ""
        fields_str = "\n  ".join(str(f) for f in self.fields)
        return f"[interface {self.name}{ext}]\n  {fields_str}"

    def fields_reordered(self) -> list[YAIFField]:
        """Return fields with non-default fields first, then default fields.
        Needed for Python dataclasses which require this ordering."""
        no_default = [f for f in self.fields if not f.has_default()]
        has_default = [f for f in self.fields if f.has_default()]
        return no_default + has_default


@dataclass
class YAIFConfig:
    """
    Parsed from the [config] block. Holds theme tokens, app metadata,
    and any per-generator overrides. All values are plain strings or
    booleans — generators pick out what they care about.

    Example .yaif block:
        [config]
        title: My App
        accent: "#e05c2a"
        background: "#f7f3ec"
        font: "Inter, sans-serif"
        mono: "DM Mono, monospace"
    """
    raw: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, fallback: str = "") -> str:
        return self.raw.get(key, fallback)

    def get_bool(self, key: str, fallback: bool = False) -> bool:
        val = self.raw.get(key)
        if val is None:
            return fallback
        return str(val).lower() in ('true', '1', 'yes')

    # ── Convenience properties for common config keys ──────────────

    @property
    def title(self) -> str:
        return self.get("title", "YAIF App")

    @property
    def description(self) -> str:
        return self.get("description", "")

    @property
    def accent(self) -> str:
        return self.get("accent", "#c84b31")

    @property
    def accent2(self) -> str:
        return self.get("accent2", "#2a6496")

    @property
    def background(self) -> str:
        return self.get("background", "#f5f0e8")

    @property
    def surface(self) -> str:
        return self.get("surface", "#ffffff")

    @property
    def cream(self) -> str:
        return self.get("cream", "#ede8dc")

    @property
    def line(self) -> str:
        return self.get("line", "#d4cec0")

    @property
    def ink(self) -> str:
        return self.get("ink", "#1a1a2e")

    @property
    def muted(self) -> str:
        return self.get("muted", "#8a8070")

    @property
    def font(self) -> str:
        return self.get("font", "'Fraunces', Georgia, serif")

    @property
    def mono(self) -> str:
        return self.get("mono", "'DM Mono', monospace")