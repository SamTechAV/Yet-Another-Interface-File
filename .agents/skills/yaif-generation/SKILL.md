---
name: yaif-generation
description: Create perfectly tailored and formatted YAIF (Yet Another Interface File) schema definitions. Use when you need to define data models, interfaces, or enums that can generate Python, TypeScript, JSON Schema, HTML CRUD apps, or Discord output.
metadata:
  version: "1.0"
  author: SamTechAV
---

## Overview

This skill provides comprehensive guidance for creating high-quality `.yaif` files that follow best practices and leverage all YAIF features. YAIF is a zero-dependency schema language that generates code for multiple targets from a single source.

## When to Use

Use this skill when you need to:
- Define data models/schemas for applications
- Create types that work across Python, TypeScript, and JSON Schema
- Generate ready-to-use HTML CRUD interfaces
- Structure data for Discord bots or webhook integration
- Replace handwritten dataclasses/interfaces with a single source of truth

## Step-by-Step Process

### 1. Understand Requirements

Gather key information:
- **What domain/application** are you modeling? (e.g., e-commerce, user management, IoT)
- **What entities** exist? (e.g., User, Product, Order, Post)
- **What fields** does each entity have? Include:
  - Field name (snake_case or camelCase)
  - Data type (string, int, float, bool, list[T], optional[T], dict[K,V], or another interface/enum)
  - Default values (if any)
  - Validation constraints
- **Any enums** needed? (e.g., Role, Status, Priority)
- **Any inheritance** relationships? (e.g., BaseEntity → User, Post)
- **Target outputs**? (Python, TypeScript, JSON Schema, HTML, Discord) — you can generate all from the same file.

### 2. Start with `[config]`

The optional `[config]` block defines application metadata and theming for the HTML generator:

```yaif
[config]
title: "My Application"           # App name (shown in HTML UI)
description: "Brief description"  # Subtitle
accent: "#c84b31"                 # Primary color (buttons, highlights)
background: "#f5f0e8"             # Page background
surface: "#ffffff"                # Card/panel background
ink: "#1a1a2e"                    # Primary text color
muted: "#8a8070"                  # Secondary text
font: "'Fraunces', Georgia, serif" # Body font
mono: "'DM Mono', monospace"      # Monospace font
```

Theme colors follow CSS conventions. The defaults are carefully chosen for a professional look.

### 3. Define Enums First (if any)

Define enumerations before interfaces that reference them:

```yaif
[enum Role]
admin, editor, viewer

[enum Status]
draft = "draft", published = "published", archived = "archived"

[enum Priority]
low = 1, normal = 2, high = 3, urgent = 4
```

**Rules:**
- Enum values without explicit assignment get sequential integers starting from 1
- Explicit assignments can be strings or integers
- Enum names use PascalCase
- Values become Python enum members and TypeScript enum values

### 4. Define Interfaces

Use `[interface InterfaceName]` blocks. Each field follows:

```
name: type [= default] [@annotation]
```

#### Field Types

| YAIF Type | Python | TypeScript | JSON Schema |
|-----------|--------|------------|-------------|
| `string`  | `str`  | `string`   | `{"type": "string"}` |
| `int`     | `int`  | `number`   | `{"type": "integer"}` |
| `float`   | `float`| `number`   | `{"type": "number"}` |
| `bool`    | `bool` | `boolean`  | `{"type": "boolean"}` |
| `list[T]` | `list[T]` | `T[]` | `{"type": "array", "items": T}` |
| `dict[K,V]` | `dict[K,V]` | `Record<K,V>` | `{"type": "object", "additionalProperties": V}` |
| `InterfaceName` | class ref | type ref | `{"$ref": "#/$defs/InterfaceName"}` |
| `EnumName` | `Enum` | `enum` | `{"$ref": "#/$defs/EnumName"}` |

#### Optional Fields

Use `optional[T]` for nullable/optional fields:

```yaif
email: optional[string] = null
metadata: optional[dict[string, string]]
parent: optional[Category]
```

In Python: `Optional[T]`; in TypeScript: `T | null`.

#### Default Values

Use `=` syntax for defaults. Required fields omit `= default`:

```yaif
name: string                           # required
active: bool = true                    # optional with default
count: int = 0
status: PostStatus = draft
```

**Python note:** Required fields must appear before optional fields (YAIF auto-reorders when generating Python).

#### Inheritance

Interfaces can extend one parent:

```yaif
[interface BaseEntity]
id: int
created_at: string

[interface User extends BaseEntity]
name: string
email: string
```

All parent fields are inherited. Circular dependency detection is built-in.

### 5. Add Annotations (Optional)

Annotations customize generation for specific targets. Place after type/default with `@key` or `@key="value"`.

#### HTML Generator Annotations

| Annotation | Effect |
|------------|--------|
| `@label="Text"` | Custom field label (overrides name) |
| `@placeholder="Text"` | Input placeholder |
| `@hint="Text"` | Helper text below field |
| `@hidden` | Exclude from generated UI |
| `@readonly` | Render as disabled |
| `@wide` | Span full form width |
| `@rows=N` | Render as textarea with N rows |
| `@group="Name"` | Group under collapsible section |
| `@order=N` | Override field display order |
| `@default="value"` | Alternative to `= value` |

#### Discord Annotations

| Annotation | Effect |
|------------|--------|
| `@discord=table\|kv\|list` | Render mode |
| `@discord_title="Name"` | Override section heading |
| `@discord_icon="📊"` | Emoji prefix |
| `@discord_width=N` | Min column width (table mode) |
| `@label="Text"` | Column/key header |
| `@hidden` | Skip field |

#### Embed Annotations (with `--embed`)

| Annotation | Effect |
|------------|--------|
| `@embed_color="#rrggbb"` | Sidebar color |
| `@embed_url="https://..."` | Hyperlink title |
| `@embed_footer="text"` | Custom footer |
| `@embed_thumbnail` | Use field as thumbnail URL |
| `@embed_image` | Use field as embed image |
| `@embed_timestamp` | Use field as ISO 8601 timestamp |
| `@embed_inline` | Render side-by-side |

### 6. Complete Example

```yaif
[config]
title: "E-Commerce Store"
description: "Product and order management"
accent: "#007aff"

[enum OrderStatus]
pending, processing, shipped, delivered, cancelled

[enum PaymentMethod]
credit_card, paypal, stripe

[interface BaseEntity]
id: int
created_at: string = now()

[interface Product extends BaseEntity]
name: string                @label="Product Name" @placeholder="Enter product name"
price: float                @label="Price" @placeholder="0.00"
description: string         @rows=5 @wide
in_stock: bool = true
category: optional[string] @label="Category"
tags: list[string]          @hint="Comma-separated tags"

[interface Order extends BaseEntity]
order_number: string        @label="Order #"
customer: string            @label="Customer Name"
status: OrderStatus         @label="Status" @order=10
payment_method: PaymentMethod @label="Payment Method"
items: list[Product]        @label="Items"
shipped_date: optional[string] @label="Shipped Date" @readonly
```

### 7. Validate and Generate

```bash
# Validate only
python -m yaif schema.yaif --validate-only

# Generate Python
python -m yaif schema.yaif -t python -o models.py

# Generate TypeScript
python -m yaif schema.yaif -t typescript -o types.ts

# Generate JSON Schema
python -m yaif schema.yaif -t jsonschema -o schema.json

# Generate HTML CRUD app
python -m yaif schema.yaif -t html -o app.html

# Generate Discord output
python -m yaif schema.yaif -t discord

# Watch mode (regenerate on changes)
python -m yaif schema.yaif -t typescript -o types.ts --watch
```

## Formatting Rules

- **No trailing commas** in block definitions
- **Indentation**: YAML-like, 2-4 spaces per level (consistent)
- **Field order** doesn't matter; YAIF sorts appropriately for each target
- **Comments**: Use `# comment` at end of line or on its own line (works in YAIF 0.1.0+)
- **Blank lines** separate blocks for readability

## Annotations Quick Reference

### For All Targets
- `@label` — Human-readable name
- `@hidden` — Exclude from output

### HTML-Focused
- `@placeholder`, `@hint`, `@rows`, `@wide`, `@group`, `@order`

### Discord-Focused
- `@discord=table|kv|list`, `@discord_title`, `@discord_icon`, `@discord_width`

### Embed-Focused (Discord embeds)
- `@embed_color`, `@embed_url`, `@embed_footer`, `@embed_thumbnail`, `@embed_image`, `@embed_timestamp`, `@embed_inline`

## Common Pitfalls

1. **Forgetting commas between fields** — Always separate fields with newlines, no commas needed within a block
2. **Required fields after optional in Python** — YAIF handles this automatically, but avoid mixing if manually editing generated code
3. **Circular inheritance** — YAIF detects and rejects cycles
4. **Undefined types** — All referenced interfaces/enums must be defined somewhere
5. **Missing quotes** on strings with spaces: `@label="Full Name"` not `@label=Full Name`

## Validation

Run before committing:
```bash
python -m yaif yourfile.yaif --validate-only
```

This catches syntax errors, undefined types, circular dependencies, and duplicate definitions.

## Resources

- Full documentation: See `README.md` in this repository
- Example files: `examples/` directory
- Specification: Running `python -m yaif --help` shows all CLI options
