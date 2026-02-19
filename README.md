<!--- yaml-front-matter-below
---
title: "YAIF — Yet Another Interface File"
description: "A lightweight schema language and multi-target code generator. Define your data model once, generate Python, TypeScript, JSON Schema, HTML CRUD apps, and Discord output."
tags: ["parser", "code-generation", "schema", "typescript", "python", "json-schema", "html", "discord", "low-code"]
---
-->

<div align="center">

# YAIF · Yet Another Interface File

[![PyPI version](https://img.shields.io/pypi/v/yaif?style=flat-square&logo=pypi)](https://pypi.org/project/yaif/)
![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat-square&logo=python)
![License](https://img.shields.io/github/license/SamTechAV/Yet-Another-Interface-File?style=flat-square&logo=open-source)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen?style=flat-square&logo=python)
![Built with stdlib](https://img.shields.io/badge/dependencies-zero-4493D?style=flat-square&logo=rust)
</div>

---

## 📦 Installation

```bash
pip install yaif
```

YAIF uses only the Python standard library—no external dependencies required.

---

## 🚀 Quick Start (60 seconds)

1️⃣ **Create** `schema.yaif`

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

2️⃣ **Generate** your code

```bash
# Python dataclasses
python -m yaif schema.yaif -t python -o models.py

# TypeScript interfaces
python -m yaif schema.yaif -t typescript -o types.ts

# Interactive HTML prototype
python -m yaif schema.yaif -t html -o app.html

# JSON Schema
python -m yaif schema.yaif -t jsonschema -o schema.json
```

3️⃣ **Open** `app.html` in your browser—instant CRUD UI with zero configuration.

---

## ✨ Why YAIF?

| ✅ Feature | 💡 Benefit |
|-----------|------------|
| **Single source of truth** | Define once, generate for multiple platforms |
| **Zero runtime deps** | Pure stdlib—no `node_modules`, no `pip install` for users |
| **Instant HTML UI** | Generated forms work immediately in any browser |
| **Type-safe** | Strong typing across Python, TypeScript, JSON Schema |
| **Live reload** | `--watch` mode regenerates on file changes |
| **Discord integration** | Send formatted output directly to channels |
| **Inheritance & grouping** | Build complex schemas with clean organization |
| **Production-grade** | Validates circular dependencies, proper defaults |

---

## 📖 The `.yaif` Format

A `.yaif` file consists of three block types:

### 1. `[config]` — Application Metadata & Theming

```yaif
[config]
title:       Store Admin
description: E-commerce management
accent:      "#007aff"
background:  "#f2f2f7"
surface:     "#ffffff"
ink:         "#1c1c1e"
muted:       "#8e8e93"
font:        "'Inter', system-ui, sans-serif"
mono:        "'SF Mono', 'Fira Code', monospace"
```

| Key | Purpose | Default |
|-----|---------|---------|
| `title` | App name in HTML UI | `YAIF App` |
| `description` | Subtitle | *(empty)* |
| `accent` | Primary color | `#c84b31` |
| `accent2` | Secondary color | `#2a6496` |
| `background` | Page background | `#f5f0e8` |
| `surface` | Card/panel background | `#ffffff` |
| `ink` | Primary text | `#1a1a2e` |
| `muted` | Secondary text | `#8a8070` |
| `font` | Body font stack | `'Fraunces', Georgia, serif` |
| `mono` | Monospace font | `'DM Mono', monospace` |
| `font_url` | Google Fonts override | *(DM Mono + Fraunces)* |

### 2. `[interface]` — Data Structures

```yaif
[interface Post extends BaseEntity]
title:    string                @label="Title"       @placeholder="Enter title"
body:     string                @rows=8              @wide
status:   PostStatus            @label="Status"      @order=10
tags:     list[string]          @label="Tags"        @hint="Comma-separated"
author:   optional[Author]      @label="Author"
created:  string       = now()  @readonly            @group="Meta"
```

**Field syntax:** `name: type [= default] [@annotation]`

**Supported types:**

| YAIF Type | Python | TypeScript | JSON Schema |
|-----------|--------|------------|-------------|
| `string` | `str` | `string` | `{"type": "string"}` |
| `int` | `int` | `number` | `{"type": "integer"}` |
| `float` | `float` | `number` | `{"type": "number"}` |
| `bool` | `bool` | `boolean` | `{"type": "boolean"}` |
| `list[T]` | `list[T]` | `T[]` | `{"type": "array", "items": ...}` |
| `optional[T]` | `Optional[T]` | `T \| null` | `{"oneOf": [T, null]}` |
| `dict[K,V]` | `dict[K,V]` | `Record<K,V>` | `{"type": "object", "additionalProperties": V}` |
| `InterfaceName` | class reference | type reference | `{"$ref": "#/$defs/InterfaceName"}` |
| `EnumName` | `Enum` subclass | `enum` | `{"$ref": "#/$defs/EnumName"}` |

### 3. `[enum]` — Enumerations

```yaif
[enum PostStatus]
draft, published, archived

[enum Priority]
low = 1, normal = 2, high = 3, urgent = 4
```

---

## 🏷️ Annotations

Place annotations after the type/default using `@key` or `@key="value"` syntax.

### HTML Generator Annotations

| Annotation | Effect |
|------------|--------|
| `@label="Text"` | Custom field label (overrides name) |
| `@placeholder="Text"` | Input placeholder text |
| `@hint="Text"` | Helper text below field |
| `@hidden` | Exclude from generated UI/output |
| `@readonly` | Render as disabled/non-editable |
| `@wide` | Span full form width |
| `@rows=N` | Render as textarea with N rows |
| `@group="Name"` | Group fields under collapsible section |
| `@order=N` | Override field display order |
| `@default="value"` | Alternative to `= value` syntax |

### Discord Annotations

| Annotation | Effect |
|------------|--------|
| `@discord=table\|kv\|list` | Render mode for this interface |
| `@discord_title="Name"` | Override section heading |
| `@discord_icon="📊"` | Emoji prefix on heading |
| `@discord_width=N` | Min column width (table mode) |
| `@label="Text"` | Column/key header text |
| `@hidden` | Skip field in output |

### Embed Annotations (when using `--embed`)

| Annotation | Effect |
|------------|--------|
| `@embed_color="#rrggbb"` | Sidebar color for this embed |
| `@embed_url="https://..."` | Make title a hyperlink |
| `@embed_footer="text"` | Custom footer text |
| `@embed_thumbnail` | Use field value as thumbnail URL |
| `@embed_image` | Use field value as embed image |
| `@embed_timestamp` | Use field value as ISO 8601 timestamp |
|| `@embed_inline` | Render field side-by-side with others |

---

## 🔄 Inheritance

Interfaces can extend other interfaces—all parent fields are inherited.

```yaif
[interface BaseEntity]
id:         int
created_at: string

[interface Post extends BaseEntity]
title: string
body:  string
```

Circular inheritance is detected and raises a parse error. Multiple inheritance levels are supported.

---

## ⚙️ Generators

Run any generator with `-t <target>`. Pipe to stdout or write with `-o <file>`.

### 🐍 Python

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

> **Note:** Fields without defaults appear before fields with defaults (required by Python dataclasses).

---

### 📘 TypeScript

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

---

### 📋 JSON Schema

Generates draft-07 JSON Schema with `$definitions`. Supports `$ref` and `allOf` for inheritance.

```bash
python -m yaif schema.yaif -t jsonschema -o schema.json
```

---

### 🌐 HTML (Instant CRUD UI)

Generates a fully self-contained, single-file HTML application. No build step, no server—just open in a browser.

```bash
python -m yaif schema.yaif -t html -o app.html
```

**Features:**
- 📑 A tab per interface
- 📝 Forms with appropriate inputs (text, number, checkbox, select, textarea)
- 🔄 Nested forms for interface fields, dynamic lists & dicts
- ➕➖ Add, edit, delete, export records as JSON
- 🎨 Full theming from `[config]` block
- 📱 Responsive design
- ⚡ Client-side only—no backend needed

---

### 💬 Discord Output

Generates formatted text with box-drawing characters for clean Discord rendering.

```bash
python -m yaif discord.yaif -t discord
```

**Render modes:**

| Mode | Default | Example |
|------|---------|---------|
| `table` | ✅ | Box-drawing table with column headers |
| `kv` |  | Aligned `key: value` pairs |
| `list` |  | Bulleted list |

---

## 📤 Discord Webhook

Send output directly to a Discord channel from the terminal.

```bash
# Send plain text
python -m yaif discord.yaif -t discord --send --webhook-url https://discord.com/api/webhooks/...

# Send as rich embeds
python -m yaif discord.yaif -t discord --send --embed
```

Store the webhook URL in `[config]` to avoid passing it every time:

```yaif
[config]
webhook_url:      https://discord.com/api/webhooks/...
webhook_username: My Bot
embed_mode:       false
embed_color:      #5865F2
```

> **Limitation:** Discord allows max 10 embeds per message—YAIF auto-batches larger payloads.

---

## 👁️ File Watcher

Watch a `.yaif` file and regenerate output automatically on every save:

```bash
python -m yaif schema.yaif -t typescript -o types.ts --watch
```

Uses simple polling (no external deps). Press `Ctrl+C` to stop.

---

## 🎯 CLI Reference

```txt
python -m yaif <file> [options]

Positional:
  file                    Path to the .yaif file

Generator options:
  -t, --target            Target: python, typescript, jsonschema, html, discord
  -o, --output            Write to file (default: stdout)
  --validate-only         Parse and validate without generating
  -w, --watch             Watch for changes and regenerate

Discord webhook options:
  --send                  Send to Discord webhook
  --webhook-url URL       Webhook URL (overrides config)
  --embed                 Send as rich embeds
  --webhook-username NAME Override bot display name
  --webhook-avatar URL    Override bot avatar URL
```

---

## 🗂️ Project Structure

```
yaif/
├── __main__.py          CLI entrypoint
├── models.py            Data classes: YAIFField, YAIFInterface, YAIFEnum, YIFConfig
├── parser.py            YAIFParser — tokenizes & validates .yaif source
├── discord_webhook.py   Discord embed builder + HTTP sender
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

## 📚 Example Files

Explore real-world usage in the `examples/` directory:

| Example | Description |
|---------|-------------|
| [`ecommerce.yaif`](examples/ecommerce.yaif) | Full e-commerce schema: products, orders, customers, reviews |
| [`clinic.yaif`](examples/clinic.yaif) | Medical clinic patient & appointment system |
| [`project_tracker.yaif`](examples/project_tracker.yaif) | Project & task management |
| [`jobs.yaif`](examples/jobs.yaif) | Job board with postings & applications |
| [`smart_home.yaif`](examples/smart_home.yaif) | IoT device & automation dashboard |
| [`rpg.yaif`](examples/rpg.yaif) | RPG game entities (characters, items, quests) |
| [`ci_discord.yaif`](examples/ci_discord.yaif) | Discord notifications for CI/CD |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `python -m yaif --validate-only` passes on example files
5. Submit a pull request

See `CONTRIBUTING.md` for detailed guidelines.

---

## 📄 License

MIT License—see [`LICENSE.txt`](LICENSE.txt) for details.

---

<div align="center">

**Built with ❤️ using only Python standard library**

[GitHub](https://github.com/SamTechAV/Yet-Another-Interface-File) · [Issues](https://github.com/SamTechAV/Yet-Another-Interface-File/issues) · [Changelog](CHANGELOG.md)

</div>