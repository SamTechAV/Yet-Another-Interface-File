"""
Python code generator — outputs dataclasses and Enums.
Config and annotations are ignored (not relevant to Python type output).
"""

import re
from typing import Optional

from .base import BaseGenerator
from ..models import YAIFInterface, YAIFEnum, YAIFConfig


class PythonGenerator(BaseGenerator):

    TYPE_MAP = {
        'string': 'str',
        'int':    'int',
        'float':  'float',
        'bool':   'bool',
    }

    def generate(
        self,
        interfaces: list[YAIFInterface],
        enums: list[YAIFEnum],
        config: YAIFConfig,
    ) -> str:
        lines = [
            'from __future__ import annotations',
            'from dataclasses import dataclass, field',
            'from enum import Enum',
            'from typing import Optional',
            '',
        ]

        if config.description:
            lines.insert(0, f'"""{config.description}"""')
            lines.insert(1, '')

        for enum in enums:
            lines.append(f'class {enum.name}(Enum):')
            for val in enum.values:
                lines.append(f'    {val.upper()} = "{val}"')
            lines.append('')

        for iface in interfaces:
            parent  = f'({iface.parent})' if iface.parent else ''
            lines.append('@dataclass')
            lines.append(f'class {iface.name}{parent}:')

            ordered = iface.fields_reordered()
            if not ordered:
                lines.append('    pass')
            else:
                for f in ordered:
                    py_type = self._convert_type(f.type_str)
                    default = self._convert_default(f.default, f.type_str)
                    if default is not None:
                        lines.append(f'    {f.name}: {py_type} = {default}')
                    else:
                        lines.append(f'    {f.name}: {py_type}')
            lines.append('')

        return '\n'.join(lines)

    def _convert_type(self, type_str: str) -> str:
        low = type_str.lower()
        if low in self.TYPE_MAP:
            return self.TYPE_MAP[low]

        generic = re.match(r'^(list|optional|dict)\[(.+)\]$', type_str, re.IGNORECASE)
        if generic:
            kind  = generic.group(1).lower()
            inner = generic.group(2)
            if kind == 'list':
                return f'list[{self._convert_type(inner)}]'
            elif kind == 'optional':
                return f'Optional[{self._convert_type(inner)}]'
            elif kind == 'dict':
                parts = [p.strip() for p in inner.split(',')]
                return f'dict[{self._convert_type(parts[0])}, {self._convert_type(parts[1])}]'

        return type_str

    def _convert_default(self, default: Optional[str], type_str: str) -> Optional[str]:
        if default is None:
            return None
        low = default.lower()
        if low == 'true':   return 'True'
        if low == 'false':  return 'False'
        if low in ('none', 'null'): return 'None'
        if low == '[]':  return 'field(default_factory=list)'
        if low == '{}':  return 'field(default_factory=dict)'
        return default