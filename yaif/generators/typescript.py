"""
TypeScript code generator — outputs interfaces and enums.
Config and annotations are ignored (not relevant to TypeScript type output).
"""

import re

from .base import BaseGenerator
from ..models import YAIFInterface, YAIFEnum, YAIFConfig


class TypeScriptGenerator(BaseGenerator):

    TYPE_MAP = {
        'string': 'string',
        'int':    'number',
        'float':  'number',
        'bool':   'boolean',
    }

    def generate(
        self,
        interfaces: list[YAIFInterface],
        enums: list[YAIFEnum],
        config: YAIFConfig,
    ) -> str:
        lines = []

        for enum in enums:
            lines.append(f'export enum {enum.name} {{')
            for val in enum.values:
                lines.append(f'  {val} = "{val}",')
            lines.append('}')
            lines.append('')

        for iface in interfaces:
            ext = f' extends {iface.parent}' if iface.parent else ''
            lines.append(f'export interface {iface.name}{ext} {{')
            for f in iface.fields:
                ts_type  = self._convert_type(f.type_str)
                optional = '?' if f.type_str.lower().startswith('optional[') else ''
                lines.append(f'  {f.name}{optional}: {ts_type};')
            lines.append('}')
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
                return f'{self._convert_type(inner)}[]'
            elif kind == 'optional':
                return f'{self._convert_type(inner)} | null'
            elif kind == 'dict':
                parts = [p.strip() for p in inner.split(',')]
                return f'Record<{self._convert_type(parts[0])}, {self._convert_type(parts[1])}>'

        return type_str