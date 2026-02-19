# YAIF — Yet Another Interface Format

A lightweight schema language and multi-target code generator. Define your data model once in a `.yaif` file, then generate Python dataclasses, TypeScript interfaces, JSON Schema, a fully interactive HTML CRUD prototype, or Discord-formatted output — all from the same source.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [The .yaif Format](#the-yaif-format)
  - [Config Block](#config-block)
  - [Interfaces](#interfaces)
  - [Enums](#enums)
  - [Types](#types)
  - [Annotations](#annotations)
  - [Inheritance](#inheritance)
- [Generators](#generators)
  - [Python](#python)
  - [TypeScript](#typescript)
  - [JSON Schema](#json-schema)
  - [HTML](#html)
  - [Discord](#discord)
- [Discord Webhook](#discord-webhook)
- [File Watcher](#file-watcher)
- [CLI Reference](#cli-reference)

---

## Installation

Clone the repository and install dependencies (no external packages required for core usage):

```bash
git clone https://github.com/yourorg/yaif.git
cd yaif
pip install -e .
```

The project uses only the Python standard library for its core parser, generator, and watcher. The Discord webhook sender also uses only stdlib (`urllib`, `json`).

---

## Quick Start

1. Create a `.yaif` file:

```yaif
[config]
title: My App
description: A sample schema

[interface User]
id:    int
name:  string   @label="Full Name"
email: string   @placeholder="user@example.com"
admin: bool     = false

[enum Role]
admin, editor, viewer
```

2. Generate output:

```bash
# Python dataclasses
python -m yaif schema.yaif -t python

# TypeScript interfaces
python -m yaif schema.yaif -t typescript -o types.ts

# Interactive HTML prototype
python -m yaif schema.yaif -t html -o app.html

# Validate only (no output)
python -m yaif schema.yaif --validate-only
```

---

## The .yaif Format

A `.yaif` file is made up of three kinds of blocks: `[config]`, `[interface]`, and `[enum]`. Lines beginning with `#` are comments.

### Config Block

The `[config]` block holds app-level metadata and theming. All values are key-value pairs separated by `:`.

```yaif
[config]
title:       My App
description: A content management schema
accent:      "#e05c2a"
background:  "#f7f3ec"
font:        "'Inter', sans-serif"
mono:        "'DM Mono', monospace"
```

Common config keys used by the HTML generator:

| Key | Purpose | Default |
|-----|---------|---------|
| `title` | App name shown in the UI | `YAIF App` |
| `description` | Subtitle / metadata | *(empty)* |
| `accent` | Primary accent color | `#c84b31` |
| `accent2` | Secondary accent color | `#2a6496` |
| `background` | Page background | `#f5f0e8` |
| `surface` | Card/panel background | `#ffffff` |
| `ink` | Primary text color | `#1a1a2e` |
| `muted` | Secondary text color | `#8a8070` |
| `font` | Body font stack | `'Fraunces', Georgia, serif` |
| `mono` | Monospace font stack | `'DM Mono', monospace` |
| `font_url` | Google Fonts URL override | *(DM Mono + Fraunces)* |

### Interfaces

Interfaces are the primary building block — each one maps to a class, type, or form:

```yaif
[interface Post]
title:    string
body:     string
tags:     list[string]
author:   optional[Author]
status:   PostStatus = draft
```

Fields follow the pattern `name: type` or `name: type = default`.

### Enums

Enums define a fixed set of string values, comma-separated:

```yaif
[enum PostStatus]
draft, published, archived
```

### Types

YAIF supports the following types:

| YAIF Type | Python | TypeScript | JSON Schema |
|-----------|--------|------------|-------------|
| `string` | `str` | `string` | `{"type": "string"}` |
| `int` | `int` | `number` | `{"type": "integer"}` |
| `float` | `float` | `number` | `{"type": "number"}` |
| `bool` | `bool` | `boolean` | `{"type": "boolean"}` |
| `list[T]` | `list[T]` | `T[]` | `{"type": "array", "items": ...}` |
| `optional[T]` | `Optional[T]` | `T \| null` | `{"oneOf": [T, null]}` |
| `dict[K, V]` | `dict[K, V]` | `Record<K, V>` | `{"type": "object", "additionalProperties": V}` |
| `InterfaceName` | class reference | type reference | `$ref` |
| `EnumName` | `Enum` subclass | `enum` | `$ref` |

### Annotations

Annotations are hints attached to fields using `@key` or `@key="value"` syntax. They are placed after the type (and optional default) on the same line:

```yaif
[interface Product]
name:        string           @label="Product Name" @placeholder="Enter name"
description: string           @rows=6 @wide @hint="Supports markdown"
price:       float            @label="Price (USD)"
internal_id: string           @hidden
created_at:  optional[string] @readonly
```

**General annotations (used by HTML generator):**

| Annotation | Effect |
|-----------|--------|
| `@label="Text"` | Display label (overrides field name) |
| `@placeholder="Text"` | Input placeholder text |
| `@hint="Text"` | Helper text shown below the field |
| `@hidden` | Exclude field from generated UI / output |
| `@readonly` | Render as disabled / non-editable |
| `@wide` | Span the full form width |
| `@rows=N` | Render as a textarea with N rows |
| `@group="Name"` | Group fields under a visual section header |
| `@order=N` | Override field display order |
| `@default="value"` | Alternative to `= value` syntax |

**Discord annotations** (see [Discord](#discord) section).

### Inheritance

Interfaces can extend one another using `extends`. All parent fields are inherited and included in generated output:

```yaif
[interface BaseEntity]
id:         int
created_at: string

[interface Post extends BaseEntity]
title: string
body:  string
```

Circular inheritance is detected and raises a parse error. Multiple levels of inheritance are supported.

---

## Generators

Run any generator with `-t <target>`. Pipe to stdout or write to a file with `-o <file>`.

### Python

Generates `@dataclass` classes and `Enum` subclasses.

```bash
python -m yaif schema.yaif -t python -o models.py
```

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class PostStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

@dataclass
class Post:
    title: str
    body: str
    status: str = "draft"
    tags: list[str] = field(default_factory=list)
```

Fields without defaults are placed before fields with defaults (required by Python dataclasses).

### TypeScript

Generates `export interface` and `export enum` declarations.

```bash
python -m yaif schema.yaif -t typescript -o types.ts
```

```typescript
export enum PostStatus {
  draft = "draft",
  published = "published",
}

export interface Post extends BaseEntity {
  title: string;
  body: string;
  status?: PostStatus;
  tags: string[];
}
```

### JSON Schema

Generates draft-07 JSON Schema with `$definitions` for all interfaces and enums. Supports `$ref` for cross-references and `allOf` for inheritance.

```bash
python -m yaif schema.yaif -t jsonschema -o schema.json
```

### HTML

Generates a fully self-contained, single-file HTML application — no build step, no server required. Open it in any browser.

```bash
python -m yaif schema.yaif -t html -o app.html
```

Features of the generated app:
- A tab per interface
- Forms with appropriate inputs for every field type (text, number, checkbox, select for enums, textarea for long text, nested forms for interface fields, dynamic lists and dicts)
- Add, edit, delete, and export records as JSON
- Field grouping via `@group`, ordering via `@order`
- Full theming driven by the `[config]` block (colors, fonts)

### Discord

Generates formatted text output for pasting or sending to Discord. Uses box-drawing characters inside code blocks for clean rendering.

```bash
python -m yaif discord.yaif -t discord
```

Three rendering modes, controlled per-interface with `@discord=<mode>`:

| Mode | Annotation | Output |
|------|-----------|--------|
| `table` | `@discord=table` *(default)* | Box-drawing table with column headers |
| `kv` | `@discord=kv` | Aligned key: value pairs |
| `list` | `@discord=list` | Bulleted list |

**Discord field annotations:**

| Annotation | Effect |
|-----------|--------|
| `@discord=table\|kv\|list` | Set render mode for this interface |
| `@discord_title="Name"` | Override the section heading |
| `@discord_icon="📊"` | Emoji prefix on the heading |
| `@discord_width=N` | Minimum column width (table mode) |
| `@label="Text"` | Column/key header text |
| `@hidden` | Skip this field in Discord output |

---

## Discord Webhook

Send output directly to a Discord channel without leaving the terminal.

```bash
# Send plain text
python -m yaif discord.yaif -t discord --send --webhook-url https://discord.com/api/webhooks/...

# Send as rich embeds
python -m yaif discord.yaif -t discord --send --embed

# Store the webhook URL in the file so you don't have to pass it every time
```

Set `webhook_url` in the `[config]` block to avoid passing `--webhook-url` on every run:

```yaif
[config]
webhook_url:      https://discord.com/api/webhooks/...
webhook_username: My Bot
embed_mode:       false
embed_color:      #5865F2
```

**Rich embed annotations** (used when `--embed` or `embed_mode: true`):

| Annotation | Effect |
|-----------|--------|
| `@embed_color="#rrggbb"` | Sidebar color for this interface's embed |
| `@embed_url="https://..."` | Make the embed title a hyperlink |
| `@embed_footer="text"` | Custom footer text |
| `@embed_thumbnail` | Use field's default as thumbnail URL |
| `@embed_image` | Use field's default as embed image URL |
| `@embed_timestamp` | Use field's default as ISO 8601 timestamp |
| `@embed_inline` | Render field side-by-side with others |

Discord limits 10 embeds per message — YAIF automatically batches larger payloads into multiple requests.

---

## File Watcher

Watch a `.yaif` file and automatically regenerate output on every save:

```bash
python -m yaif schema.yaif -t typescript -o types.ts --watch
```

Uses simple polling (no external dependencies). Press `Ctrl+C` to stop.

---

## CLI Reference

```
python -m yaif <file> [options]

Positional:
  file                    Path to the .yaif file

Generator options:
  -t, --target            Output target: python, typescript, jsonschema, html, discord
  -o, --output            Write output to this file (default: stdout)
  --validate-only         Parse and validate without generating output
  -w, --watch             Watch file for changes and regenerate automatically

Discord webhook options:
  --send                  Send output to a Discord webhook
  --webhook-url URL       Discord webhook URL (overrides config)
  --embed                 Send as rich embeds instead of plain text
  --webhook-username NAME Override bot display name
  --webhook-avatar URL    Override bot avatar URL
```

---

## Project Structure

```
yaif/
├── __main__.py          CLI entrypoint
├── models.py            Data classes: YAIFField, YAIFInterface, YAIFEnum, YAIFConfig
├── parser.py            YAIFParser — tokenizes and validates .yaif source
├── discord_webhook.py   Discord embed builder and HTTP sender
├── watcher.py           File watcher (polling-based)
└── generators/
    ├── base.py          BaseGenerator abstract class
    ├── python.py        Python dataclass generator
    ├── typescript.py    TypeScript interface generator
    ├── jsonschema.py    JSON Schema draft-07 generator
    ├── html.py          Self-contained HTML CRUD generator
    └── discord.py       Discord text formatter
```

---

## Example Files

- `example.yaif` — full kitchen-sink example (blog system) demonstrating all HTML generator features
- `discord.yaif` — Discord output demo with all render modes and embed annotations

---

## License

See `LICENSE.txt` for terms.